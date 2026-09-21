"""Payment-service configuration (environment variables only).

Supported variables:

SERVICE_NAME / SERVICE_VERSION / APP_ENV / PORT / REQUEST_TIMEOUT_SECONDS /
SIMULATED_LATENCY_MS
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the payment-service."""

    service_name: str = "payment-service"
    service_version: str = "1.0.0"
    app_env: str = "development"
    port: int = 8003
    request_timeout_seconds: float = 5.0
    simulated_latency_ms: int = 0

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