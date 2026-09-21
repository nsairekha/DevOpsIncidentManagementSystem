"""Shared pytest fixtures for the payment-service test suite."""

import pytest
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry

from services.payment_service.app.main import create_app
from services.payment_service.app.store import reset_store


@pytest.fixture()
def payment_client() -> TestClient:
    """Provide a TestClient bound to a fresh app with an isolated registry."""
    reset_store()
    return TestClient(create_app(registry=CollectorRegistry()))