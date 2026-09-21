"""In-memory payment store (simulated processing only)."""

import uuid

from services.common.utils import utc_now_iso
from services.payment_service.app.models import Payment, PaymentRequest

_payments: dict[str, Payment] = {}


def process_payment(request: PaymentRequest) -> Payment:
    """Simulate a payment and record it, always succeeding in this step."""
    payment = Payment(
        payment_id=uuid.uuid4().hex,
        order_id=request.order_id,
        user_id=request.user_id,
        status="success",
        amount=request.amount,
        timestamp=utc_now_iso(),
    )
    _payments[payment.payment_id] = payment
    return payment


def get_payment(payment_id: str) -> Payment | None:
    """Return a recorded payment, or None when unknown."""
    return _payments.get(payment_id)


def reset_store() -> None:
    """Clear all recorded payments (used by tests for isolation)."""
    _payments.clear()