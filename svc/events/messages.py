from uuid import UUID

from svc.infrastructure.kafka.message import Message


class OrderCanceledMessage(Message):
    event = "customer-order-canceled"
    order_id: UUID


class OrderPaidMessage(Message):
    event = "customer-order-paid"
    order_id: UUID
