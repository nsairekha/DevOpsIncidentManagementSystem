"""Notification-service API routes (health, info, dependencies, send)."""

import time

from fastapi import APIRouter, Depends, Request

from services.common.models import DependencyList, ServiceInfo
from services.common.utils import apply_simulated_latency, utc_now_iso
from services.notification_service.app import store
from services.notification_service.app.config import Settings, get_settings
from services.notification_service.app.models import (
    HealthResponse,
    Notification,
    NotificationRequest,
)

router = APIRouter(tags=["notification"])


@router.get("/health", response_model=HealthResponse, summary="Notification-service health check")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Report the notification-service status and identification (UTC timestamp)."""
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.app_env,
        timestamp=utc_now_iso(),
    )


@router.get("/api/v1/", response_model=ServiceInfo, summary="Service information")
def api_info(settings: Settings = Depends(get_settings)) -> ServiceInfo:
    """Return service identification and the available endpoints."""
    return ServiceInfo(
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.app_env,
        timestamp=utc_now_iso(),
        endpoints=[
            "/health",
            "/api/v1/",
            "/api/v1/dependencies",
            "/api/v1/notifications",
        ],
    )


@router.get(
    "/api/v1/dependencies",
    response_model=DependencyList,
    summary="Service dependencies",
)
def dependencies(settings: Settings = Depends(get_settings)) -> DependencyList:
    """Return the downstream dependencies of the notification-service (none yet)."""
    return DependencyList(service=settings.service_name, dependencies=[])


@router.post(
    "/api/v1/notifications",
    response_model=Notification,
    summary="Send a notification",
)
def create_notification(
    payload: NotificationRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Notification:
    """Simulate delivery and record the notification (no email/SMS provider)."""
    metrics = request.app.state.notification_metrics
    metrics.notifications_total.inc()
    started = time.perf_counter()
    apply_simulated_latency(settings.simulated_latency_ms)
    notification = store.send_notification(payload)
    metrics.notification_processing_duration_seconds.observe(
        time.perf_counter() - started
    )
    metrics.notifications_success_total.inc()
    return notification