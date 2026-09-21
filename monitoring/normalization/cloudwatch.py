"""Normalization of CloudWatch observations into MetricRecords.

Adapts :class:`monitoring.cloudwatch.models.MetricRecord` (real
``source="cloudwatch"`` or demo ``source="cloudwatch_demo"``) and raw
CloudWatch datapoints into the canonical
:class:`monitoring.models.metric.MetricRecord`. Source information is
preserved exactly — demo data can never become ``source="cloudwatch"``.
"""

from typing import Any

from monitoring.cloudwatch.models import MetricRecord as CloudWatchRecord
from monitoring.models.metric import MetricRecord
from monitoring.normalization.normalizer import canonical_name


def from_cloudwatch_record(record: CloudWatchRecord) -> MetricRecord:
    """Convert one CloudWatch-module record into the canonical record."""
    return MetricRecord(
        timestamp=record.timestamp,
        source=record.source,
        service_name=record.service_name,
        metric_name=canonical_name(record.metric_name),
        value=record.value,
        unit=record.unit,
        resource_id=record.resource_id,
        labels=dict(record.labels),
        metadata=dict(record.metadata),
    )


def from_cloudwatch_records(records: list[CloudWatchRecord]) -> list[MetricRecord]:
    """Convert CloudWatch-module records, preserving order."""
    return [from_cloudwatch_record(record) for record in records]


def from_datapoint(
    point: dict[str, Any],
    *,
    namespace: str,
    metric_name: str,
    resource_id: str,
    statistic: str,
) -> MetricRecord:
    """Convert one raw CloudWatch datapoint into the canonical record."""
    return MetricRecord(
        timestamp=point["Timestamp"],
        source="cloudwatch",
        service_name=None,
        metric_name=canonical_name(metric_name),
        value=float(point[statistic]),
        unit=point.get("Unit"),
        resource_id=resource_id,
        labels={},
        metadata={"namespace": namespace, "statistic": statistic},
    )