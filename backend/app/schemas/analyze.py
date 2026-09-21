"""Request/response schemas for the analysis endpoint."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

DetectorName = Literal["zscore", "iqr", "isolation_forest"]

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "none": -1}


class AnalysisRequest(BaseModel):
    """Input telemetry for an anomaly analysis run.

    Attributes:
        reference: Per-signal training window describing "normal" behaviour.
        telemetry: Per-signal live window to analyse.
        detector: Which detector family to use (defaults to z-score).
        threshold: Z-score threshold used by the z-score detector.
    """

    reference: dict[str, list[float]]
    telemetry: dict[str, list[float]]
    detector: DetectorName = "zscore"
    threshold: float = Field(default=3.0, gt=0)

    @field_validator("reference", "telemetry")
    @classmethod
    def _require_signals(cls, value: dict[str, list[float]]) -> dict[str, list[float]]:
        if not value:
            raise ValueError("at least one signal is required")
        for signal, samples in value.items():
            if len(samples) == 0:
                raise ValueError(f"signal '{signal}' must contain samples")
        return value


class FindingOut(BaseModel):
    """A single anomaly finding, as exposed by the API."""

    signal: str
    value: float
    expected_range: tuple[float | None, float | None] | None = None
    score: float
    severity: str
    timestamp: str | None = None
    details: str


class AnalysisResponse(BaseModel):
    """Result of an analysis run, including its audit reference."""

    detector: str
    n_findings: int
    severity: str
    summary: str
    findings: list[FindingOut]
    audited: bool
    block_hash: str
    event_id: str
    chain_valid: bool