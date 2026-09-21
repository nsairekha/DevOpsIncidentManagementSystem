"""Tests for order creation, retrieval, and downstream failure handling.

Downstream HTTP calls are mocked with ``httpx.MockTransport`` so no servers
are required; the order-service still exercises its real HTTP client code.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from services.order_service.app import routes
from services.order_service.app.clients import (
    NotificationClient,
    PaymentClient,
)
from services.order_service.app.config import Settings

ORDER_PAYLOAD = {
    "user_id": 1,
    "product": "Cloud Monitoring Subscription",
    "quantity": 1,
    "amount": 999.0,
}


def _ok_payment(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "payment_id": "pay-1",
            "order_id": 1001,
            "user_id": 1,
            "status": "success",
            "amount": 999.0,
            "timestamp": "2026-01-01T00:00:00+00:00",
        },
    )


def _ok_notification(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "notification_id": "notif-1",
            "user_id": 1,
            "status": "sent",
            "timestamp": "2026-01-01T00:00:00+00:00",
        },
    )


def _wire_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the order-service at healthy mocked downstream services."""
    monkeypatch.setattr(
        routes,
        "build_payment_client",
        lambda settings: PaymentClient(
            "http://payment",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(_ok_payment)),
        ),
    )
    monkeypatch.setattr(
        routes,
        "build_notification_client",
        lambda settings: NotificationClient(
            "http://notification",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(_ok_notification)),
        ),
    )


def test_build_clients_use_configured_urls() -> None:
    """Client factories read downstream URLs from configuration (no hard-coding)."""
    settings = Settings()

    assert (
        routes.build_payment_client(settings).base_url == settings.payment_service_url
    )
    assert (
        routes.build_notification_client(settings).base_url
        == settings.notification_service_url
    )


def test_create_order_full_flow(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /api/v1/orders charges and notifies, returning the enriched order."""
    _wire_success(monkeypatch)

    response = order_client.post("/api/v1/orders", json=ORDER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["order_id"] == 1001
    assert body["user_id"] == 1
    assert body["product"] == "Cloud Monitoring Subscription"
    assert body["quantity"] == 1
    assert body["amount"] == 999.0
    assert body["status"] == "created"
    assert body["payment_id"] == "pay-1"
    assert body["payment_status"] == "success"
    assert body["notification_status"] == "sent"


def test_get_order_roundtrip(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A created order can be retrieved by ID."""
    _wire_success(monkeypatch)
    created = order_client.post("/api/v1/orders", json=ORDER_PAYLOAD).json()

    fetched = order_client.get(f"/api/v1/orders/{created['order_id']}").json()

    assert fetched == created


def test_get_unknown_order_returns_404(order_client: TestClient) -> None:
    """Unknown order IDs produce a JSON 404."""
    response = order_client.get("/api/v1/orders/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Order 9999 not found"}


def test_create_order_rejects_invalid_payload(order_client: TestClient) -> None:
    """Zero quantity fails validation with a JSON 422."""
    response = order_client.post("/api/v1/orders", json={**ORDER_PAYLOAD, "quantity": 0})

    assert response.status_code == 422
    assert "detail" in response.json()


def test_request_id_propagates_to_downstream(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The caller's X-Request-ID reaches payment and notification untouched."""
    seen: dict[str, str | None] = {}

    def capture_payment(request: httpx.Request) -> httpx.Response:
        seen["payment"] = request.headers.get("x-request-id")
        return _ok_payment(request)

    def capture_notification(request: httpx.Request) -> httpx.Response:
        seen["notification"] = request.headers.get("x-request-id")
        return _ok_notification(request)

    monkeypatch.setattr(
        routes,
        "build_payment_client",
        lambda settings: PaymentClient(
            "http://payment",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(capture_payment)),
        ),
    )
    monkeypatch.setattr(
        routes,
        "build_notification_client",
        lambda settings: NotificationClient(
            "http://notification",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(capture_notification)),
        ),
    )

    response = order_client.post(
        "/api/v1/orders", json=ORDER_PAYLOAD, headers={"X-Request-ID": "trace-123"}
    )

    assert response.status_code == 201
    assert response.headers["x-request-id"] == "trace-123"
    assert seen["payment"] == "trace-123"
    assert seen["notification"] == "trace-123"


