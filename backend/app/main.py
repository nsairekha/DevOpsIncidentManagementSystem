"""Backend application entrypoint.

Run locally with:

    uvicorn backend.app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CollectorRegistry

from backend.app.api.routes.analyze import router as analyze_router
from backend.app.api.routes.audit import router as audit_router
from backend.app.api.routes.cloudwatch import router as cloudwatch_router
from backend.app.api.routes.health import legacy_router, router as health_router
from backend.app.api.routes.metrics import router as metrics_router
from backend.app.config import settings
from backend.app.exceptions import configure_exception_handlers
from backend.app.monitoring.setup import setup_metrics
from backend.app.utils.logging import RequestContextMiddleware, setup_logging
from blockchain import AuditLedger
from monitoring.baseline.service import BaselineService


def create_app(registry: CollectorRegistry | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        registry: Optional Prometheus registry; defaults to the process-wide
            singleton. Tests pass a fresh registry for isolation.
    """
    setup_logging(service=settings.service_name)

    app = FastAPI(
        title="AI Cloud Observability",
        version=settings.app_version,
        description="AI-Based Cloud Observability System - backend API",
    )

    # Application-wide audit ledger (append-only chained blocks).
    app.state.ledger = AuditLedger()

    # Shared baseline service for the metric pipeline endpoints.
    app.state.baseline_service = BaselineService()

    # Structured JSON request logging with per-request IDs.
    app.add_middleware(RequestContextMiddleware, service=settings.service_name)

    # Allow the Next.js dashboard (and local tooling) to call the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    configure_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(legacy_router)
    app.include_router(metrics_router)
    app.include_router(cloudwatch_router)
    app.include_router(analyze_router)
    app.include_router(audit_router)
    setup_metrics(app, registry=registry)

    return app


app = create_app()