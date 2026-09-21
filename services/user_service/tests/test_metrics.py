"""Tests for the user-service Prometheus metrics."""

from fastapi.testclient import TestClient


def _metrics(user_client: TestClient) -> str:
    response = user_client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    return response.text


def test_metrics_endpoint_uses_prometheus_format(user_client: TestClient) -> None:
    """GET /metrics serves the Prometheus text exposition format."""
    body = _metrics(user_client)

    assert "# HELP http_requests_total" in body
    assert "# TYPE http_requests_total counter" in body
    assert "# TYPE http_request_duration_seconds histogram" in body


def test_request_counter_labels(user_client: TestClient) -> None:
    """Requests are counted with service, method, route template, and status."""
    user_client.get("/api/v1/users/1")
    user_client.get("/api/v1/users/2")
    user_client.get("/api/v1/users/999")

    body = _metrics(user_client)

    ok = 'http_requests_total{endpoint="/api/v1/users/{user_id}",method="GET",service="user-service",status_code="200"} 2.0'
    missing = 'http_requests_total{endpoint="/api/v1/users/{user_id}",method="GET",service="user-service",status_code="404"} 1.0'
    assert ok in body
    assert missing in body
    # Concrete IDs must never become metric labels.
    assert "/api/v1/users/1" not in body
    assert "/api/v1/users/2" not in body


def test_error_counter_tracks_4xx(user_client: TestClient) -> None:
    """4xx answers increment the error counter alongside the total."""
    user_client.get("/api/v1/users/999")

    body = _metrics(user_client)

    assert 'http_request_errors_total{endpoint="/api/v1/users/{user_id}",method="GET",service="user-service",status_code="404"} 1.0' in body


def test_latency_histogram_records_observations(user_client: TestClient) -> None:
    """Latency observations land in histogram buckets (P50/P95/P99 capable)."""
    user_client.get("/health")

    body = _metrics(user_client)

    assert 'http_request_duration_seconds_count{endpoint="/health",method="GET",service="user-service"} 1.0' in body
    assert 'http_request_duration_seconds_bucket{endpoint="/health",le=' in body


def test_in_flight_gauge_drains(user_client: TestClient) -> None:
    """After requests complete, the in-flight gauge returns to zero."""
    user_client.get("/health")

    body = _metrics(user_client)

    assert 'http_requests_in_progress{method="GET",service="user-service"} 0.0' in body


def test_service_up_reports_healthy(user_client: TestClient) -> None:
    """service_up is 1 for the running service."""
    body = _metrics(user_client)

    assert 'service_up{service="user-service"} 1.0' in body


def test_user_application_counters(user_client: TestClient) -> None:
    """User lookups and lookup errors feed the application counters."""
    user_client.get("/api/v1/users/1")
    user_client.get("/api/v1/users/999")

    body = _metrics(user_client)

    assert "\nuser_requests_total 2.0" in body
    assert "\nuser_lookup_errors_total 1.0" in body


def test_metrics_endpoint_is_not_counted(user_client: TestClient) -> None:
    """Scraping /metrics does not feed back into the request counters."""
    user_client.get("/metrics")

    body = _metrics(user_client)

    assert 'endpoint="/metrics"' not in body


def test_request_id_never_becomes_a_label(user_client: TestClient) -> None:
    """Request IDs stay in logs; they must not appear as metric labels."""
    user_client.get("/health", headers={"X-Request-ID": "trace-secret-1"})

    body = _metrics(user_client)

    assert "request_id" not in body
    assert "trace-secret-1" not in body


def test_health_behavior_unchanged(user_client: TestClient) -> None:
    """Metrics plumbing does not alter the health payload."""
    body = user_client.get("/health").json()

    assert body["status"] == "healthy"
    assert body["service"] == "user-service"