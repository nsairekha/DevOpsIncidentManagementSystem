"""Reusable Prometheus metric definitions for the microservices.

Every service builds its collectors on its own :class:`CollectorRegistry`
(passed in by the application factory, so tests stay isolated). Metric names
are consistent across services:

Stored collectors (per service):

- ``http_requests_total{service,method,endpoint,status_code}`` (Counter)
- ``http_request_duration_seconds{service,method,endpoint}`` (Histogram)
- ``http_requests_in_progress{service,method}`` (Gauge)
- ``http_request_errors_total{service,method,endpoint,status_code}`` (Counter, 4xx/5xx only)
- ``service_up{service}`` (Gauge, 1 = healthy)
- ``process_cpu_seconds_total`` / ``process_resident_memory_bytes`` (standard
  process collector — real values on Linux)

Derived (NOT stored — Prometheus computes them from the counters above):

- request rate: ``rate(http_requests_total[5m])`` (also ``[1m]``)
- error rate: ``sum(rate(http_requests_total{status_code=~"5.."}[5m])) /
  sum(rate(http_requests_total[5m]))``
- P50/P95/P99: ``histogram_quantile(0.5|0.95|0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, ...))``

No high-cardinality labels (request_id, user_id, order_id, ...) are ever
attached to metrics; request IDs stay in the JSON logs.
"""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    ProcessCollector,
    generate_latest,
)

DEFAULT_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)


@dataclass(frozen=True)
class ServiceMetrics:
    """Common HTTP metrics for one service, bound to one registry."""

    service_name: str
    registry: CollectorRegistry
    http_requests_total: Counter
    http_request_duration_seconds: Histogram
    http_requests_in_progress: Gauge
    http_request_errors_total: Counter
    service_up: Gauge


@dataclass(frozen=True)
class DependencyMetrics:
    """Downstream dependency metrics (source → target over HTTP)."""

    requests_total: Counter
    request_duration_seconds: Histogram
    errors_total: Counter

    def _labels(self, source: str, target: str, endpoint: str) -> dict[str, str]:
        return {
            "source_service": source,
            "target_service": target,
            "endpoint": endpoint,
        }


@dataclass(frozen=True)
class UserMetrics:
    """Application metrics for the user-service."""

    user_requests_total: Counter
    user_lookup_errors_total: Counter


@dataclass(frozen=True)
class OrderMetrics:
    """Application metrics for the order-service."""

    orders_created_total: Counter
    orders_failed_total: Counter
    order_processing_duration_seconds: Histogram
    payment_dependency_requests_total: Counter
    payment_dependency_errors_total: Counter
    notification_dependency_requests_total: Counter
    notification_dependency_errors_total: Counter


@dataclass(frozen=True)
class PaymentMetrics:
    """Application metrics for the payment-service."""

    payments_total: Counter
    payments_success_total: Counter
    payments_failed_total: Counter
    payment_processing_duration_seconds: Histogram


@dataclass(frozen=True)
class NotificationMetrics:
    """Application metrics for the notification-service."""

    notifications_total: Counter
    notifications_success_total: Counter
    notifications_failed_total: Counter
    notification_processing_duration_seconds: Histogram


def create_service_metrics(
    service_name: str, registry: CollectorRegistry | None = None
) -> ServiceMetrics:
    """Create the common HTTP collectors for a service."""
    registry = registry or CollectorRegistry()
    # Real process metrics (CPU time, resident memory) on Linux.
    ProcessCollector(registry=registry)

    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests handled",
        ("service", "method", "endpoint", "status_code"),
        registry=registry,
    )
    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        ("service", "method", "endpoint"),
        buckets=DEFAULT_BUCKETS,
        registry=registry,
    )
    http_requests_in_progress = Gauge(
        "http_requests_in_progress",
        "HTTP requests currently being served",
        ("service", "method"),
        registry=registry,
    )
    http_request_errors_total = Counter(
        "http_request_errors_total",
        "Total HTTP requests answered with 4xx/5xx",
        ("service", "method", "endpoint", "status_code"),
        registry=registry,
    )
    service_up = Gauge(
        "service_up",
        "Service health (1 = healthy, 0 = unhealthy)",
        ("service",),
        registry=registry,
    )
    service_up.labels(service=service_name).set(1)

    return ServiceMetrics(
        service_name=service_name,
        registry=registry,
        http_requests_total=http_requests_total,
        http_request_duration_seconds=http_request_duration_seconds,
        http_requests_in_progress=http_requests_in_progress,
        http_request_errors_total=http_request_errors_total,
        service_up=service_up,
    )


def create_user_metrics(registry: CollectorRegistry) -> UserMetrics:
    """Create the user-service application collectors."""
    return UserMetrics(
        user_requests_total=Counter(
            "user_requests_total",
            "Total user lookup requests",
            registry=registry,
        ),
        user_lookup_errors_total=Counter(
            "user_lookup_errors_total",
            "Total user lookups for unknown IDs",
            registry=registry,
        ),
    )


