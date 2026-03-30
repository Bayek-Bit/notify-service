import uuid
from datetime import datetime, timezone
from typing import List

from src.api.v1.notifications.exceptions import (
    UserNotFoundError,
    NotificationNotFoundError,
)
from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
    NotificationMarkAsRead,
)
from src.api.v1.notifications.repository import NotificationRepository


class NotificationService:
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    async def send_notification(
        self, notification: NotificationCreate
    ) -> NotificationResponse:
        user = await self.repo.get_user_by_id(notification.recipient_id)
        if user is None:
            raise UserNotFoundError(user_id=notification.recipient_id)

        return NotificationResponse(
            id=uuid.uuid4(),
            recipient_id=notification.recipient_id,
            title=notification.title,
            body=notification.body,
            status=NotificationStatus.PENDING,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )

    async def get_user_notifications(
        self, user_id: uuid.UUID
    ) -> List[NotificationResponse]:
        return await self.repo.get_user_notifications(user_id) or []

    async def _get_notification_or_raise(
        self, notification_id: uuid.UUID
    ) -> Notification:
        notification = await self.repo.get_notification_by_id(notification_id)
        if notification is None:
            raise NotificationNotFoundError(notification_id)
        return notification

    async def mark_notification_as_read(
        self, notification_to_read: NotificationMarkAsRead
    ) -> NotificationResponse:

        notification = await self._get_notification_or_raise(
            notification_to_read.notification_id
        )

        await self.repo.mark_notification_as_read(notification)

        notification.status = NotificationStatus.SENT
        return NotificationResponse.model_validate(notification)
