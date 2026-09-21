"""Tests for the payment-service health, info, and plumbing endpoints."""

from datetime import datetime

from fastapi.testclient import TestClient


def test_health(payment_client: TestClient) -> None:
    """GET /health reports a healthy payment-service with identification."""
    body = payment_client.get("/health").json()

    assert body["status"] == "healthy"
    assert body["service"] == "payment-service"
    assert body["version"] == "1.0.0"
    assert body["environment"] == "development"
    assert datetime.fromisoformat(body["timestamp"]).tzinfo is not None


def test_api_info(payment_client: TestClient) -> None:
    """GET /api/v1/ identifies the service and lists endpoints."""
    body = payment_client.get("/api/v1/").json()

    assert body["service"] == "payment-service"
    assert "/api/v1/payments" in body["endpoints"]


def test_dependencies(payment_client: TestClient) -> None:
    """GET /api/v1/dependencies reports no downstream dependencies yet."""
    body = payment_client.get("/api/v1/dependencies").json()

    assert body["service"] == "payment-service"
    assert body["dependencies"] == []


def test_request_id_header_present_and_unique(payment_client: TestClient) -> None:
    """Every response carries a unique X-Request-ID header."""
    first = payment_client.get("/health")
    second = payment_client.get("/health")

    assert first.headers.get("x-request-id")
    assert first.headers["x-request-id"] != second.headers["x-request-id"]


def test_incoming_request_id_is_honored(payment_client: TestClient) -> None:
    """A caller-provided X-Request-ID is echoed back unchanged."""
    response = payment_client.get("/health", headers={"X-Request-ID": "trace-abc"})

    assert response.headers["x-request-id"] == "trace-abc"