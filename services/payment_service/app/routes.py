"""Payment-service API routes (health, info, dependencies, payments)."""

import time

from fastapi import APIRouter, Depends, HTTPException, Request

from services.common.models import DependencyList, ServiceInfo
from services.common.utils import apply_simulated_latency, utc_now_iso
from services.payment_service.app import store
from services.payment_service.app.config import Settings, get_settings
from services.payment_service.app.models import (
    HealthResponse,
    Payment,
    PaymentRequest,
)

router = APIRouter(tags=["payment"])


@router.get("/health", response_model=HealthResponse, summary="Payment-service health check")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Report the payment-service status and identification (UTC timestamp)."""
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
            "/api/v1/payments",
        ],
    )


@router.get(
    "/api/v1/dependencies",
    response_model=DependencyList,
    summary="Service dependencies",
)
def dependencies(settings: Settings = Depends(get_settings)) -> DependencyList:
    """Return the downstream dependencies of the payment-service (none yet)."""
    return DependencyList(service=settings.service_name, dependencies=[])


@router.post("/api/v1/payments", response_model=Payment, summary="Process a payment")
def create_payment(
    payload: PaymentRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Payment:
    """Simulate payment processing and record the payment (no real provider)."""
    metrics = request.app.state.payment_metrics
    metrics.payments_total.inc()
    started = time.perf_counter()
    apply_simulated_latency(settings.simulated_latency_ms)
    payment = store.process_payment(payload)
    metrics.payment_processing_duration_seconds.observe(time.perf_counter() - started)
    metrics.payments_success_total.inc()
    return payment


@router.get(
    "/api/v1/payments/{payment_id}",
    response_model=Payment,
    summary="Get a payment by ID",
)
def get_payment(payment_id: str) -> Payment:
    """Return a recorded payment, or 404 when the ID is unknown."""
    payment = store.get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found")
    return payment