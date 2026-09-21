"""Tests for the health endpoint."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """The health endpoint reports a healthy service with metadata."""
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "ai-cloud-observability"
    assert body["version"] == "0.1.0"
    assert body["environment"] == "development"


def test_root_returns_running_message(client: TestClient) -> None:
    """The root endpoint confirms the API is running."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "ai-cloud-observability API is running"