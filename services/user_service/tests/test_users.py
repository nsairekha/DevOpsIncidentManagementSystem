"""Tests for the user retrieval endpoint (in-memory store)."""

from fastapi.testclient import TestClient


def test_get_user_returns_structured_user(user_client: TestClient) -> None:
    """GET /api/v1/users/{id} returns the seeded user record."""
    response = user_client.get("/api/v1/users/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "active": True,
    }


def test_get_user_response_structure(user_client: TestClient) -> None:
    """User payloads expose exactly the documented fields."""
    body = user_client.get("/api/v1/users/2").json()

    assert set(body) == {"id", "name", "email", "active"}
    assert body["id"] == 2
    assert body["email"] == "grace@example.com"


def test_get_unknown_user_returns_404(user_client: TestClient) -> None:
    """Unknown user IDs produce a JSON 404 with a detail message."""
    response = user_client.get("/api/v1/users/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "User 999 not found"}


def test_get_user_rejects_non_integer_id(user_client: TestClient) -> None:
    """Non-integer IDs fail validation with a JSON 422."""
    response = user_client.get("/api/v1/users/not-an-id")

    assert response.status_code == 422
    assert "detail" in response.json()