"""Structured JSON logging and per-request context.

Every HTTP request gets a unique request ID, is timed, and is logged on
completion as a single JSON line containing:

- ``timestamp`` (UTC)
- ``service``
- ``method`` (HTTP method)
- ``endpoint`` (request path)
- ``status_code``
- ``request_id``
- ``response_time_ms``

The request ID is also returned to callers in the ``X-Request-ID`` response
header.
"""

import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone

RequestLogger = logging.getLogger("request")


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
    """Configure the request logger with a JSON handler.

    Args:
        service: Name of the service emitting the logs.
        level: Minimum log level.
        stream: Optional output stream (defaults to stderr).

    Returns:
        The handler attached to the request logger.
    """
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(JsonFormatter())
    RequestLogger.addHandler(handler)
    RequestLogger.setLevel(level)
    RequestLogger.propagate = False
    return handler


def generate_request_id() -> str:
    """Return a fresh unique request ID (uuid4 hex)."""
    return uuid.uuid4().hex


class RequestContextMiddleware:
    """Assign a request ID, time the request, and log it as JSON."""

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