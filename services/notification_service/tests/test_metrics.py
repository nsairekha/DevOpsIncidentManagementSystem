"""Tests for the notification-service Prometheus metrics."""

from fastapi.testclient import TestClient


def _metrics(notification_client: TestClient) -> str:
    response = notification_client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    return response.text


def test_metrics_endpoint_uses_prometheus_format(
    notification_client: TestClient,
) -> None:
    """GET /metrics serves the Prometheus text exposition format."""
    body = _metrics(notification_client)

    assert "# HELP http_requests_total" in body
    assert "# TYPE http_request_duration_seconds histogram" in body


def test_notification_application_counters(
    notification_client: TestClient,
) -> None:
    """Sent notifications feed totals, successes, and durations."""
    notification_client.post(
        "/api/v1/notifications",
        json={"user_id": 1, "message": "hello", "type": "order_update"},
    )

    body = _metrics(notification_client)

    assert "\nnotifications_total 1.0" in body
    assert "\nnotifications_success_total 1.0" in body
    assert "\nnotification_processing_duration_seconds_count 1.0" in body


def test_request_counter_and_service_up(notification_client: TestClient) -> None:
    """HTTP counters carry status labels and service_up reports healthy."""
    notification_client.post(
        "/api/v1/notifications",
        json={"user_id": 1, "message": "hello", "type": "order_update"},
    )

    body = _metrics(notification_client)

    assert 'http_requests_total{endpoint="/api/v1/notifications",method="POST",service="notification-service",status_code="200"} 1.0' in body
    assert 'service_up{service="notification-service"} 1.0' in body


def test_request_id_never_becomes_a_label(
    notification_client: TestClient,
) -> None:
    """Request IDs stay in logs; they must not appear as metric labels."""
    notification_client.get("/health", headers={"X-Request-ID": "trace-secret-3"})

    body = _metrics(notification_client)

    assert "request_id" not in body
    assert "trace-secret-3" not in body