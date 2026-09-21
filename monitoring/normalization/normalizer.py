"""Normalization interface: canonical names, dispatch, deduplication.

Canonical names unify equivalent concepts across sources (e.g. CloudWatch
``CPUUtilization`` and a future container metric both become
``cpu_utilization``). Names without a documented mapping pass through
unchanged; the registry (``monitoring/pipeline/registry.py``) records which
canonical names currently have a live source so nothing is claimed present
that is not provided.
"""

from monitoring.models.metric import MetricRecord

#: Raw-name → canonical-name mapping for sources available today.
CANONICAL_NAMES: dict[str, str] = {
    # CloudWatch infrastructure concepts.
    "CPUUtilization": "cpu_utilization",
    "NetworkIn": "network_in",
    "NetworkOut": "network_out",
    "NetworkPacketsIn": "network_packets_in",
    "NetworkPacketsOut": "network_packets_out",
    "DiskReadBytes": "disk_read_bytes",
    "DiskWriteBytes": "disk_write_bytes",
    # Prometheus application concepts.
    "http_requests_total": "request_count",
    "http_request_duration_seconds": "latency",
    "http_request_errors_total": "http_5xx",
}


def canonical_name(raw_name: str) -> str:
    """Map a raw source metric name to its canonical name (pass-through if unknown)."""
    return CANONICAL_NAMES.get(raw_name, raw_name)


def normalize(record: MetricRecord) -> MetricRecord:
    """Return a copy of ``record`` with its canonical metric name applied."""
    if record.metric_name in CANONICAL_NAMES:
        return record.model_copy(
            update={"metric_name": CANONICAL_NAMES[record.metric_name]}
        )
    return record


def normalize_all(records: list[MetricRecord]) -> list[MetricRecord]:
    """Apply :func:`normalize` to every record, preserving order."""
    return [normalize(record) for record in records]


def deduplicate(records: list[MetricRecord]) -> list[MetricRecord]:
    """Drop exact duplicate observations, keeping the first of each group.

    Two records are duplicates when they share timestamp, source,
    service_name, metric_name, resource_id, labels, AND value — i.e. the
    full observation. Legitimate repeated measurements with different values
    (or different timestamps) are always kept.
    """
    seen: set[tuple] = set()
    unique: list[MetricRecord] = []
    for record in records:
        key = (
            record.timestamp,
            record.source,
            record.service_name,
            record.metric_name,
            record.resource_id,
            tuple(sorted(record.labels.items())),
            record.value,
        )
        if key not in seen:
            seen.add(key)
            unique.append(record)
    return unique