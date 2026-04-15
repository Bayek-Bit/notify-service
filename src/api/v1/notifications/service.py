import asyncio
import uuid
from typing import List

from src.api.v1.notifications.exceptions import (
    NotificationNotFoundError,
)
from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.queue_producer import (
    QueueProducerProtocol,
)
from src.api.v1.notifications.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
    NotificationMarkAsRead,
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
        """Создает уведомление."""
        notification = await self.repo.create_notification(notification_data)

        asyncio.create_task(self._send_notification(notification_data))

        return NotificationResponse.model_validate(notification)

    async def _send_notification(self, notification: NotificationCreate) -> bool:
        # На этом этапе мы доверяем отправителю, допуская, что notification.recipient_id относится к существующему пользователю.
        # Либо обращаться к UserService, который можно будет реализовать потом
        # user = await self.repo.get_user_by_id(notification.recipient_id)
        # if user is None:
        #     raise UserNotFoundError(user_id=notification.recipient_id)

        result = await self.queue_producer.send_notification_task(
            notification=notification,
            task_type="message",
        )
        return result

    async def get_user_notifications(self, user_id: uuid.UUID) -> List[str]:
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

        notification.status = NotificationStatus.SENT
        return NotificationResponse.model_validate(notification)

    async def delete_notification(self, notification_id: uuid.UUID):

        notification = await self._get_notification_or_raise(notification_id)

        await self.repo.delete_notification(notification.id)
