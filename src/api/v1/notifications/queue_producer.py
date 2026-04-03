from typing import Protocol

import aio_pika
import json

from src.api.v1.notifications.logging_service import logger
from src.api.v1.notifications.schemas import NotificationCreate


class QueueProducerProtocol(Protocol):
    async def send_notification_task(
        self, notification: NotificationCreate, task_type: str
    ) -> bool: ...


class QueueProducer(QueueProducerProtocol):
    def __init__(self, host: str = "localhost"):
        self.host = host
        self.connection = None
        self.channel = None
        self.queue_name = "notification_processing"

    async def connect(self):
        """Подключение к RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                f"amqp://guest:guest@{self.host}/"
            )
            self.channel = await self.connection.channel()
            await self.channel.declare_queue("notification_processing", durable=True)
            logger.info("Producer подключен")
            return True
        except Exception as e:
            logger.error("Ошибка подключения: %s", e)
            return False

    async def send_notification_task(
        self,
        notification: NotificationCreate,
        task_type: str,
    ):
        if not self.channel or not self.connection:
            if not await self.connect():
                return False
        try:
            message = {"task_type": task_type, **notification}

            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=self.queue_name,
            )
            logger.info("Задача отправлена в очередь: %s", message)
            return True

        except Exception as ex:
            logger.warning("Ошибка при отправки уведомления в очередь: %s", ex)
            return False

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()


queue_producer = QueueProducer()
