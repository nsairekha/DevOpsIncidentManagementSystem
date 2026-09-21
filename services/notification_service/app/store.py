"""In-memory notification store (simulated delivery only)."""

import uuid

from services.common.utils import utc_now_iso
from services.notification_service.app.models import (
    Notification,
    NotificationRequest,
)

_notifications: dict[str, Notification] = {}


def send_notification(request: NotificationRequest) -> Notification:
    """Simulate delivery and record the notification as sent."""
    notification = Notification(
        notification_id=uuid.uuid4().hex,
        user_id=request.user_id,
        message=request.message,
        type=request.type,
        status="sent",
        timestamp=utc_now_iso(),
    )
    _notifications[notification.notification_id] = notification
    return notification


def reset_store() -> None:
    """Clear all recorded notifications (used by tests for isolation)."""
    _notifications.clear()