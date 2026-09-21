"""Tests for the payment-service Prometheus metrics."""

from fastapi.testclient import TestClient


def _metrics(payment_client: TestClient) -> str:
    response = payment_client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    return response.text


def test_metrics_endpoint_uses_prometheus_format(payment_client: TestClient) -> None:
    """GET /metrics serves the Prometheus text exposition format."""
    body = _metrics(payment_client)

    assert "# HELP http_requests_total" in body
    assert "# TYPE http_request_duration_seconds histogram" in body


def test_payment_application_counters(payment_client: TestClient) -> None:
    """Processed payments feed totals, successes, and durations."""
    payment_client.post(
        "/api/v1/payments", json={"order_id": 1001, "user_id": 1, "amount": 5.0}
    )

    body = _metrics(payment_client)

    assert "\npayments_total 1.0" in body
    assert "\npayments_success_total 1.0" in body
    assert "\npayment_processing_duration_seconds_count 1.0" in body


def test_failed_counter_present(payment_client: TestClient) -> None:
    """The failed-payments counter is exported (0 while simulation never fails)."""
    body = _metrics(payment_client)

    assert "\npayments_failed_total 0.0" in body


def test_request_counter_and_errors(payment_client: TestClient) -> None:
    """HTTP counters carry status labels; 4xx also feeds the error counter."""
    payment_client.get("/health")
    payment_client.get("/api/v1/payments/missing")

    body = _metrics(payment_client)

    assert 'http_requests_total{endpoint="/health",method="GET",service="payment-service",status_code="200"} 1.0' in body
    assert 'http_requests_total{endpoint="/api/v1/payments/{payment_id}",method="GET",service="payment-service",status_code="404"} 1.0' in body
    assert 'http_request_errors_total{endpoint="/api/v1/payments/{payment_id}",method="GET",service="payment-service",status_code="404"} 1.0' in body
    assert 'service_up{service="payment-service"} 1.0' in body


def test_request_id_never_becomes_a_label(payment_client: TestClient) -> None:
    """Request IDs stay in logs; they must not appear as metric labels."""
    payment_client.get("/health", headers={"X-Request-ID": "trace-secret-2"})

    body = _metrics(payment_client)

    assert "request_id" not in body
    assert "trace-secret-2" not in body