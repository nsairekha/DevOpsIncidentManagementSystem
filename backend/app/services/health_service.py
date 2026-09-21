"""Business/service logic for the backend."""

from datetime import datetime, timezone

from backend.app.models.health import ApiInfoResponse, HealthResponse
from backend.app.config import Settings


def get_health(settings: Settings) -> HealthResponse:
    """Build the health response for the backend service."""
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        environment=settings.app_env,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def get_api_info(settings: Settings) -> ApiInfoResponse:
    """Build the API information (service identification) response."""
    return ApiInfoResponse(
        service=settings.service_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc).isoformat(),
        endpoints=["/api/v1/health", "/api/v1/"],
    )