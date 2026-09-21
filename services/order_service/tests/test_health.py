"""Tests for the order-service health, info, and plumbing endpoints."""

from datetime import datetime

from fastapi.testclient import TestClient


def test_health(order_client: TestClient) -> None:
    """GET /health reports a healthy order-service with identification."""
    body = order_client.get("/health").json()

    assert body["status"] == "healthy"
    assert body["service"] == "order-service"
    assert body["version"] == "1.0.0"
    assert body["environment"] == "development"
    assert datetime.fromisoformat(body["timestamp"]).tzinfo is not None


def test_api_info(order_client: TestClient) -> None:
    """GET /api/v1/ identifies the service and lists endpoints."""
    body = order_client.get("/api/v1/").json()

    assert body["service"] == "order-service"
    assert "/api/v1/orders" in body["endpoints"]


def test_dependencies_lists_downstream_services(order_client: TestClient) -> None:
    """GET /api/v1/dependencies names payment and notification over HTTP."""
    body = order_client.get("/api/v1/dependencies").json()

    assert body["service"] == "order-service"
    by_name = {d["service"]: d for d in body["dependencies"]}
    assert by_name["payment-service"]["type"] == "http"
    assert by_name["payment-service"]["url"].endswith(":8003")
    assert by_name["notification-service"]["type"] == "http"
    assert by_name["notification-service"]["url"].endswith(":8004")


def test_request_id_header_present_and_unique(order_client: TestClient) -> None:
    """Every response carries a unique X-Request-ID header."""
    first = order_client.get("/health")
    second = order_client.get("/health")

    assert first.headers.get("x-request-id")
    assert first.headers["x-request-id"] != second.headers["x-request-id"]