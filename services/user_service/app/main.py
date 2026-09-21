"""User-service application entrypoint.

Run locally with (from the repository root):

    uvicorn services.user_service.app.main:app --reload --port 8001

The service is independent from the main backend and needs no shared code.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CollectorRegistry
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from services.common.logging import RequestContextMiddleware, setup_logging
from services.common.metrics import (
    CONTENT_TYPE_LATEST,
    create_service_metrics,
    create_user_metrics,
    render_metrics,
)
from services.common.middleware import MetricsMiddleware
from services.user_service.app.api.routes.health import router as health_router
from services.user_service.app.api.routes.info import router as info_router
from services.user_service.app.api.routes.users import router as users_router
from services.user_service.app.config import settings
from services.user_service.app.request_logging import (
    RequestContextMiddleware as RequestIDMiddleware,
    setup_logging as setup_request_logging,
)


def create_app(registry: CollectorRegistry | None = None) -> FastAPI:
    """Build and configure the user-service application.

    Args:
        registry: Optional Prometheus registry; a fresh one is created when
            omitted. Tests pass an isolated registry per test.
    """
    setup_request_logging(service=settings.service_name)

    metrics_registry = registry or CollectorRegistry()
    http_metrics = create_service_metrics(settings.service_name, metrics_registry)
    user_metrics = create_user_metrics(metrics_registry)

    app = FastAPI(
        title="AI Cloud Observability - User Service",
        version=settings.service_version,
        description="User microservice for the AI-Based Cloud Observability System",
    )
    app.state.metrics_registry = metrics_registry
    app.state.user_metrics = user_metrics

    app.add_middleware(MetricsMiddleware, metrics=http_metrics)
    app.add_middleware(RequestIDMiddleware, service=settings.service_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc: StarletteHTTPException) -> JSONResponse:
        """Return HTTP errors as JSON with a ``detail`` field."""
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError) -> JSONResponse:
        """Return validation errors as JSON with a ``detail`` field."""
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    app.include_router(health_router)
    app.include_router(info_router)
    app.include_router(users_router)

    @app.get("/metrics", include_in_schema=False)
    def metrics_endpoint() -> Response:
        """Expose Prometheus metrics in the text exposition format."""
        return Response(
            content=render_metrics(metrics_registry),
            media_type=CONTENT_TYPE_LATEST,
        )

    return app


app = create_app()