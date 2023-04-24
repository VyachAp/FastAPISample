import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List, Optional, Type

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from opentelemetry import context, trace
from sqlalchemy.ext.asyncio.engine import AsyncConnection

from svc.infrastructure.kafka.kafka_instrumentation import kafka_trace_formatter
from svc.infrastructure.kafka.message import Message
from svc.persist.database import Database

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def deserializer(serialized: bytes) -> dict:
    return json.loads(serialized)


@dataclass
class TopicInfo:
    message_cls: Type[Message]
    handler: Callable[[Message, AsyncConnection], Coroutine[Any, Any, None]]


class KafkaConsumer:
    def __init__(
        self,
        topics: List[str],
        bootstrap: str,
        group_id: str,
        database: Database,
        before_handler_hook: Optional[Callable[[trace.Span, Any], None]] = None,
    ) -> None:
        self._topics = topics
        self._bootstrap = bootstrap
        self._group_id = group_id
        self._client: Optional[AIOKafkaConsumer] = None
        self._handlers_registry: Dict[str, TopicInfo] = {}
        self._database = database
        self._before_handler_hook = before_handler_hook

    def register_topic_handler(self, topic: str, topic_info: TopicInfo) -> None:
        self._handlers_registry[topic] = topic_info

    async def start(self) -> None:
        logger.info(f"Starting Kafka consumer group {self._group_id}, topics: {self._topics}")
        self._client = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._bootstrap,
            group_id=self._group_id,
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
            auto_offset_reset="earliest",
            value_deserializer=deserializer,
        )
        asyncio.create_task(self._loop())

    async def _loop(self) -> None:
        if self._client is None:
            raise RuntimeError("uninitialized kafka producer!")

        await self._client.start()
        msg: ConsumerRecord
        async for msg in self._client:
            trace_context = kafka_trace_formatter.extract(msg.headers)
            token = context.attach(trace_context)
            try:
                with tracer.start_as_current_span(f"kafka topic {msg.topic}", kind=trace.SpanKind.CONSUMER) as span:
                    if self._before_handler_hook is not None:
                        self._before_handler_hook(span, {})

                    topic_info = self._handlers_registry[msg.topic]
                    message = topic_info.message_cls.parse_obj(msg.value)

                    # We need DI container here
                    async with self._database.engine.connect() as connection:
                        await topic_info.handler(message, connection)
            except KeyError:
                logger.exception(f"No handler for topic '{msg.topic}' registered")
            except Exception:
                logger.exception(f"Unhandled exception while processing message: {msg.value}")
            finally:
                context.detach(token)

    async def stop(self) -> None:
        logger.info("Stop Kafka consumer")
        if self._client is None:
            raise RuntimeError("uninitialized kafka producer!")

        await self._client.stop()
