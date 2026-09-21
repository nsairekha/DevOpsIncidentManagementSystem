"""Tests for the shared service utilities (logging, http, helpers)."""

import json
import logging
import time
from datetime import datetime

import httpx
import pytest

from services.common.http import DownstreamError, post_json
from services.common.logging import (
    JsonFormatter,
    generate_request_id,
    get_request_id,
    setup_logging,
)
from services.common.utils import apply_simulated_latency, utc_now_iso


def test_generate_request_id_unique() -> None:
    """Generated request IDs are non-empty and unique."""
    first, second = generate_request_id(), generate_request_id()

    assert first and second
    assert first != second


def test_get_request_id_defaults_to_none() -> None:
    """Outside a request, no request ID is set."""
    assert get_request_id() is None


def test_setup_logging_returns_json_handler() -> None:
    """setup_logging attaches a JSON-formatting handler."""
    handler = setup_logging("test-service")

    assert isinstance(handler.formatter, JsonFormatter)


def test_json_formatter_includes_all_fields() -> None:
    """Formatted request logs carry every required field."""
    record = logging.LogRecord(
        name="request",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request completed",
        args=(),
        exc_info=None,
    )
    record.service = "order-service"
    record.method = "POST"
    record.endpoint = "/api/v1/orders"
    record.status_code = 201
    record.request_id = "abc-123"
    record.response_time_ms = 12.5

    payload = json.loads(JsonFormatter().format(record))

    assert payload["service"] == "order-service"
    assert payload["method"] == "POST"
    assert payload["endpoint"] == "/api/v1/orders"
    assert payload["status_code"] == 201
    assert payload["request_id"] == "abc-123"
    assert payload["response_time_ms"] == 12.5
    assert datetime.fromisoformat(payload["timestamp"]).tzinfo is not None


def _success(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"ok": True})


def test_post_json_forwards_request_id() -> None:
    """An explicit request ID is forwarded as X-Request-ID."""
    seen: dict[str, str | None] = {}

    def capture(request: httpx.Request) -> httpx.Response:
        seen["id"] = request.headers.get("x-request-id")
        return _success(request)

    body = post_json(
        "downstream",
        "http://downstream/path",
        {"a": 1},
        timeout_seconds=5.0,
        request_id="trace-1",
        client=httpx.Client(transport=httpx.MockTransport(capture)),
    )

    assert body == {"ok": True}
    assert seen["id"] == "trace-1"


def test_post_json_without_request_context() -> None:
    """Outside a request, the call still works with no trace header."""
    seen: dict[str, str | None] = {"id": "unset"}

    def capture(request: httpx.Request) -> httpx.Response:
        seen["id"] = request.headers.get("x-request-id")
        return _success(request)

    body = post_json(
        "downstream",
        "http://downstream/path",
        {},
        timeout_seconds=5.0,
        client=httpx.Client(transport=httpx.MockTransport(capture)),
    )

    assert body == {"ok": True}
    assert seen["id"] is None


def test_post_json_creates_and_closes_own_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without an injected client, post_json owns and closes its client."""
    closed = {"value": False}
    transport_client = httpx.Client(transport=httpx.MockTransport(_success))
    original_close = transport_client.close

    def close() -> None:
        closed["value"] = True
        original_close()

    transport_client.close = close  # type: ignore[method-assign]
    monkeypatch.setattr(httpx, "Client", lambda timeout: transport_client)

    body = post_json(
        "downstream", "http://downstream/path", {}, timeout_seconds=5.0
    )

    assert body == {"ok": True}
    assert closed["value"] is True


def test_post_json_timeout_maps_to_downstream_error() -> None:
    """Timeouts become DownstreamError(kind='timeout')."""
    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("too slow")

    with pytest.raises(DownstreamError) as exc:
        post_json(
            "downstream",
            "http://downstream/path",
            {},
            timeout_seconds=1.0,
            client=httpx.Client(transport=httpx.MockTransport(slow)),
        )

    assert exc.value.service == "downstream"
    assert exc.value.kind == "timeout"
    assert exc.value.status_code is None


def test_post_json_http_error_carries_status() -> None:
    """Non-2xx answers become DownstreamError with the status attached."""
    def broken(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "down"})

    with pytest.raises(DownstreamError) as exc:
        post_json(
            "downstream",
            "http://downstream/path",
            {},
            timeout_seconds=5.0,
            client=httpx.Client(transport=httpx.MockTransport(broken)),
        )

    assert exc.value.kind == "http_error"
    assert exc.value.status_code == 503


def test_post_json_invalid_json_body() -> None:
    """A 200 with a non-JSON body becomes a DownstreamError."""
    def text(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    with pytest.raises(DownstreamError) as exc:
        post_json(
            "downstream",
            "http://downstream/path",
            {},
            timeout_seconds=5.0,
            client=httpx.Client(transport=httpx.MockTransport(text)),
        )

    assert exc.value.kind == "http_error"


def test_utc_now_iso_is_timezone_aware() -> None:
    """utc_now_iso returns a parseable UTC timestamp."""
    parsed = datetime.fromisoformat(utc_now_iso())

    assert parsed.tzinfo is not None


def test_apply_simulated_latency_zero_is_noop() -> None:
    """Zero latency returns immediately."""
    start = time.perf_counter()
    apply_simulated_latency(0)
    assert time.perf_counter() - start < 0.05


def test_apply_simulated_latency_sleeps() -> None:
    """A positive latency blocks for approximately that long."""
    start = time.perf_counter()
    apply_simulated_latency(120)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert elapsed_ms >= 100


def test_apply_simulated_latency_rejects_negative() -> None:
    """Negative latency raises ValueError."""
    with pytest.raises(ValueError, match="latency_ms"):
        apply_simulated_latency(-1)