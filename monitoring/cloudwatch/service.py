"""CloudWatch orchestration: status, retrieval, normalization, demo mode."""

from typing import Any

from monitoring.cloudwatch import client as client_module
from monitoring.cloudwatch import metrics as metrics_module
from monitoring.cloudwatch.config import CloudWatchConfig
from monitoring.cloudwatch.models import (
    SUPPORTED_METRICS,
    SUPPORTED_STATISTICS,
    CloudWatchAWSError,
    CloudWatchConfigError,
    CloudWatchDisabledError,
    MetricRecord,
)


class CloudWatchService:
    """Coordinate CloudWatch collection and normalization."""

    def __init__(self, config: CloudWatchConfig) -> None:
        self.config = config

    # ------------------------------------------------------------------ #
    # Status
    # ------------------------------------------------------------------ #
    def status(self) -> dict:
        """Report whether collection is enabled and configured."""
        if not self.config.aws_enabled:
            return {
                "enabled": False,
                "available": False,
                "message": "CloudWatch integration is disabled (AWS_ENABLED=false)",
            }
        try:
            client_module.build_client(self.config)
        except CloudWatchDisabledError as exc:  # pragma: no cover - guarded above
            return {"enabled": False, "available": False, "message": exc.message}
        except Exception as exc:
            return {
                "enabled": True,
                "available": False,
                "region": self.config.aws_region,
                "namespace": self.config.cloudwatch_namespace,
                "message": f"CloudWatch client could not be created: {exc}",
            }
        return {
            "enabled": True,
            "available": True,
            "region": self.config.aws_region,
            "namespace": self.config.cloudwatch_namespace,
            "message": "CloudWatch integration is enabled",
        }

    # ------------------------------------------------------------------ #
    # Retrieval + normalization
    # ------------------------------------------------------------------ #
    def get_metrics(
        self,
        *,
        metric_name: str | None = None,
        resource_id: str | None = None,
        lookback_minutes: int | None = None,
        statistic: str = "Average",
        demo: bool = False,
    ) -> list[MetricRecord]:
        """Fetch and normalize one metric over the lookback window.

        Args:
            metric_name: Defaults to ``CPUUtilization``.
            resource_id: Overrides the configured dimension value.
            lookback_minutes: Overrides the configured lookback.
            statistic: One of Average/Minimum/Maximum/Sum/SampleCount.
            demo: Return clearly-marked demo records instead of AWS data.

        Raises:
            CloudWatchDisabledError: When disabled (and not demo mode).
            CloudWatchConfigError: On unknown metrics/statistics, bad
                lookback, or no configured resource.
            CloudWatchAWSError: On any AWS-side failure.
        """
        name = metric_name or "CPUUtilization"
        if demo:
            return self.demo_records(
                metric_name=name,
                resource_id=resource_id,
                lookback_minutes=lookback_minutes
                or self.config.cloudwatch_lookback_minutes,
            )
        if not self.config.aws_enabled:
            raise CloudWatchDisabledError(
                "CloudWatch integration is disabled (AWS_ENABLED=false); "
                "pass demo=true for clearly-marked demo records"
            )
        if name not in SUPPORTED_METRICS:
            raise CloudWatchConfigError(
                f"unsupported metric '{name}'; supported: {', '.join(SUPPORTED_METRICS)}"
            )
        if statistic not in SUPPORTED_STATISTICS:
            raise CloudWatchConfigError(
                f"unsupported statistic '{statistic}'; "
                f"supported: {', '.join(SUPPORTED_STATISTICS)}"
            )

        resolved_resource = resource_id or self.config.cloudwatch_dimension_value
        if not resolved_resource:
            raise CloudWatchConfigError(
                "no resource configured; set CLOUDWATCH_DIMENSION_VALUE "
                "or pass resource_id"
            )
        lookback = lookback_minutes or self.config.cloudwatch_lookback_minutes

        start, end = metrics_module.lookback_window(lookback)
        dimensions = {
            self.config.cloudwatch_dimension_name: resolved_resource
        }
        boto_client = client_module.build_client(self.config)
        datapoints = metrics_module.fetch_datapoints(
            boto_client,
            namespace=self.config.cloudwatch_namespace,
            metric_name=name,
            dimensions=dimensions,
            start_time=start,
            end_time=end,
            period=self.config.cloudwatch_period,
            statistics=[statistic],
        )
        return [
            self.normalize_datapoint(
                point,
                namespace=self.config.cloudwatch_namespace,
                metric_name=name,
                resource_id=resolved_resource,
                statistic=statistic,
            )
            for point in datapoints
            if statistic in point
        ]

    @staticmethod
    def normalize_datapoint(
        point: dict[str, Any],
        *,
        namespace: str,
        metric_name: str,
        resource_id: str,
        statistic: str,
    ) -> MetricRecord:
        """Convert one raw CloudWatch datapoint into a MetricRecord."""
        dimensions = {
            item["Name"]: item["Value"]
            for item in point.get("Dimensions", [])
        }
        return MetricRecord(
            timestamp=point["Timestamp"],
            source="cloudwatch",
            service_name=None,
            metric_name=metric_name,
            value=float(point[statistic]),
            unit=point.get("Unit"),
            resource_id=resource_id,
            labels=dimensions,
            metadata={
                "namespace": namespace,
                "statistic": statistic,
            },
        )

    def demo_records(
        self,
        *,
        metric_name: str,
        resource_id: str | None,
        lookback_minutes: int,
    ) -> list[MetricRecord]:
        """Return deterministic demo records, always marked ``cloudwatch_demo``.

        Strictly separated from the production path: demo records are never
        presented as real CloudWatch data.
        """
        start, end = metrics_module.lookback_window(lookback_minutes)
        resolved = resource_id or self.config.cloudwatch_dimension_value or "demo-resource"
        records = []
        for index in range(5):
            fraction = index / 4.0
            timestamp = start + (end - start) * fraction
            records.append(
                MetricRecord(
                    timestamp=timestamp,
                    source="cloudwatch_demo",
                    service_name=None,
                    metric_name=metric_name,
                    value=round(40.0 + 10.0 * fraction, 3),
                    unit="Percent",
                    resource_id=resolved,
                    labels={self.config.cloudwatch_dimension_name: resolved},
                    metadata={"namespace": self.config.cloudwatch_namespace,
                              "statistic": "Average", "mode": "demo"},
                )
            )
        return records