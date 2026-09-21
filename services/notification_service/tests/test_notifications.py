"""Tests for simulated notification delivery."""

from fastapi.testclient import TestClient


def test_create_notification(notification_client: TestClient) -> None:
    """POST /api/v1/notifications simulates delivery as sent."""
    response = notification_client.post(
        "/api/v1/notifications",
        json={
            "user_id": 1,
            "message": "Order 1001 payment successful",
            "type": "order_update",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["notification_id"]
    assert body["user_id"] == 1
    assert body["status"] == "sent"


def test_create_notification_rejects_empty_message(
    notification_client: TestClient,
) -> None:
    """Empty messages fail validation with a JSON 422."""
    response = notification_client.post(
        "/api/v1/notifications",
        json={"user_id": 1, "message": "", "type": "order_update"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_unknown_path_returns_json_404(notification_client: TestClient) -> None:
    """Unmatched paths produce a JSON 404 with a detail message."""
    response = notification_client.get("/no-such-path")

    assert response.status_code == 404
    assert "detail" in response.json()