def test_request_id_generated_when_absent(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a caller ID, one ID is generated and shared downstream."""
    seen: dict[str, str | None] = {}

    def capture(request: httpx.Request) -> httpx.Response:
        seen.setdefault("payment", request.headers.get("x-request-id"))
        return _ok_payment(request)

    monkeypatch.setattr(
        routes,
        "build_payment_client",
        lambda settings: PaymentClient(
            "http://payment",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(capture)),
        ),
    )
    monkeypatch.setattr(
        routes,
        "build_notification_client",
        lambda settings: NotificationClient(
            "http://notification",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(_ok_notification)),
        ),
    )

    response = order_client.post("/api/v1/orders", json=ORDER_PAYLOAD)

    generated = response.headers["x-request-id"]
    assert generated
    assert seen["payment"] == generated


def test_payment_unavailable_returns_503(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dead payment-service yields a structured 503 without crashing."""
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(
        routes,
        "build_payment_client",
        lambda settings: PaymentClient(
            "http://payment",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(refused)),
        ),
    )

    response = order_client.post("/api/v1/orders", json=ORDER_PAYLOAD)

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["error"] == "payment_service_unavailable"
    assert detail["service"] == "order-service"
    assert detail["request_id"] == response.headers["x-request-id"]
    assert detail["timestamp"]

    # The failed order is still recorded for inspection.
    stored = order_client.get("/api/v1/orders/1001").json()
    assert stored["payment_status"] == "failed"


def test_payment_timeout_returns_503(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A timed-out payment-service also yields a structured 503."""
    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("too slow")

    monkeypatch.setattr(
        routes,
        "build_payment_client",
        lambda settings: PaymentClient(
            "http://payment",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(slow)),
        ),
    )

    response = order_client.post("/api/v1/orders", json=ORDER_PAYLOAD)

    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "payment_service_unavailable"


def test_payment_http_error_returns_502(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 5xx from payment-service yields a structured 502."""
    def broken(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "boom"})

    monkeypatch.setattr(
        routes,
        "build_payment_client",
        lambda settings: PaymentClient(
            "http://payment",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(broken)),
        ),
    )

    response = order_client.post("/api/v1/orders", json=ORDER_PAYLOAD)

    assert response.status_code == 502
    assert response.json()["detail"]["error"] == "payment_failed"


def test_payment_non_success_status_returns_502(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 200 with a non-success status is treated as a payment failure."""
    def declined(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"payment_id": "pay-9", "status": "declined"})

    monkeypatch.setattr(
        routes,
        "build_payment_client",
        lambda settings: PaymentClient(
            "http://payment",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(declined)),
        ),
    )

    response = order_client.post("/api/v1/orders", json=ORDER_PAYLOAD)

    assert response.status_code == 502
    assert response.json()["detail"]["error"] == "payment_failed"


def test_notification_failure_keeps_payment_successful(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dead notification-service degrades the order instead of failing it."""
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(
        routes,
        "build_payment_client",
        lambda settings: PaymentClient(
            "http://payment",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(_ok_payment)),
        ),
    )
    monkeypatch.setattr(
        routes,
        "build_notification_client",
        lambda settings: NotificationClient(
            "http://notification",
            5.0,
            client=httpx.Client(transport=httpx.MockTransport(refused)),
        ),
    )

    response = order_client.post("/api/v1/orders", json=ORDER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["payment_status"] == "success"
    assert body["payment_id"] == "pay-1"
    assert body["notification_status"] == "failed"