"""Notification domain models (simulated delivery, no email/SMS provider)."""

from pydantic import BaseModel, Field


class NotificationRequest(BaseModel):
    """Incoming simulated-delivery request."""

    user_id: int
    message: str = Field(min_length=1)
    type: str = Field(min_length=1)


class Notification(BaseModel):
    """A recorded (simulated as sent) notification."""

    notification_id: str
    user_id: int
    message: str
    type: str
    status: str
    timestamp: str


class HealthResponse(BaseModel):
    """Payload returned by the notification-service health endpoint."""

    status: str
    service: str
    version: str
    environment: str
    timestamp: str