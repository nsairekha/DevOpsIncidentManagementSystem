"""User retrieval endpoints (in-memory store, no database yet)."""

from fastapi import APIRouter, HTTPException, Request

from services.user_service.app.models.user import User
from services.user_service.app.services import user_service

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.get("/users/{user_id}", response_model=User, summary="Get a user by ID")
def get_user(user_id: int, request: Request) -> User:
    """Return a single demo user, or 404 when the ID is unknown."""
    metrics = request.app.state.user_metrics
    metrics.user_requests_total.inc()
    user = user_service.get_user(user_id)
    if user is None:
        metrics.user_lookup_errors_total.inc()
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user