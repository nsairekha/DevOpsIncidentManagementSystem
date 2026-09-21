"""Service information and dependency endpoints for the user-service."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from services.user_service.app.config import Settings, get_settings
from services.user_service.app.models.user import (
    DependencyList,
    ServiceInfo,
)

router = APIRouter(prefix="/api/v1", tags=["info"])


@router.get("/", response_model=ServiceInfo, summary="Service information")
def api_info(settings: Settings = Depends(get_settings)) -> ServiceInfo:
    """Return service identification and the available endpoints."""
    return ServiceInfo(
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc).isoformat(),
        endpoints=["/health", "/api/v1/", "/api/v1/dependencies", "/api/v1/users/{user_id}"],
    )


@router.get(
    "/dependencies",
    response_model=DependencyList,
    summary="Service dependencies",
)
def dependencies(settings: Settings = Depends(get_settings)) -> DependencyList:
    """Return the downstream dependencies of the user-service (none)."""
    return DependencyList(service=settings.service_name, dependencies=[])