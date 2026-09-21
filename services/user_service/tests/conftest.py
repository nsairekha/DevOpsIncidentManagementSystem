"""Shared pytest fixtures for the user-service test suite."""

import pytest
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry

from services.user_service.app.main import create_app


@pytest.fixture()
def user_client() -> TestClient:
    """Provide a TestClient bound to a fresh app with an isolated registry."""
    return TestClient(create_app(registry=CollectorRegistry()))