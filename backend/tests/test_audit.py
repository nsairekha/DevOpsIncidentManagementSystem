"""Tests for the /api/audit endpoint and CORS configuration."""

from fastapi.testclient import TestClient


def test_audit_starts_with_genesis_block(client: TestClient) -> None:
    """A fresh app exposes a single, valid genesis block."""
    response = client.get("/api/audit")

    assert response.status_code == 200
    body = response.json()
    assert body["length"] == 1
    assert body["valid"] is True
    assert body["errors"] == []
    assert len(body["last_hash"]) == 64
    assert body["blocks"][0]["event_type"] == "GENESIS"
    assert body["blocks"][0]["previous_hash"] == "0" * 64


def test_audit_accumulates_analysis_events(client: TestClient) -> None:
    """Analysis runs append agent_result blocks to the exposed trail."""
    client.post(
        "/api/analyze",
        json={"reference": {"cpu": [10.0] * 5}, "telemetry": {"cpu": [9.9, 10.1]}},
    )
    client.post(
        "/api/analyze",
        json={"reference": {"cpu": [10.0] * 5}, "telemetry": {"cpu": [9.9, 10.1]}},
    )

    body = client.get("/api/audit").json()

    assert body["length"] == 3
    event_types = [b["event_type"] for b in body["blocks"]]
    assert event_types == ["GENESIS", "agent_result", "agent_result"]
    assert body["valid"] is True
    # Blocks are properly chained.
    for previous, current in zip(body["blocks"], body["blocks"][1:]):
        assert current["previous_hash"] == previous["hash"]


def test_cors_preflight_allows_dashboard_origin(client: TestClient) -> None:
    """The dashboard origin receives CORS headers on requests and preflights."""
    allowed = client.get(
        "/health", headers={"Origin": "http://localhost:3000"}
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"

    preflight = client.options(
        "/api/analyze",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.status_code == 200
    assert "POST" in preflight.headers.get("access-control-allow-methods", "")


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    """Origins outside the allow list get no CORS header."""
    response = client.get("/health", headers={"Origin": "http://evil.example"})
    assert response.headers.get("access-control-allow-origin") is None