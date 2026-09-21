"""Tests for the order-service Prometheus metrics (incl. dependencies)."""

import httpx
import pytest
from fastapi.testclient import TestClient

from services.order_service.app import routes
from services.order_service.app.clients import (
    NotificationClient,
    PaymentClient,
)

ORDER_PAYLOAD = {
    "user_id": 1,
    "product": "Cloud Monitoring Subscription",
    "quantity": 1,
    "amount": 999.0,
}


def _metrics(order_client: TestClient) -> str:
    response = order_client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    return response.text


def _ok_payment(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"payment_id": "pay-1", "status": "success"},
    )


def _ok_notification(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"notification_id": "n-1", "status": "sent"})


def _wire_success(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_metrics_endpoint_uses_prometheus_format(order_client: TestClient) -> None:
    """GET /metrics serves the Prometheus text exposition format."""
    body = _metrics(order_client)

    assert "# HELP http_requests_total" in body
    assert "# HELP dependency_requests_total" in body
    assert 'service_up{service="order-service"} 1.0' in body


def test_order_application_counters(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Created orders feed totals and the processing-duration histogram."""
    _wire_success(monkeypatch)
    order_client.post("/api/v1/orders", json=ORDER_PAYLOAD)

    body = _metrics(order_client)

    assert "\norders_created_total 1.0" in body
    assert "\norder_processing_duration_seconds_count 1.0" in body
    assert 'http_requests_total{endpoint="/api/v1/orders",method="POST",service="order-service",status_code="201"} 1.0' in body


def test_order_failure_counters(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failed orders and payment dependency errors are counted."""
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

    body = _metrics(order_client)

    assert "\norders_created_total 1.0" in body
    assert "\norders_failed_total 1.0" in body
    assert "\npayment_dependency_requests_total 1.0" in body
    assert "\npayment_dependency_errors_total 1.0" in body
    assert 'http_requests_total{endpoint="/api/v1/orders",method="POST",service="order-service",status_code="503"} 1.0' in body
    assert 'http_request_errors_total{endpoint="/api/v1/orders",method="POST",service="order-service",status_code="503"} 1.0' in body


def test_generic_dependency_metrics(
    order_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Source/target-labelled dependency metrics track calls and latency."""
    _wire_success(monkeypatch)
    order_client.post("/api/v1/orders", json=ORDER_PAYLOAD)

    body = _metrics(order_client)

    pay = 'source_service="order-service",target_service="payment-service"'
    notif = 'source_service="order-service",target_service="notification-service"'
    assert f"dependency_requests_total{{endpoint=\"/api/v1/payments\",{pay}}} 1.0" in body
    assert f"dependency_requests_total{{endpoint=\"/api/v1/notifications\",{notif}}} 1.0" in body
    assert f"dependency_request_duration_seconds_count{{endpoint=\"/api/v1/payments\",{pay}}} 1.0" in body
    assert f"dependency_request_duration_seconds_count{{endpoint=\"/api/v1/notifications\",{notif}}} 1.0" in body
    assert "\nnotification_dependency_requests_total 1.0" in body


def test_unmatched_route_label_is_bounded(order_client: TestClient) -> None:
    """Requests matching no route are labelled 'unmatched', not by raw path."""
    order_client.get("/some/arbitrary/path/12345")

    body = _metrics(order_client)

    assert 'http_requests_total{endpoint="unmatched",method="GET",service="order-service",status_code="404"} 1.0' in body
    assert "/some/arbitrary/path/12345" not in body


def test_request_id_never_becomes_a_label(order_client: TestClient) -> None:
    """Request IDs stay in logs; they must not appear as metric labels."""
    order_client.get("/health", headers={"X-Request-ID": "trace-secret-4"})

    body = _metrics(order_client)

    assert "request_id" not in body
    assert "trace-secret-4" not in body