"""Metrics registry and collectors for the backend.

A single ``CollectorRegistry`` owns all app metrics. The registry (and the
metrics bound to it) can be created against an explicit registry for tests, or
against a module-level default singleton for the running application.
"""

from dataclasses import dataclass
from functools import lru_cache

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

DEFAULT_BUCKETS = (
    0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0,
)


@lru_cache
def get_default_registry() -> CollectorRegistry:
    """Return the process-wide default registry (singleton)."""
    return CollectorRegistry()


@dataclass(frozen=True)
class AppMetrics:
    """All metric objects used by the backend, bound to one registry."""

    registry: CollectorRegistry
    http_requests_total: Counter
    http_request_duration_seconds: Histogram
    http_requests_in_progress: Gauge
    app_info: Gauge


def create_app_metrics(registry: CollectorRegistry | None = None) -> AppMetrics:
    """Create metrics collectors, optionally on a custom registry."""
    registry = registry or get_default_registry()

    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests handled",
        ("method", "path", "status"),
        registry=registry,
    )
    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        ("method", "path"),
        buckets=DEFAULT_BUCKETS,
        registry=registry,
    )
    http_requests_in_progress = Gauge(
        "http_requests_in_progress",
        "HTTP requests currently being served",
        ("method",),
        registry=registry,
    )
    app_info = Gauge(
        "app_info",
        "Static metadata about the application (always 1)",
        ("app_name", "version", "environment"),
        registry=registry,
    )

    return AppMetrics(
        registry=registry,
        http_requests_total=http_requests_total,
        http_request_duration_seconds=http_request_duration_seconds,
        http_requests_in_progress=http_requests_in_progress,
        app_info=app_info,
    )