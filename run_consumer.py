import asyncio

from src.api.v1.notifications.push_service import send_push_notification
from src.database import session_factory
from src.api.v1.notifications.queue_consumer import notification_consumer
from src.api.v1.notifications.repository import NotificationRepository
from src.api.v1.notifications.schemas import NotificationTask, NotificationStatus
from src.api.v1.notifications.redis_pubsub import redis_manager
from src.api.v1.notifications.logging_service import logger


# 2. Логика обработки конкретного типа задачи ("message")
async def handle_notification_event(task: NotificationTask) -> bool:
    """
    Основной обработчик: БД -> Push -> Redis
    """
    try:
        async with session_factory() as session:
            repo = NotificationRepository(session)

            # Меняем статус на PROCESSING
            await repo.update_status(task.id, NotificationStatus.PROCESSING)

            # Отправляем "пуш"
            push_sent = await send_push_notification(task)

            if push_sent:
                # Статус SENT в БД
                await repo.update_status(task.id, NotificationStatus.SENT)

                # Публикация в Redis Pub/Sub для других инстансов
                channel = f"notifications:{task.recipient_id}"
                await redis_manager.publish(channel, task.model_dump())

                return True

            # Если пуш не ушел
            await repo.update_status(task.id, NotificationStatus.FAILED)
            return False

    except Exception as e:
        logger.error(f"Ошибка в обработчике уведомления {task.id}: {e}")
        return False


async def main():
    # Регистрируем обработчик для task_type="message"
    # (именно этот тип отправляет твой NotificationService)
    notification_consumer.register_handler("message", handle_notification_event)

    logger.info("Консьюмер инициализирован. Ожидание задач...")

    try:
        await notification_consumer.start()
    except KeyboardInterrupt:
        await notification_consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
