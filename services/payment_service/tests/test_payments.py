"""Tests for simulated payment processing and retrieval."""

from fastapi.testclient import TestClient


def test_create_payment(payment_client: TestClient) -> None:
    """POST /api/v1/payments simulates a successful payment."""
    response = payment_client.post(
        "/api/v1/payments",
        json={"order_id": 1001, "user_id": 1, "amount": 999.0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["payment_id"]
    assert body["order_id"] == 1001
    assert body["status"] == "success"
    assert body["amount"] == 999.0


def test_get_payment_roundtrip(payment_client: TestClient) -> None:
    """A created payment can be retrieved by its generated ID."""
    created = payment_client.post(
        "/api/v1/payments",
        json={"order_id": 1001, "user_id": 1, "amount": 10.0},
    ).json()

    fetched = payment_client.get(f"/api/v1/payments/{created['payment_id']}").json()

    assert fetched == created


def test_get_unknown_payment_returns_404(payment_client: TestClient) -> None:
    """Unknown payment IDs produce a JSON 404."""
    response = payment_client.get("/api/v1/payments/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Payment does-not-exist not found"}


def test_create_payment_rejects_bad_amount(payment_client: TestClient) -> None:
    """Non-positive amounts fail validation with a JSON 422."""
    response = payment_client.post(
        "/api/v1/payments",
        json={"order_id": 1001, "user_id": 1, "amount": 0},
    )

    assert response.status_code == 422
    assert "detail" in response.json()