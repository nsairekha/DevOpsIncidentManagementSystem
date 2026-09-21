"""ASGI middleware recording Prometheus HTTP metrics.

Every request increments counters, observes latency, and tracks in-flight
requests. The ``endpoint`` label uses the normalized FastAPI route template
(e.g. ``/api/v1/users/{user_id}``) so concrete IDs never become metric
labels; requests matching no route are labelled ``unmatched``. ``/metrics``
itself is excluded so scrapes don't feed back into the counters.
"""

import time

from services.common.metrics import ServiceMetrics

METRICS_PATH = "/metrics"
UNMATCHED_ENDPOINT = "unmatched"


class MetricsMiddleware:
    """Record HTTP metrics around the inner application."""

    def __init__(self, app, metrics: ServiceMetrics) -> None:
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope: dict, receive, send) -> None:
        # Non-HTTP scopes (lifespan, websockets) are not instrumented.
        if scope["type"] != "http":  # pragma: no cover - exercised by other clients
            await self.app(scope, receive, send)
            return

        if scope.get("path", "") == METRICS_PATH:
            await self.app(scope, receive, send)
            return

        service = self.metrics.service_name
        method = scope.get("method", "")
        status_holder = {"code": 500}
        start = time.perf_counter()

        self.metrics.http_requests_in_progress.labels(
            service=service, method=method
        ).inc()

        async def wrapped_send(message: dict) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            self.metrics.http_requests_in_progress.labels(
                service=service, method=method
            ).dec()
            duration = time.perf_counter() - start
            # The router sets scope["route"] during the inner call, so the
            # route template is only available *after* handling.
            route = scope.get("route")
            if route is not None and getattr(route, "path", None):
                endpoint = route.path
            else:
                endpoint = UNMATCHED_ENDPOINT
            status = str(status_holder["code"])
            self.metrics.http_request_duration_seconds.labels(
                service=service, method=method, endpoint=endpoint
            ).observe(duration)
            self.metrics.http_requests_total.labels(
                service=service, method=method, endpoint=endpoint, status_code=status
            ).inc()
            if status_holder["code"] >= 400:
                self.metrics.http_request_errors_total.labels(
                    service=service, method=method, endpoint=endpoint, status_code=status
                ).inc()