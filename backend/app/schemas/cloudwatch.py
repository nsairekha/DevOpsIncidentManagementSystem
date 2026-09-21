"""Response schemas for the CloudWatch endpoints."""

from pydantic import BaseModel

from monitoring.cloudwatch.models import MetricRecord


class CloudWatchStatusResponse(BaseModel):
    """Status of the CloudWatch integration (never includes credentials)."""

    enabled: bool
    available: bool
    region: str | None = None
    namespace: str | None = None
    message: str


class CloudWatchMetricsResponse(BaseModel):
    """Normalized metric records served by the metrics endpoint."""

    count: int
    records: list[MetricRecord]