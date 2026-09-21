"""Structured JSON request logging with distributed request-ID propagation.

Every HTTP request is timed and logged on completion as a single JSON line
containing ``timestamp``, ``service``, ``method``, ``endpoint``,
``status_code``, ``request_id`` and ``response_time_ms``.

Propagation rule: when the incoming request already carries an ``X-Request-ID``
header (i.e. it arrived from another service in the same distributed trace),
that ID is reused; otherwise a fresh one is generated. The effective ID is
returned in the ``X-Request-ID`` response header and is available to route
handlers via :func:`get_request_id` so downstream HTTP calls can forward it.
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

REQUEST_ID_HEADER = "X-Request-ID"

RequestLogger = logging.getLogger("request")

# Request ID of the in-flight request (set by the middleware per request).
_current_request_id: ContextVar[str | None] = ContextVar(
    "service_request_id", default=None
)


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", None),
            "message": record.getMessage(),
        }
        for field in (
            "method",
            "endpoint",
            "status_code",
            "request_id",
            "response_time_ms",
        ):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload, default=str, sort_keys=True)


def setup_logging(service: str, level: int = logging.INFO, stream=None) -> logging.Handler:
    """Configure the request logger with a JSON handler."""
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(JsonFormatter())
    RequestLogger.addHandler(handler)
    RequestLogger.setLevel(level)
    RequestLogger.propagate = False
    return handler


def generate_request_id() -> str:
    """Return a fresh unique request ID (uuid4 hex)."""
    return uuid.uuid4().hex


def get_request_id() -> str | None:
    """Return the request ID of the in-flight request, if any."""
    return _current_request_id.get()


class RequestContextMiddleware:
    """Assign/propagate a request ID, time the request, and log it as JSON."""

    def __init__(self, app, service: str) -> None:
        self.app = app
        self.service = service

    async def __call__(self, scope: dict, receive, send) -> None:
        if scope["type"] != "http":  # pragma: no cover - exercised by other clients
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        incoming = headers.get(b"x-request-id")
        request_id = (
            incoming.decode("ascii") if incoming else generate_request_id()
        )
        token = _current_request_id.set(request_id)

        method = scope.get("method", "")
        endpoint = scope.get("path", "")
        status_holder = {"code": 500}
        start = time.perf_counter()

        async def wrapped_send(message: dict) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
                extra_headers = message.get("headers", [])
                extra_headers.append(
                    (b"x-request-id", request_id.encode("ascii"))
                )
                message["headers"] = extra_headers
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception:  # pragma: no cover - defensive; routes return responses
            RequestLogger.exception(
                "request failed",
                extra={"service": self.service},
            )
            raise
        finally:
            _current_request_id.reset(token)
            duration_ms = (time.perf_counter() - start) * 1000.0
            RequestLogger.info(
                "request completed",
                extra={
                    "service": self.service,
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": status_holder["code"],
                    "request_id": request_id,
                    "response_time_ms": round(duration_ms, 3),
                },
            )