"""Data types produced by AI agents."""

from dataclasses import dataclass
from datetime import datetime

SEVERITIES = ("low", "medium", "high")


@dataclass(frozen=True)
class Finding:
    """A single anomaly finding emitted by an incident-analysis agent.

    Attributes:
        signal: The telemetry signal (column) implicated in the anomaly.
        value: The observed value at the anomaly point.
        expected_range: ``(lower, upper)`` normal bounds from the baseline,
            or ``(None, None)`` when no baseline is available.
        score: Standardized deviation of the observed value.
        severity: One of ``low``, ``medium``, ``high``.
        timestamp: When the anomalous sample was observed, if known.
        details: Human-readable explanation of the finding.
    """

    signal: str
    value: float
    expected_range: tuple[float | None, float | None]
    score: float
    severity: str
    timestamp: datetime | None
    details: str


@dataclass(frozen=True)
class AgentResult:
    """Structured output of a single agent run."""

    findings: tuple[Finding, ...]
    n_findings: int
    summary: str

    def as_dict(self) -> dict:
        """Return the result as a plain, serialisable dictionary."""
        return {
            "n_findings": self.n_findings,
            "summary": self.summary,
            "findings": [
                {
                    "signal": f.signal,
                    "value": f.value,
                    "expected_range": list(f.expected_range),
                    "score": f.score,
                    "severity": f.severity,
                    "timestamp": f.timestamp.isoformat() if f.timestamp else None,
                    "details": f.details,
                }
                for f in self.findings
            ],
        }