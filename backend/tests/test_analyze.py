"""Tests for the /api/analyze endpoint and its helpers."""

from datetime import datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from agents import Finding
from ai import IQRDetector, IsolationForestDetector, ZScoreDetector
from backend.app.api.routes.analyze import build_detector, to_finding_out, worst_severity
from backend.app.schemas.analyze import FindingOut

REFERENCE = {"cpu": [10.0, 10.5, 9.8, 10.2, 10.1] * 4}
TELEMETRY_NORMAL = {"cpu": [10.2, 9.9, 10.0, 10.1, 9.8]}
TELEMETRY_ANOMALOUS = {"cpu": [10.2, 9.9, 99.0, 10.1, 9.8]}


def _analyze(client: TestClient, telemetry: dict, **overrides) -> TestClient:
    payload = {"reference": REFERENCE, "telemetry": telemetry, **overrides}
    return client.post("/api/analyze", json=payload)


def test_analyze_normal_telemetry_reports_no_findings(client: TestClient) -> None:
    """A clean window yields no findings and is still audited."""
    response = _analyze(client, TELEMETRY_NORMAL)

    assert response.status_code == 200
    body = response.json()
    assert body["detector"] == "zscore"
    assert body["n_findings"] == 0
    assert body["severity"] == "none"
    assert body["findings"] == []
    assert body["audited"] is True
    assert len(body["block_hash"]) == 64
    assert body["event_id"]
    assert body["chain_valid"] is True


def test_analyze_detects_anomalies_and_audits(client: TestClient) -> None:
    """An anomalous window is flagged, summarised, and appended to the ledger."""
    response = _analyze(client, TELEMETRY_ANOMALOUS)

    assert response.status_code == 200
    body = response.json()
    assert body["n_findings"] >= 1
    assert body["severity"] in {"low", "medium", "high"}
    assert body["summary"]

    finding = body["findings"][0]
    assert finding["signal"] == "cpu"
    assert finding["value"] > 10.0
    assert finding["timestamp"] is None  # integer row index -> no timestamp
    assert finding["details"]

    # The run was recorded: a follow-up audit must include an agent_result block.
    audit = client.get("/api/audit").json()
    assert audit["length"] == 2
    assert audit["blocks"][1]["event_type"] == "agent_result"
    assert audit["valid"] is True


def test_analyze_all_detector_families(client: TestClient) -> None:
    """Every detector family is accepted by the endpoint."""
    for detector in ("zscore", "iqr", "isolation_forest"):
        response = _analyze(client, TELEMETRY_NORMAL, detector=detector)
        assert response.status_code == 200
        assert response.json()["detector"] == detector
        assert response.json()["severity"] == "none"


def test_analyze_empty_telemetry_is_rejected(client: TestClient) -> None:
    """Telemetry must contain at least one signal."""
    response = _analyze(client, {})
    assert response.status_code == 422


def test_analyze_rejects_unknown_detector_literal(client: TestClient) -> None:
    """Unsupported detector names fail request validation."""
    response = _analyze(client, TELEMETRY_NORMAL, detector="knn")
    assert response.status_code == 422


def test_analyze_requires_signals(client: TestClient) -> None:
    """Empty reference and empty value lists are rejected with 422."""
    empty_ref = client.post(
        "/api/analyze", json={"reference": {}, "telemetry": TELEMETRY_NORMAL}
    )
    assert empty_ref.status_code == 422

    empty_signal = client.post(
        "/api/analyze",
        json={"reference": {"cpu": []}, "telemetry": TELEMETRY_NORMAL},
    )
    assert empty_signal.status_code == 422


def test_analyze_rejects_non_positive_threshold(client: TestClient) -> None:
    """A zero threshold fails validation."""
    response = _analyze(client, TELEMETRY_NORMAL, threshold=0.0)
    assert response.status_code == 422


def test_build_detector_families() -> None:
    """build_detector returns the right detector for each family."""
    assert isinstance(build_detector("zscore", 3.0), ZScoreDetector)
    assert isinstance(build_detector("iqr", 3.0), IQRDetector)
    assert isinstance(build_detector("isolation_forest", 3.0), IsolationForestDetector)


def test_build_detector_unknown_raises_400() -> None:
    """Unknown detector names produce an HTTP 400 from the helper."""
    with pytest.raises(HTTPException) as exc:
        build_detector("knn", 3.0)
    assert exc.value.status_code == 400
    assert "unknown detector" in exc.value.detail


def test_worst_severity_aggregation() -> None:
    """worst_severity picks the highest severity present (or 'none')."""
    finding = FindingOut(
        signal="cpu", value=12.0, score=4.0, severity="low", details="d"
    )
    assert worst_severity([]) == "none"
    assert worst_severity([finding]) == "low"
    assert (
        worst_severity(
            [
                finding,
                FindingOut(signal="mem", value=2.0, score=6.0, severity="high", details="d"),
            ]
        )
        == "high"
    )


def test_to_finding_out_preserves_timestamp() -> None:
    """findings with a datetime timestamp are ISO-formatted on output."""
    stamp = datetime(2026, 9, 20, 12, 30, 0)
    finding = Finding(
        signal="cpu",
        value=99.0,
        expected_range=(8.0, 12.0),
        score=50.0,
        severity="high",
        timestamp=stamp,
        details="spike",
    )

    out = to_finding_out(finding)

    assert out.timestamp == "2026-09-20T12:30:00"
    assert out.expected_range == (8.0, 12.0)
    assert out.details == "spike"