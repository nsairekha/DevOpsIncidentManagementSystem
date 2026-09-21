"""Tests for the versioned backend API (``/api/v1``) and request plumbing."""

import json
import logging
from datetime import datetime

from fastapi.testclient import TestClient

from backend.app.utils.logging import JsonFormatter


def test_app_title_is_ai_cloud_observability(client: TestClient) -> None:
    """The application carries the required service title."""
    assert client.app.title == "AI Cloud Observability"


def test_api_v1_health(client: TestClient) -> None:
    """GET /api/v1/health reports a healthy backend in development."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "backend"
    assert body["environment"] == "development"


def test_api_v1_health_response_structure(client: TestClient) -> None:
    """The health payload exposes name, version, environment and timestamp."""
    body = client.get("/api/v1/health").json()

    assert set(body) == {"status", "service", "environment", "version", "timestamp"}
    assert body["version"] == "0.1.0"
    # Timestamp must be a parseable UTC ISO-8601 string.
    parsed = datetime.fromisoformat(body["timestamp"])
    assert parsed.tzinfo is not None


def test_api_v1_root_returns_service_identification(client: TestClient) -> None:
    """GET /api/v1/ identifies the service and lists versioned endpoints."""
    response = client.get("/api/v1/")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "backend"
    assert body["version"] == "0.1.0"
    assert body["environment"] == "development"
    assert datetime.fromisoformat(body["timestamp"]).tzinfo is not None
    assert "/api/v1/health" in body["endpoints"]


def test_request_id_header_present_and_unique(client: TestClient) -> None:
    """Every response carries a unique X-Request-ID header."""
    first = client.get("/api/v1/health")
    second = client.get("/api/v1/health")

    assert first.headers.get("x-request-id")
    assert second.headers.get("x-request-id")
    assert first.headers["x-request-id"] != second.headers["x-request-id"]


def test_request_log_is_structured_json(client: TestClient) -> None:
    """Each request is logged as JSON with the required fields."""
    records: list[logging.LogRecord] = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger("request")
    handler = ListHandler()
    logger.addHandler(handler)
    try:
        client.get("/api/v1/health")
    finally:
        logger.removeHandler(handler)

    entries = [r for r in records if getattr(r, "endpoint", "") == "/api/v1/health"]
    assert entries, "expected a request log entry for /api/v1/health"

    payload = json.loads(JsonFormatter().format(entries[-1]))
    for field in (
        "timestamp",
        "service",
        "method",
        "endpoint",
        "status_code",
        "request_id",
        "response_time_ms",
    ):
        assert field in payload, f"missing log field: {field}"
    assert payload["service"] == "backend"
    assert payload["method"] == "GET"
    assert payload["status_code"] == 200