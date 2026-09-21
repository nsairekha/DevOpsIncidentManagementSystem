"""Shared pytest fixtures for the backend test suite."""

import pytest
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry

from backend.app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    """Provide a TestClient bound to a fresh app with an isolated registry."""
    app = create_app(registry=CollectorRegistry())
    return TestClient(app)