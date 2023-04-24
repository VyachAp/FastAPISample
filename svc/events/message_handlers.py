from sqlalchemy.ext.asyncio import AsyncConnection

from svc.events.initiate import create_coupon_service
from svc.events.messages import OrderCanceledMessage, OrderPaidMessage


async def handle_order_canceled(message: OrderCanceledMessage, connection: AsyncConnection) -> None:
    coupon_service = create_coupon_service(connection)
    await coupon_service.process_cancelled(order_id=message.order_id)


async def handle_order_paid(message: OrderPaidMessage, connection: AsyncConnection) -> None:
    coupon_service = create_coupon_service(connection)
    await coupon_service.process_paid(order_id=message.order_id)
