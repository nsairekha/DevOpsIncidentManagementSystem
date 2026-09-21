"""Tests for the user-service health endpoint and request plumbing."""

import json
import logging
from datetime import datetime

from fastapi.testclient import TestClient

from services.user_service.app.request_logging import JsonFormatter


def test_health_reports_healthy_user_service(user_client: TestClient) -> None:
    """GET /health reports a healthy user-service."""
    response = user_client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "user-service"


def test_health_response_structure(user_client: TestClient) -> None:
    """The health payload exposes name, version, environment and timestamp."""
    body = user_client.get("/health").json()

    assert set(body) == {"status", "service", "version", "environment", "timestamp"}
    assert body["version"] == "1.0.0"
    assert body["environment"] == "development"
    assert datetime.fromisoformat(body["timestamp"]).tzinfo is not None


def test_request_id_header_present_and_unique(user_client: TestClient) -> None:
    """Every response carries a unique X-Request-ID header."""
    first = user_client.get("/health")
    second = user_client.get("/health")

    assert first.headers.get("x-request-id")
    assert second.headers.get("x-request-id")
    assert first.headers["x-request-id"] != second.headers["x-request-id"]


def test_request_log_is_structured_json(user_client: TestClient) -> None:
    """Each request is logged as JSON with the required fields."""
    records: list[logging.LogRecord] = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger("request")
    handler = ListHandler()
    logger.addHandler(handler)
    try:
        user_client.get("/health")
    finally:
        logger.removeHandler(handler)

    entries = [r for r in records if getattr(r, "endpoint", "") == "/health"]
    assert entries, "expected a request log entry for /health"

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
    assert payload["service"] == "user-service"
    assert payload["status_code"] == 200