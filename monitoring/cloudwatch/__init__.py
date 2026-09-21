"""AWS CloudWatch integration (STEP 6)."""

from monitoring.cloudwatch.client import build_client
from monitoring.cloudwatch.config import CloudWatchConfig
from monitoring.cloudwatch.models import (
    SUPPORTED_METRICS,
    SUPPORTED_STATISTICS,
    CloudWatchAWSError,
    CloudWatchConfigError,
    CloudWatchDisabledError,
    CloudWatchError,
    MetricRecord,
)
from monitoring.cloudwatch.service import CloudWatchService

__all__ = [
    "SUPPORTED_METRICS",
    "SUPPORTED_STATISTICS",
    "CloudWatchAWSError",
    "CloudWatchConfigError",
    "CloudWatchDisabledError",
    "CloudWatchError",
    "CloudWatchConfig",
    "CloudWatchService",
    "MetricRecord",
    "build_client",
]