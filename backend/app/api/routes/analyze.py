"""Anomaly analysis and incident findings endpoint.

Runs the AI incident-analysis pipeline (baselines + detector + agent) over
an HTTP request, emits a service event, and records the outcome in the
append-only audit ledger.
"""

from fastapi import APIRouter, Depends, HTTPException, Request

import pandas as pd

from ai import IQRDetector, IsolationForestDetector, ZScoreDetector
from agents import IncidentAnalysisAgent
from blockchain import AuditLedger, Block
from backend.app.deps import get_ledger
from backend.app.schemas.analyze import (
    SEVERITY_ORDER,
    AnalysisRequest,
    AnalysisResponse,
    FindingOut,
)
from dataset.baseline import compute_baselines
from services import EventEnvelope, EventTypes

router = APIRouter(prefix="/api", tags=["analysis"])


def build_detector(name: str, threshold: float):
    """Instantiate the detector family selected in the request."""
    if name == "zscore":
        return ZScoreDetector(threshold=threshold)
    if name == "iqr":
        return IQRDetector()
    if name == "isolation_forest":
        return IsolationForestDetector()
    raise HTTPException(status_code=400, detail=f"unknown detector '{name}'")


def worst_severity(findings: list[FindingOut]) -> str:
    """Aggregate finding severities into the worst one (or 'none')."""
    if not findings:
        return "none"
    return max((f.severity for f in findings), key=SEVERITY_ORDER.__getitem__)


def to_finding_out(finding) -> FindingOut:
    """Convert an agent :class:`Finding` into the API response model."""
    return FindingOut(
        signal=finding.signal,
        value=finding.value,
        expected_range=finding.expected_range,
        score=finding.score,
        severity=finding.severity,
        timestamp=finding.timestamp.isoformat() if finding.timestamp else None,
        details=finding.details,
    )


@router.post("/analyze", response_model=AnalysisResponse, summary="Analyse telemetry for anomalies")
def analyze(
    payload: AnalysisRequest,
    request: Request,
    ledger: AuditLedger = Depends(get_ledger),
) -> AnalysisResponse:
    """Run the incident-analysis agent and audit the outcome.

    The request's reference window is used to fit a detector and compute
    per-signal baselines; the telemetry window is then analysed for anomalies.
    Every run is emitted as an event and appended to the audit ledger, whose
    block hash is returned so callers can trace the result.
    """
    reference = pd.DataFrame(payload.reference)
    telemetry = pd.DataFrame(payload.telemetry)

    detector = build_detector(payload.detector, payload.threshold).fit(reference)
    agent = IncidentAnalysisAgent(detector, compute_baselines(reference))
    result = agent.analyze(telemetry)

    envelope = EventEnvelope.create(
        EventTypes.ANOMALY_DETECTED,
        "backend.app.api.analyze",
        {"detector": payload.detector, "analysis": result.as_dict()},
    )
    block: Block = ledger.append("agent_result", envelope.as_dict())

    findings = [to_finding_out(f) for f in result.findings]

    return AnalysisResponse(
        detector=payload.detector,
        n_findings=result.n_findings,
        severity=worst_severity(findings),
        summary=result.summary,
        findings=findings,
        audited=True,
        block_hash=block.hash,
        event_id=envelope.event_id,
        chain_valid=ledger.verify().valid,
    )