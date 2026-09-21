"""Order-service API routes.

Orchestrates the distributed flow ``order → payment → notification`` over
HTTP (never via Python imports). Dependency failures are logged with the
trace's request ID and surfaced as structured errors without crashing.
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Request

from services.common.http import DownstreamError
from services.common.logging import RequestLogger, get_request_id
from services.common.metrics import track_dependency
from services.common.models import (
    Dependency,
    DependencyList,
    ErrorResponse,
    ServiceInfo,
)
from services.common.utils import apply_simulated_latency, utc_now_iso
from services.order_service.app import store
from services.order_service.app.clients import (
    NotificationClient,
    PaymentClient,
)
from services.order_service.app.config import Settings, get_settings
from services.order_service.app.models import (
    HealthResponse,
    Order,
    OrderRequest,
)

router = APIRouter(tags=["order"])


def build_payment_client(settings: Settings) -> PaymentClient:
    """Build the payment-service HTTP client from configuration."""
    return PaymentClient(settings.payment_service_url, settings.request_timeout_seconds)


def build_notification_client(settings: Settings) -> NotificationClient:
    """Build the notification-service HTTP client from configuration."""
    return NotificationClient(
        settings.notification_service_url, settings.request_timeout_seconds
    )


@router.get("/health", response_model=HealthResponse, summary="Order-service health check")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Report the order-service status and identification (UTC timestamp)."""
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
            "/api/v1/orders",
        ],
    )


@router.get(
    "/api/v1/dependencies",
    response_model=DependencyList,
    summary="Service dependencies",
)
def dependencies(settings: Settings = Depends(get_settings)) -> DependencyList:
    """Return the downstream HTTP dependencies of the order-service."""
    return DependencyList(
        service=settings.service_name,
        dependencies=[
            Dependency(service="payment-service", url=settings.payment_service_url),
            Dependency(
                service="notification-service",
                url=settings.notification_service_url,
            ),
        ],
    )


def _dependency_error(
    *, error: str, service: str, status_code: int
) -> HTTPException:
    """Build a structured dependency-failure response (never crash)."""
    request_id = get_request_id()
    body = ErrorResponse(
        error=error,
        service=service,
        request_id=request_id,
        timestamp=utc_now_iso(),
    ).model_dump()
    return HTTPException(status_code=status_code, detail=body)


@router.post(
    "/api/v1/orders",
    response_model=Order,
    status_code=201,
    summary="Create an order (charges payment, sends notification)",
)
def create_order(
    payload: OrderRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Order:
    """Create an order, charge it via payment-service, notify via notification-service.

    If payment-service is unreachable the order fails with 503. If only the
    notification-service fails, the payment stands and the order reports
    ``notification_status="failed"``.
    """
    metrics = request.app.state.order_metrics
    dependencies = request.app.state.dependency_metrics
    started = time.perf_counter()
    apply_simulated_latency(settings.simulated_latency_ms)
    order = store.create_order(payload)
    metrics.orders_created_total.inc()
    request_id = get_request_id()
    try:
        return _fulfill_order(
            order, payload, settings, metrics, dependencies, request_id
        )
    finally:
        metrics.order_processing_duration_seconds.observe(
            time.perf_counter() - started
        )


def _fulfill_order(
    order: Order,
    payload: OrderRequest,
    settings: Settings,
    metrics,
    dependencies,
    request_id: str | None,
) -> Order:
    """Charge the payment and send the notification for an order."""
    # 1-3. Charge through payment-service over HTTP.
    metrics.payment_dependency_requests_total.inc()
    try:
        with track_dependency(
            dependencies,
            settings.service_name,
            "payment-service",
            "/api/v1/payments",
        ):
            payment = build_payment_client(settings).process_payment(
                order.order_id, order.user_id, order.amount
            )
    except DownstreamError as exc:
        order.payment_status = "failed"
        store.update_order(order)
        metrics.orders_failed_total.inc()
        metrics.payment_dependency_errors_total.inc()
        RequestLogger.error(
            "dependency failure: %s",
            exc.detail,
            extra={"service": settings.service_name, "request_id": request_id},
        )
        if exc.kind in ("unavailable", "timeout"):
            raise _dependency_error(
                error="payment_service_unavailable",
                service=settings.service_name,
                status_code=503,
            ) from exc
        raise _dependency_error(
            error="payment_failed",
            service=settings.service_name,
            status_code=502,
        ) from exc

    if payment.get("status") != "success":
        order.payment_status = "failed"
        store.update_order(order)
        metrics.orders_failed_total.inc()
        metrics.payment_dependency_errors_total.inc()
        RequestLogger.error(
            "dependency failure: payment-service reported %s",
            payment.get("status"),
            extra={"service": settings.service_name, "request_id": request_id},
        )
        raise _dependency_error(
            error="payment_failed",
            service=settings.service_name,
            status_code=502,
        )

    order.payment_id = str(payment.get("payment_id"))
    order.payment_status = "success"

    # 4-5. Notify through notification-service over HTTP (best effort).
    metrics.notification_dependency_requests_total.inc()
    try:
        with track_dependency(
            dependencies,
            settings.service_name,
            "notification-service",
            "/api/v1/notifications",
        ):
            build_notification_client(settings).send_notification(
                order.user_id,
                f"Order {order.order_id} payment successful",
                "order_update",
            )
    except DownstreamError as exc:
        order.notification_status = "failed"
        store.update_order(order)
        metrics.notification_dependency_errors_total.inc()
        RequestLogger.error(
            "dependency failure: %s",
            exc.detail,
            extra={"service": settings.service_name, "request_id": request_id},
        )
        return order

    # 6. Everything succeeded.
    order.notification_status = "sent"
    return store.update_order(order)


@router.get(
    "/api/v1/orders/{order_id}",
    response_model=Order,
    summary="Get an order by ID",
)
def get_order(order_id: int) -> Order:
    """Return a recorded order, or 404 when the ID is unknown."""
    order = store.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order