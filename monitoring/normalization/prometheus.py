"""Normalization of Prometheus observations into MetricRecords.

Converts Prometheus HTTP API results (instant vectors and range matrices)
into :class:`MetricRecord` objects with ``source="prometheus"``. The
``service`` label (or ``job`` fallback) becomes ``service_name``; every
other label is preserved verbatim in ``labels``.
"""

from datetime import datetime, timezone
from typing import Any

from monitoring.models.metric import MetricRecord
from monitoring.normalization.normalizer import canonical_name


def _to_datetime(value: float | int) -> datetime:
    """Convert a Prometheus unix timestamp to tz-aware UTC datetime."""
    return datetime.fromtimestamp(float(value), tz=timezone.utc)


def from_instant_vector(
    results: list[dict[str, Any]],
    metric_name: str,
    unit: str | None = None,
) -> list[MetricRecord]:
    """Convert an instant-query ``result`` list into records.

    Each result is ``{"metric": {...labels}, "value": [ts, "str-value"]}``.
    """
    records = []
    for result in results:
        labels = dict(result.get("metric", {}))
        labels.pop("__name__", None)  # internal series name, not a dimension
        timestamp, raw_value = result.get("value", (None, None))
        if timestamp is None or raw_value is None:
            continue
        service = labels.pop("service", None) or labels.pop("job", None)
        records.append(
            MetricRecord(
                timestamp=_to_datetime(timestamp),
                source="prometheus",
                service_name=service,
                metric_name=canonical_name(metric_name),
                value=float(raw_value),
                unit=unit,
                resource_id=None,
                labels={k: str(v) for k, v in labels.items()},
                metadata={"query_type": "instant"},
            )
        )
    return records


def from_matrix(
    results: list[dict[str, Any]],
    metric_name: str,
    unit: str | None = None,
) -> list[MetricRecord]:
    """Convert a range-query ``result`` list into records.

    Each result is ``{"metric": {...labels}, "values": [[ts, "v"], ...]}``.
    """
    records = []
    for result in results:
        labels = dict(result.get("metric", {}))
        labels.pop("__name__", None)  # internal series name, not a dimension
        service = labels.pop("service", None) or labels.pop("job", None)
        remaining = {k: str(v) for k, v in labels.items()}
        for timestamp, raw_value in result.get("values", []):
            records.append(
                MetricRecord(
                    timestamp=_to_datetime(timestamp),
                    source="prometheus",
                    service_name=service,
                    metric_name=canonical_name(metric_name),
                    value=float(raw_value),
                    unit=unit,
                    resource_id=None,
                    labels=dict(remaining),
                    metadata={"query_type": "range"},
                )
            )
    return records