"""Metric registry: metadata describing known metrics.

A :class:`MetricDefinition` records what a metric means, its unit, and which
direction is worse. The registry is metadata for the future AI/ML pipeline —
it is never used to classify observations (no anomaly decisions here).
Canonical names without a live source are still registered so they can be
added later; ``has_source`` tells whether data actually flows today.
"""

from pydantic import BaseModel


class MetricDefinition(BaseModel):
    """Metadata for one canonical metric."""

    name: str
    description: str
    unit: str
    source: str
    metric_type: str
    aggregation: str
    higher_is_worse: bool = False
    lower_is_worse: bool = False
    has_source: bool = True


def _define(
    name: str,
    description: str,
    unit: str,
    source: str,
    metric_type: str,
    aggregation: str,
    higher_is_worse: bool = False,
    lower_is_worse: bool = False,
    has_source: bool = True,
) -> MetricDefinition:
    return MetricDefinition(
        name=name,
        description=description,
        unit=unit,
        source=source,
        metric_type=metric_type,
        aggregation=aggregation,
        higher_is_worse=higher_is_worse,
        lower_is_worse=lower_is_worse,
        has_source=has_source,
    )


REGISTRY: dict[str, MetricDefinition] = {
    # --- Resources (CloudWatch provides these today) ---
    "cpu_utilization": _define(
        "cpu_utilization", "CPU utilization", "percent", "cloudwatch",
        "resource", "average", higher_is_worse=True,
    ),
    "memory_utilization": _define(
        "memory_utilization", "Memory utilization", "percent", "cloudwatch",
        "resource", "average", higher_is_worse=True, has_source=False,
    ),
    "disk_utilization": _define(
        "disk_utilization", "Disk space utilization", "percent", "cloudwatch",
        "resource", "average", higher_is_worse=True, has_source=False,
    ),
    "disk_read_bytes": _define(
        "disk_read_bytes", "Disk bytes read", "bytes", "cloudwatch",
        "resource", "sum",
    ),
    "disk_write_bytes": _define(
        "disk_write_bytes", "Disk bytes written", "bytes", "cloudwatch",
        "resource", "sum",
    ),
    # --- Network (CloudWatch provides these today) ---
    "network_in": _define(
        "network_in", "Inbound network traffic", "bytes", "cloudwatch",
        "network", "sum",
    ),
    "network_out": _define(
        "network_out", "Outbound network traffic", "bytes", "cloudwatch",
        "network", "sum",
    ),
    "network_packets_in": _define(
        "network_packets_in", "Inbound network packets", "count", "cloudwatch",
        "network", "sum",
    ),
    "network_packets_out": _define(
        "network_packets_out", "Outbound network packets", "count", "cloudwatch",
        "network", "sum",
    ),
    "network_errors": _define(
        "network_errors", "Network error count", "count", "prometheus",
        "network", "sum", higher_is_worse=True, has_source=False,
    ),
    # --- Requests (Prometheus provides these today) ---
    "request_count": _define(
        "request_count", "Total HTTP requests served", "count", "prometheus",
        "requests", "sum",
    ),
    "request_rate": _define(
        "request_rate", "HTTP requests per second (PromQL rate over counters)",
        "count/second", "prometheus", "requests", "rate",
    ),
    "throughput": _define(
        "throughput", "Served request throughput", "count/second", "prometheus",
        "requests", "rate",
    ),
    # --- Latency (Prometheus histograms provide these today) ---
    "latency": _define(
        "latency", "Raw request latency observations", "seconds", "prometheus",
        "latency", "histogram",
    ),
    "latency_avg": _define(
        "latency_avg", "Mean request latency", "seconds", "prometheus",
        "latency", "average", higher_is_worse=True,
    ),
    "latency_p50": _define(
        "latency_p50", "Median (50th percentile) request latency", "seconds",
        "prometheus", "latency", "p50", higher_is_worse=True,
    ),
    "latency_p95": _define(
        "latency_p95", "95th percentile request latency", "seconds",
        "prometheus", "latency", "p95", higher_is_worse=True,
    ),
    "latency_p99": _define(
        "latency_p99", "99th percentile request latency", "seconds",
        "prometheus", "latency", "p99", higher_is_worse=True,
    ),
    # --- Errors (Prometheus provides these today) ---
    "http_4xx": _define(
        "http_4xx", "HTTP client-error responses", "count", "prometheus",
        "errors", "sum", higher_is_worse=True,
    ),
    "http_5xx": _define(
        "http_5xx", "HTTP server-error responses", "count", "prometheus",
        "errors", "sum", higher_is_worse=True,
    ),
    "error_rate": _define(
        "error_rate", "Error share of traffic (PromQL ratio over counters)",
        "ratio", "prometheus", "errors", "ratio", higher_is_worse=True,
    ),
    # --- Availability ---
    "availability": _define(
        "availability", "Service health signal", "boolean", "prometheus",
        "availability", "gauge", lower_is_worse=True,
    ),
    # --- Containers / reliability (registered for later; no source yet) ---
    "restart_count": _define(
        "restart_count", "Container restart count", "count", "prometheus",
        "containers", "sum", higher_is_worse=True, has_source=False,
    ),
    "timeout_count": _define(
        "timeout_count", "Dependency timeout count", "count", "prometheus",
        "reliability", "sum", higher_is_worse=True, has_source=False,
    ),
    "retry_count": _define(
        "retry_count", "Dependency retry count", "count", "prometheus",
        "reliability", "sum", higher_is_worse=True, has_source=False,
    ),
    # --- Dependencies (Prometheus provides these today) ---
    "dependency_request_count": _define(
        "dependency_request_count", "Downstream dependency calls", "count",
        "prometheus", "dependencies", "sum",
    ),
    "dependency_latency": _define(
        "dependency_latency", "Downstream dependency latency", "seconds",
        "prometheus", "dependencies", "histogram", higher_is_worse=True,
    ),
    "dependency_error_rate": _define(
        "dependency_error_rate", "Downstream dependency error share", "ratio",
        "prometheus", "dependencies", "ratio", higher_is_worse=True,
    ),
    # --- Cloud/AWS canonical aliases (CloudWatch provides these today) ---
    "cloudwatch_cpu_utilization": _define(
        "cloudwatch_cpu_utilization", "EC2 CPU utilization (CloudWatch alias)",
        "percent", "cloudwatch", "resource", "average", higher_is_worse=True,
    ),
    "cloudwatch_network_in": _define(
        "cloudwatch_network_in", "Inbound traffic (CloudWatch alias)", "bytes",
        "cloudwatch", "network", "sum",
    ),
    "cloudwatch_network_out": _define(
        "cloudwatch_network_out", "Outbound traffic (CloudWatch alias)", "bytes",
        "cloudwatch", "network", "sum",
    ),
}


def get_definition(name: str) -> MetricDefinition | None:
    """Return the registry entry for a canonical name, if registered."""
    return REGISTRY.get(name)


def registered_names() -> list[str]:
    """Return all registered canonical names, sorted."""
    return sorted(REGISTRY)


def sourced_names() -> list[str]:
    """Return registered names that currently have a live source."""
    return sorted(name for name, definition in REGISTRY.items() if definition.has_source)