"""ASGI middleware that records HTTP request metrics for Prometheus.

Requests are labelled by HTTP method and the matched route template (e.g.
``/health`` instead of a concrete path) to keep cardinality low. The
``/metrics`` endpoint itself is excluded from instrumentation so the scrape
does not feed back into the counters.
"""

import time

from backend.app.monitoring.metrics import AppMetrics

METRICS_PATH = "/metrics"


class MetricsMiddleware:
    """Increment counters, observe latency, and track in-flight requests."""

    def __init__(self, app, metrics: AppMetrics) -> None:
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope: dict, receive, send) -> None:
        # Non-HTTP scopes (lifespan, websockets) are not instrumented.
        if scope["type"] != "http":  # pragma: no cover - exercised by other clients
            await self.app(scope, receive, send)
            return

        request_path = scope.get("path", "")
        if request_path == METRICS_PATH:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        status_holder = {"code": 500}
        start = time.perf_counter()

        self.metrics.http_requests_in_progress.labels(method=method).inc()

        async def wrapped_send(message: dict) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            self.metrics.http_requests_in_progress.labels(method=method).dec()
            duration = time.perf_counter() - start
            # The router sets scope["route"] during the inner call, so the
            # route template is only available *after* the app has handled
            # the request. Prefer it over the raw path for low cardinality.
            route = scope.get("route")
            if route is not None and getattr(route, "path", None):
                path = route.path
            else:
                path = request_path
            self.metrics.http_request_duration_seconds.labels(
                method=method, path=path
            ).observe(duration)
            self.metrics.http_requests_total.labels(
                method=method, path=path, status=str(status_holder["code"])
            ).inc()