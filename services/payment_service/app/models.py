"""Payment domain models (simulated processing, no real provider)."""

from pydantic import BaseModel, Field


class PaymentRequest(BaseModel):
    """Incoming simulated-payment request."""

    order_id: int
    user_id: int
    amount: float = Field(gt=0)


class Payment(BaseModel):
    """A processed (simulated) payment record."""

    payment_id: str
    order_id: int
    user_id: int
    status: str
    amount: float
    timestamp: str


class HealthResponse(BaseModel):
    """Payload returned by the payment-service health endpoint."""

    status: str
    service: str
    version: str
    environment: str
    timestamp: str