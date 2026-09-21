"""Health endpoint for the user-service."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from services.user_service.app.config import Settings, get_settings
from services.user_service.app.models.user import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="User-service health check")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Report the user-service status and identification (UTC timestamp)."""
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )