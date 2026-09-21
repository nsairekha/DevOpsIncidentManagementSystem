"""Health and API information endpoints (``/api/v1``).

Routes delegate to the service layer; they contain no business logic.
"""

from fastapi import APIRouter, Depends

from backend.app.config import Settings, get_settings
from backend.app.models.health import ApiInfoResponse, HealthResponse, LegacyHealthResponse
from backend.app.services import health_service

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Backend health check")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Report the backend service status and identification."""
    return health_service.get_health(settings)


@router.get("/", response_model=ApiInfoResponse, summary="API information")
def api_info(settings: Settings = Depends(get_settings)) -> ApiInfoResponse:
    """Return service identification and the available versioned endpoints."""
    return health_service.get_api_info(settings)


legacy_router = APIRouter(tags=["health"])


@legacy_router.get(
    "/health", response_model=LegacyHealthResponse, summary="Legacy health check"
)
def legacy_health(settings: Settings = Depends(get_settings)) -> LegacyHealthResponse:
    """Operational health endpoint (used by container probes).

    Preserved from the original backend skeleton; new clients should use
    ``GET /api/v1/health``.
    """
    return LegacyHealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


@legacy_router.get("/", include_in_schema=False)
def root(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Confirm the API is running (legacy root endpoint)."""
    return {"message": f"{settings.app_name} API is running"}