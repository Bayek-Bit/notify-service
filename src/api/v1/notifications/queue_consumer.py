# src/api/v1/notifications/consumer.py
from typing import Callable, Awaitable, Dict
import asyncio
import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractQueue

from src.api.v1.notifications.logging_service import logger
from src.api.v1.notifications.redis_pubsub import redis_manager
from src.api.v1.notifications.schemas import NotificationTask

# Тип обработчика для каждого task_type
HandlerType = Callable[[NotificationTask], Awaitable[bool]]


class NotificationConsumer:
    def __init__(
        self,
        host: str = "localhost",
        queue_name: str = "notification_processing",
        prefetch_count: int = 5,
    ):
        self.host = host
        self.queue_name = queue_name
        self.prefetch_count = prefetch_count
        self.connection: aio_pika.abc.AbstractRobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None
        self.queue: AbstractQueue | None = None
        self._handlers: Dict[str, HandlerType] = {}
        self._running = False

    async def connect(self) -> bool:
        """Подключение и настройка очереди, exchange, DLQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                f"amqp://guest:guest@{self.host}/"
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.prefetch_count)

            # Объявляем основной exchange и очередь
            exchange = await self.channel.declare_exchange(
                "notifications.exchange",
                type=aio_pika.ExchangeType.DIRECT,
                durable=True,
            )
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "notifications.dlx",
                    "x-dead-letter-routing-key": "notification.failed",
                },
            )
            await self.queue.bind(exchange, routing_key=self.queue_name)

            # DLQ exchange + queue
            dlx = await self.channel.declare_exchange(
                "notifications.dlx",
                type=aio_pika.ExchangeType.DIRECT,
                durable=True,
            )
            dlq = await self.channel.declare_queue(
                "notification_failed",
                durable=True,
            )
            await dlq.bind(dlx, routing_key="notification.failed")

            logger.info("Consumer подключен, очередь: %s", self.queue_name)
            return True
        except Exception as e:
            logger.error("Ошибка подключения consumer: %s", e)
            return False

    def register_handler(self, task_type: str, handler: HandlerType):
        """Регистрация обработчика для конкретного типа уведомления"""
        self._handlers[task_type] = handler
        logger.info("Зарегистрирован обработчик для task_type: %s", task_type)

    async def _process_message(self, message: AbstractIncomingMessage):
        async with message.process(requeue=False):
            try:
                body = json.loads(message.body.decode())
                task_type = body.pop("task_type", None)
                notification = NotificationTask(**body)

                handler = self._handlers.get(task_type)
                if not handler:
                    logger.warning(
                        f"Нет обработчика для task_type='{task_type}', сообщение отклонено"
                    )
                    await message.nack(
                        requeue=False
                    )  # В DLQ, т.к. неизвестный тип задачи
                    return

                success = await handler(notification)

                if success:
                    # Публикация в Redis для real-time связки бэкенд-бэкенд
                    channel = f"notifications:{notification.recipient_id}"
                    await redis_manager.publish(channel, notification.model_dump())
                    logger.info(
                        f"Задача {notification.id} (type={task_type}) успешно обработана"
                    )
                else:
                    logger.error(
                        f"Обработчик вернул failure для задачи {notification.id}"
                    )
                    await message.nack(requeue=True)  # Повтор при временной ошибке

            except Exception as e:
                logger.critical(f"Critical error in consumer: {e}")
                await message.nack(requeue=False)  # В DLQ при критической ошибке

    async def start(self):
        """Запуск потребления сообщений"""
        if not self.connection or not self.queue:
            if not await self.connect():
                return
        self._running = True
        logger.info("Consumer запущен, слушаем очередь...")
        await self.queue.consume(self._process_message)
        # Держим цикл, пока не остановят
        while self._running:
            await asyncio.sleep(1)

    async def stop(self):
        """Корректная остановка"""
        self._running = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Consumer остановлен")


# Глобальный инстанс
notification_consumer = NotificationConsumer()
