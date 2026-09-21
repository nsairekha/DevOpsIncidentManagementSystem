"""Wiring helpers: attach Prometheus monitoring to a FastAPI app."""

from fastapi import FastAPI
from prometheus_client import CollectorRegistry, generate_latest
from starlette.responses import Response

from backend.app.config import settings
from backend.app.monitoring.metrics import AppMetrics, create_app_metrics
from backend.app.monitoring.middleware import MetricsMiddleware


def setup_metrics(
    app: FastAPI, *, registry: CollectorRegistry | None = None
) -> AppMetrics:
    """Attach the metrics registry, HTTP middleware, and /metrics endpoint.

    Args:
        app: The FastAPI application to instrument.
        registry: Optional custom registry (used by tests to stay isolated).

    Returns:
        The :class:`AppMetrics` bound to this application.
    """
    metrics = create_app_metrics(registry)
    app.add_middleware(MetricsMiddleware, metrics=metrics)
    app.state.metrics = metrics

    metrics.app_info.labels(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    ).set(1)

    @app.get("/metrics", include_in_schema=False)
    def metrics_endpoint() -> Response:
        """Expose Prometheus metrics in the text exposition format."""
        return Response(
            content=generate_latest(metrics.registry),
            media_type="text/plain; version=0.0.4",
        )

    return metrics