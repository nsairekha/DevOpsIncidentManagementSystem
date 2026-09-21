"""Order domain models (in-memory representation, no database yet)."""

from pydantic import BaseModel, Field


class OrderRequest(BaseModel):
    """Incoming order creation request."""

    user_id: int
    product: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    amount: float = Field(gt=0)


class Order(BaseModel):
    """A recorded order, enriched with downstream outcomes."""

    order_id: int
    user_id: int
    product: str
    quantity: int
    amount: float
    status: str
    payment_id: str | None = None
    payment_status: str = "pending"
    notification_status: str = "pending"
    timestamp: str


class HealthResponse(BaseModel):
    """Payload returned by the order-service health endpoint."""

    status: str
    service: str
    version: str
    environment: str
    timestamp: str