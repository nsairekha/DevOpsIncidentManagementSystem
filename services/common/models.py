"""Shared response models for service info, dependencies, and errors."""

from pydantic import BaseModel


class ServiceInfo(BaseModel):
    """Basic service identification returned by ``GET /api/v1/``."""

    service: str
    version: str
    environment: str
    timestamp: str
    endpoints: list[str]


class Dependency(BaseModel):
    """One downstream dependency of a service."""

    service: str
    url: str
    type: str = "http"


class DependencyList(BaseModel):
    """Dependency topology fragment returned by ``GET /api/v1/dependencies``."""

    service: str
    dependencies: list[Dependency]


class ErrorResponse(BaseModel):
    """Structured error body for dependency failures."""

    error: str
    service: str
    request_id: str | None = None
    timestamp: str