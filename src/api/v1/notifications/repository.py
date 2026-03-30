import logging
import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.notifications.models import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_notification_by_id(
        self, notification_id: uuid.UUID
    ) -> Optional[Notification]:
        """Получает уведомление по ID."""
        stmt = select(Notification).where(Notification.id == notification_id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def mark_notification_as_read(self, notifcation_id: uuid.UUID) -> bool:
        """Отмечает уведомление как прочитанное"""
        notification = await self.get_notification_by_id(notifcation_id)
        if notification is None:
            return False

        notification.is_read = True
        # notification.read_at = datetime.now(timezone.utc)  # Можно добавить позже

        await self.session.commit()
        return True

    async def get_user_notifications(self, user_id: uuid.UUID) -> List[Notification]:
        """Получает только заголовки всех уведомления пользователя."""
        result = await self.session.execute(
            select(Notification.title)
            .where(Notification.recipient_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()
