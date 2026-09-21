"""Application configuration loaded from environment variables and .env.

Settings are defined with pydantic-settings so they can be overridden via
environment variables (e.g. ``APP_ENV=production``) or a local ``.env`` file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the backend application."""

    # --- Application ---
    app_env: str = "development"
    app_name: str = "ai-cloud-observability"
    app_version: str = "0.1.0"
    debug: bool = False
    # Logical service name reported by health/info endpoints.
    service_name: str = "backend"

    # --- Placeholder connection settings (filled in by later milestones) ---
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    prometheus_url: str | None = None
    database_url: str | None = None
    blockchain_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton for the app lifetime)."""
    return Settings()


# Convenience instance for non-DI usage (e.g. module-level defaults).
settings = get_settings()