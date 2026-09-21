"""User-service configuration (environment variables, no .env coupling).

The service stays independent from the backend: it reads plain environment
variables (``SERVICE_NAME``, ``SERVICE_VERSION``, ``APP_ENV``) and does not
load the backend's ``.env`` file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the user-service."""

    service_name: str = "user-service"
    service_version: str = "1.0.0"
    app_env: str = "development"

    model_config = SettingsConfigDict(
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