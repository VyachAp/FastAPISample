from svc.events.message_handlers import handle_order_canceled, handle_order_paid
from svc.events.messages import OrderCanceledMessage, OrderPaidMessage
from svc.infrastructure.kafka.consumer import KafkaConsumer, TopicInfo
from svc.infrastructure.traces import set_trace_context_var
from svc.persist.database import Database
from svc.settings import Settings


def create_consumer(settings: Settings, database: Database) -> KafkaConsumer:
    topics = [
        ("customer.order.canceled", OrderCanceledMessage, handle_order_canceled),
        ("customer.order.paid", OrderPaidMessage, handle_order_paid),
    ]
    consumer = KafkaConsumer(
        [t for t, *_ in topics],
        settings.kafka.bootstrap,
        settings.kafka.group_id,
        database,
        set_trace_context_var,
    )

    for topic, message_cls, handler in topics:
        consumer.register_topic_handler(
            topic, TopicInfo(message_cls=message_cls, handler=handler)  # type:ignore[arg-type]
        )

    return consumer
