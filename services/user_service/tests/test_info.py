"""Tests for the user-service info and dependency endpoints."""

from fastapi.testclient import TestClient


def test_api_info(user_client: TestClient) -> None:
    """GET /api/v1/ identifies the service and lists endpoints."""
    body = user_client.get("/api/v1/").json()

    assert body["service"] == "user-service"
    assert body["version"] == "1.0.0"
    assert body["environment"] == "development"
    assert "/api/v1/users/{user_id}" in body["endpoints"]


def test_dependencies(user_client: TestClient) -> None:
    """GET /api/v1/dependencies reports no downstream dependencies."""
    body = user_client.get("/api/v1/dependencies").json()

    assert body["service"] == "user-service"
    assert body["dependencies"] == []