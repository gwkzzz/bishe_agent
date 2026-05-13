from __future__ import annotations

import json
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, Message

from app.core.config import get_settings
from app.integrations.errors import QueuePublishError


class RabbitMQPublisher:
    def __init__(self, url: str | None = None) -> None:
        self.url = url or get_settings().rabbitmq_url
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None

    async def connect(self) -> None:
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self.url)
            self._channel = await self._connection.channel()

    async def declare_queue(self, queue_name: str, durable: bool = True) -> None:
        try:
            await self.connect()
            assert self._channel is not None
            await self._channel.declare_queue(queue_name, durable=durable)
        except Exception as exc:
            raise QueuePublishError(f"RabbitMQ queue declaration failed for {queue_name}") from exc

    async def publish_json(
        self,
        routing_key: str,
        payload: dict[str, Any],
        exchange_name: str = "",
    ) -> None:
        try:
            await self.connect()
            assert self._channel is not None
            body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            message = Message(
                body,
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
            )
            if exchange_name:
                exchange = await self._channel.get_exchange(exchange_name)
                await exchange.publish(message, routing_key=routing_key)
            else:
                await self._channel.default_exchange.publish(message, routing_key=routing_key)
        except Exception as exc:
            raise QueuePublishError(f"RabbitMQ publish failed for {routing_key}") from exc

    async def close(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        self._channel = None
        self._connection = None
