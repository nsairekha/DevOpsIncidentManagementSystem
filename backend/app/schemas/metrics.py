"""Response schemas for the metric pipeline endpoints."""

from pydantic import BaseModel

from monitoring.baseline.models import BaselineRecord
from monitoring.models.metric import MetricRecord


class MetricsListResponse(BaseModel):
    """Metric records served by the metrics endpoint."""

    count: int
    records: list[MetricRecord]
    message: str | None = None


class BaselinesListResponse(BaseModel):
    """Baseline records served by the baselines endpoint."""

    count: int
    baselines: list[BaselineRecord]
    message: str | None = None


class SourceSummary(BaseModel):
    """Availability snapshot for one observability source."""

    available: bool
    metric_count: int


class MetricsSummaryResponse(BaseModel):
    """Current snapshot across sources and known services."""

    timestamp: str
    sources: dict[str, SourceSummary]
    services: list[str]