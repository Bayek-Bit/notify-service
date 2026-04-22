import asyncio
import uuid
from typing import Sequence

from src.api.v1.notifications.exceptions import (
    NotificationNotFoundError,
)
from src.api.v1.notifications.logging_service import logger
from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.queue_producer import (
    QueueProducerProtocol,
)
from src.api.v1.notifications.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
    NotificationMarkAsRead,
    NotificationTask,
)
from src.api.v1.notifications.repository import NotificationRepository


class NotificationService:
    def __init__(
        self, repo: NotificationRepository, queue_producer: QueueProducerProtocol
    ):
        self.repo = repo
        self.queue_producer = queue_producer

    async def create_notification(
        self, notification_data: NotificationCreate
    ) -> NotificationResponse:
        """Создает уведомление и ставит задачу в очередь (Fire & Forget)."""
        notification = await self.repo.create_notification(notification_data)

        task = NotificationTask(
            id=notification.id,
            recipient_id=notification.recipient_id,
            title=notification.title,
            body=notification.body,
        )

        # Запускаем в фоне с обёрткой для логирования ошибок
        asyncio.create_task(
            self._safe_send_task(task, "message"),
            name=f"notification-{notification.id}",  # Имя для отладки
        )

        return NotificationResponse.model_validate(notification)

    async def _safe_send_task(self, task: NotificationTask, task_type: str) -> None:
        """Обёртка для безопасного выполнения фоновой задачи."""
        try:
            success = await self.queue_producer.send_notification_task(task, task_type)
            if not success:
                logger.warning("Failed to queue notification task: %s", task.id)
        except asyncio.CancelledError:
            # Задача отменена при завершении приложения - это нормально
            logger.info("Task cancelled during shutdown: %s", task.id)
        except Exception as e:
            # Ловим всё, что не поймал producer
            logger.critical("Critical error in background task %s: %s", task.id, e)

    async def get_user_notifications(self, user_id: uuid.UUID) -> Sequence[str]:
        return await self.repo.get_user_notifications(user_id) or []

    async def _get_notification_or_raise(
        self, notification_id: uuid.UUID
    ) -> Notification:
        notification = await self.repo.get_notification_by_id(notification_id)
        if notification is None:
            raise NotificationNotFoundError(notification_id)
        return notification

    async def get_notification_by_id(
        self, notification_id: uuid.UUID
    ) -> NotificationResponse:
        """Получает уведомление по ID."""
        notification = await self._get_notification_or_raise(notification_id)
        return NotificationResponse.model_validate(notification)

    async def mark_notification_as_read(
        self, notification_to_read: NotificationMarkAsRead
    ) -> NotificationResponse:

        notification = await self._get_notification_or_raise(
            notification_to_read.notification_id
        )

        await self.repo.mark_notification_as_read(notification)

        notification.status = NotificationStatus.READ
        return NotificationResponse.model_validate(notification)

    async def delete_notification(self, notification_id: uuid.UUID):

        notification = await self._get_notification_or_raise(notification_id)

        await self.repo.delete_notification(notification.id)
