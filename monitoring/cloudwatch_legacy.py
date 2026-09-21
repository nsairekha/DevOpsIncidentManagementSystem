"""AWS CloudWatch metrics client.

Fetches metric statistics from AWS CloudWatch via boto3 and normalises them
into the project's internal telemetry representation so that downstream
modules (dataset baselines, anomaly detectors) can consume them unchanged.
"""

from dataclasses import dataclass, field
from datetime import datetime

import boto3
import pandas as pd

from backend.app.config import Settings

ALLOWED_STATISTICS = frozenset({"Average", "Sum", "Minimum", "Maximum", "SampleCount"})


@dataclass(frozen=True)
class CloudWatchMetric:
    """A single normalised telemetry sample retrieved from CloudWatch."""

    namespace: str
    metric_name: str
    timestamp: datetime
    value: float
    unit: str
    dimensions: tuple[tuple[str, str], ...] = field(default_factory=tuple)


class CloudWatchClient:
    """Thin wrapper around the CloudWatch ``get_metric_statistics`` API."""

    def __init__(
        self,
        *,
        region_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ) -> None:
        self.session = boto3.Session(
            region_name=region_name or "us-east-1",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.client = self.session.client("cloudwatch")

    def get_metric_statistics(
        self,
        *,
        namespace: str,
        metric_name: str,
        dimensions: dict[str, str],
        start_time: datetime,
        end_time: datetime,
        period: int,
        statistic: str = "Average",
    ) -> list[CloudWatchMetric]:
        """Fetch and normalise one metric's statistics over a time window.

        Args:
            namespace: CloudWatch namespace (e.g. ``AWS/EC2``).
            metric_name: Metric name (e.g. ``CPUUtilization``).
            dimensions: Metric dimensions (e.g. ``{"InstanceId": "i-123"}``).
            start_time/end_time: Window bounds (inclusive start, exclusive end).
            period: Aggregation period in seconds.
            statistic: One of Average, Sum, Minimum, Maximum, SampleCount.

        Returns:
            Datapoints normalised to :class:`CloudWatchMetric`, sorted
            chronologically.
        """
        if statistic not in ALLOWED_STATISTICS:
            raise ValueError(f"unsupported statistic '{statistic}'")

        response = self.client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=[{"Name": k, "Value": v} for k, v in dimensions.items()],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=[statistic],
        )

        metrics = [
            CloudWatchMetric(
                namespace=namespace,
                metric_name=metric_name,
                timestamp=dp["Timestamp"],
                value=float(dp[statistic]),
                unit=str(dp.get("Unit", "")),
                dimensions=tuple(sorted(dimensions.items())),
            )
            for dp in response.get("Datapoints", [])
            if statistic in dp
        ]

        return sorted(metrics, key=lambda m: m.timestamp)


def cloudwatch_client_from_settings(settings: Settings) -> CloudWatchClient:
    """Build a CloudWatchClient from application settings."""
    return CloudWatchClient(
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def metrics_to_dataframe(metrics: list[CloudWatchMetric]) -> pd.DataFrame:
    """Convert normalised CloudWatch metrics into a tidy DataFrame.

    Columns: ``timestamp``, ``metric`` (``namespace/metric_name``), ``value``,
    ``unit``, plus one column per dimension key.
    """
    if not metrics:
        return pd.DataFrame(
            columns=["timestamp", "metric", "value", "unit"]
        )

    rows = []
    for m in metrics:
        row = {
            "timestamp": m.timestamp,
            "metric": f"{m.namespace}/{m.metric_name}",
            "value": m.value,
            "unit": m.unit,
        }
        row.update(dict(m.dimensions))
        rows.append(row)

    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)