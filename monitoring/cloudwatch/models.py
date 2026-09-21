"""Normalized metric models and shared CloudWatch error types."""

from datetime import datetime

from pydantic import BaseModel, Field

#: Metrics the integration knows how to retrieve.
SUPPORTED_METRICS = (
    "CPUUtilization",
    "NetworkIn",
    "NetworkOut",
    "NetworkPacketsIn",
    "NetworkPacketsOut",
    "DiskReadBytes",
    "DiskWriteBytes",
    "DiskReadOps",
    "DiskWriteOps",
)

#: CloudWatch statistics accepted by the integration.
SUPPORTED_STATISTICS = ("Average", "Minimum", "Maximum", "Sum", "SampleCount")


class MetricRecord(BaseModel):
    """Common internal representation for one observed metric value.

    Both Prometheus-derived and CloudWatch-derived data can be expressed
    through this record so a later baseline/anomaly layer processes one
    shape. ``source`` is ``"cloudwatch"`` for real AWS data and
    ``"cloudwatch_demo"`` for the clearly-marked demo mechanism — demo
    records are never presented as real CloudWatch data.
    """

    timestamp: datetime
    source: str = Field(pattern="^(cloudwatch|cloudwatch_demo|prometheus)$")
    service_name: str | None = None
    metric_name: str
    value: float
    unit: str | None = None
    resource_id: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)


class CloudWatchError(Exception):
    """Base class for CloudWatch integration errors (structured, never silent)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class CloudWatchDisabledError(CloudWatchError):
    """Collection is disabled (``AWS_ENABLED=false``)."""

    def __init__(self, message: str = "CloudWatch integration is disabled") -> None:
        super().__init__("cloudwatch_disabled", message)


class CloudWatchConfigError(CloudWatchError):
    """The request or configuration is invalid (unknown metric, no resource...)."""

    def __init__(self, message: str) -> None:
        super().__init__("cloudwatch_invalid_configuration", message)


class CloudWatchAWSError(CloudWatchError):
    """AWS itself failed (credentials, permissions, network, API errors)."""

    def __init__(self, message: str, aws_code: str | None = None) -> None:
        super().__init__("cloudwatch_aws_error", message)
        self.aws_code = aws_code