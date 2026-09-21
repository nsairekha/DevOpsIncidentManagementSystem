"""In-memory order store (no database yet)."""

from services.common.utils import utc_now_iso
from services.order_service.app.models import Order, OrderRequest

_START_ID = 1000

_orders: dict[int, Order] = {}
_next_id = _START_ID + 1


def create_order(request: OrderRequest) -> Order:
    """Record a new order with the next sequential ID (first is 1001)."""
    global _next_id
    order = Order(
        order_id=_next_id,
        user_id=request.user_id,
        product=request.product,
        quantity=request.quantity,
        amount=request.amount,
        status="created",
        timestamp=utc_now_iso(),
    )
    _orders[order.order_id] = order
    _next_id += 1
    return order


def get_order(order_id: int) -> Order | None:
    """Return a recorded order, or None when unknown."""
    return _orders.get(order_id)


def update_order(order: Order) -> Order:
    """Persist downstream outcomes (payment/notification) on an order."""
    _orders[order.order_id] = order
    return order


def reset_store() -> None:
    """Clear all orders and restart IDs (used by tests for isolation)."""
    global _next_id
    _orders.clear()
    _next_id = _START_ID + 1