def create_order_metrics(registry: CollectorRegistry) -> OrderMetrics:
    """Create the order-service application collectors."""
    return OrderMetrics(
        orders_created_total=Counter(
            "orders_created_total", "Total orders created", registry=registry
        ),
        orders_failed_total=Counter(
            "orders_failed_total",
            "Total orders that failed (usually payment failures)",
            registry=registry,
        ),
        order_processing_duration_seconds=Histogram(
            "order_processing_duration_seconds",
            "End-to-end order creation latency in seconds",
            buckets=DEFAULT_BUCKETS,
            registry=registry,
        ),
        payment_dependency_requests_total=Counter(
            "payment_dependency_requests_total",
            "Total calls from order-service to payment-service",
            registry=registry,
        ),
        payment_dependency_errors_total=Counter(
            "payment_dependency_errors_total",
            "Total failed calls from order-service to payment-service",
            registry=registry,
        ),
        notification_dependency_requests_total=Counter(
            "notification_dependency_requests_total",
            "Total calls from order-service to notification-service",
            registry=registry,
        ),
        notification_dependency_errors_total=Counter(
            "notification_dependency_errors_total",
            "Total failed calls from order-service to notification-service",
            registry=registry,
        ),
    )


def create_payment_metrics(registry: CollectorRegistry) -> PaymentMetrics:
    """Create the payment-service application collectors."""
    return PaymentMetrics(
        payments_total=Counter(
            "payments_total", "Total payment attempts", registry=registry
        ),
        payments_success_total=Counter(
            "payments_success_total",
            "Total successfully processed payments",
            registry=registry,
        ),
        payments_failed_total=Counter(
            "payments_failed_total",
            "Total failed payments (stays 0 while simulation never fails)",
            registry=registry,
        ),
        payment_processing_duration_seconds=Histogram(
            "payment_processing_duration_seconds",
            "Payment processing latency in seconds",
            buckets=DEFAULT_BUCKETS,
            registry=registry,
        ),
    )


def create_notification_metrics(registry: CollectorRegistry) -> NotificationMetrics:
    """Create the notification-service application collectors."""
    return NotificationMetrics(
        notifications_total=Counter(
            "notifications_total",
            "Total notification attempts",
            registry=registry,
        ),
        notifications_success_total=Counter(
            "notifications_success_total",
            "Total successfully sent notifications",
            registry=registry,
        ),
        notifications_failed_total=Counter(
            "notifications_failed_total",
            "Total failed notifications (stays 0 while simulation never fails)",
            registry=registry,
        ),
        notification_processing_duration_seconds=Histogram(
            "notification_processing_duration_seconds",
            "Notification processing latency in seconds",
            buckets=DEFAULT_BUCKETS,
            registry=registry,
        ),
    )


def create_dependency_metrics(registry: CollectorRegistry) -> DependencyMetrics:
    """Create the generic downstream dependency collectors (§6 design)."""
    return DependencyMetrics(
        requests_total=Counter(
            "dependency_requests_total",
            "Total downstream dependency requests",
            ("source_service", "target_service", "endpoint"),
            registry=registry,
        ),
        request_duration_seconds=Histogram(
            "dependency_request_duration_seconds",
            "Downstream dependency latency in seconds",
            ("source_service", "target_service", "endpoint"),
            buckets=DEFAULT_BUCKETS,
            registry=registry,
        ),
        errors_total=Counter(
            "dependency_errors_total",
            "Total failed downstream dependency requests",
            ("source_service", "target_service", "endpoint"),
            registry=registry,
        ),
    )


@contextmanager
def track_dependency(
    metrics: DependencyMetrics, source: str, target: str, endpoint: str
) -> Iterator[None]:
    """Record one downstream call: count, time, and count failures.

    Usage::

        with track_dependency(deps, "order-service", "payment-service",
                              "/api/v1/payments"):
            client.process_payment(...)
    """
    labels = metrics._labels(source, target, endpoint)  # noqa: SLF001 - shared helper
    started = time.perf_counter()
    metrics.requests_total.labels(**labels).inc()
    try:
        yield
    except Exception:
        metrics.errors_total.labels(**labels).inc()
        raise
    finally:
        metrics.request_duration_seconds.labels(**labels).observe(
            time.perf_counter() - started
        )


def render_metrics(registry: CollectorRegistry) -> bytes:
    """Render a registry in the Prometheus text exposition format."""
    return generate_latest(registry)


__all__ = [
    "CONTENT_TYPE_LATEST",
    "DEFAULT_BUCKETS",
    "DependencyMetrics",
    "NotificationMetrics",
    "OrderMetrics",
    "PaymentMetrics",
    "ServiceMetrics",
    "UserMetrics",
    "create_dependency_metrics",
    "create_notification_metrics",
    "create_order_metrics",
    "create_payment_metrics",
    "create_service_metrics",
    "create_user_metrics",
    "render_metrics",
    "track_dependency",
]