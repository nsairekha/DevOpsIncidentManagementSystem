"""HTTP clients for the order-service's downstream dependencies.

The order-service never imports other services' Python code; it talks to
them exclusively through these HTTP clients, which forward the in-flight
``X-Request-ID`` for distributed trace continuity.
"""

import httpx

from services.common.http import DownstreamError, post_json
from services.common.logging import get_request_id


class PaymentClient:
    """HTTP client for the payment-service."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.client = client

    def process_payment(
        self, order_id: int, user_id: int, amount: float
    ) -> dict:
        """Charge the order; raises :class:`DownstreamError` on failure."""
        return post_json(
            "payment-service",
            f"{self.base_url}/api/v1/payments",
            {"order_id": order_id, "user_id": user_id, "amount": amount},
            timeout_seconds=self.timeout_seconds,
            request_id=get_request_id(),
            client=self.client,
        )


class NotificationClient:
    """HTTP client for the notification-service."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.client = client

    def send_notification(self, user_id: int, message: str, type: str) -> dict:
        """Send a notification; raises :class:`DownstreamError` on failure."""
        return post_json(
            "notification-service",
            f"{self.base_url}/api/v1/notifications",
            {"user_id": user_id, "message": message, "type": type},
            timeout_seconds=self.timeout_seconds,
            request_id=get_request_id(),
            client=self.client,
        )


__all__ = ["DownstreamError", "NotificationClient", "PaymentClient"]