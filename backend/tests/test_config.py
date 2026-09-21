"""Tests for application configuration defaults."""

from backend.app.config import Settings


def test_settings_defaults() -> None:
    """Settings fall back to sensible defaults when no .env is present."""
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.app_name == "ai-cloud-observability"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.blockchain_enabled is False


def test_settings_override_from_environment(monkeypatch) -> None:
    """Settings honor environment variable overrides."""
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("APP_NAME", "custom-name")

    settings = Settings()

    assert settings.app_env == "testing"
    assert settings.app_name == "custom-name"


def test_prometheus_url_setting(monkeypatch) -> None:
    """The Prometheus URL is readable from the environment."""
    monkeypatch.setenv("PROMETHEUS_URL", "http://localhost:9090")

    settings = Settings()

    assert settings.prometheus_url == "http://localhost:9090"