"""Tests for the Prometheus integration."""

import re

from fastapi.testclient import TestClient


def test_metrics_endpoint_exposes_prometheus_format(client: TestClient) -> None:
    """/metrics serves the Prometheus text exposition format."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "# HELP http_requests_total" in response.text
    assert "# TYPE http_requests_total counter" in response.text
    assert "# TYPE http_request_duration_seconds histogram" in response.text


def test_requests_are_counted_per_route(client: TestClient) -> None:
    """Hits are counted with method, route template, and status labels."""
    client.get("/health")
    client.get("/health")
    client.get("/")

    metrics = client.get("/metrics").text

    assert 'http_requests_total{method="GET",path="/health",status="200"} 2.0' in metrics
    assert 'http_requests_total{method="GET",path="/",status="200"} 1.0' in metrics


def test_app_info_gauge_present(client: TestClient) -> None:
    """Static application metadata is exposed as a gauge."""
    metrics = client.get("/metrics").text

    assert (
        'app_info{app_name="ai-cloud-observability",environment="development",'
        'version="0.1.0"} 1.0' in metrics
    )


def test_metrics_endpoint_is_not_counted(client: TestClient) -> None:
    """Scraping /metrics does not feed back into the request counters."""
    client.get("/metrics")
    client.get("/metrics")
    client.get("/health")

    metrics = client.get("/metrics").text

    assert 'path="/metrics"' not in metrics


def test_in_flight_gauge_returns_to_zero(client: TestClient) -> None:
    """After requests complete, the in-flight gauge drains to zero."""
    client.get("/health")

    metrics = client.get("/metrics").text

    assert re.search(r'http_requests_in_progress\{method="GET"\} 0\.0', metrics) is not None


def test_unmatched_routes_fall_back_to_raw_path(client: TestClient) -> None:
    """Requests without a matched route are labelled with the raw path."""
    client.get("/does-not-exist")

    metrics = client.get("/metrics").text

    assert 'http_requests_total{method="GET",path="/does-not-exist",status="404"} 1.0' in metrics


def test_duration_histogram_records_observations(client: TestClient) -> None:
    """Latency observations exist for the instrumented route."""
    client.get("/health")
    client.get("/health")

    metrics = client.get("/metrics").text

    count_line = (
        'http_request_duration_seconds_count{method="GET",path="/health"} 2.0'
    )
    assert count_line in metrics