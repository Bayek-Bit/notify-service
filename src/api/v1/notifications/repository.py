import logging
import uuid
from typing import Optional, List, Sequence

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

    async def mark_notification_as_read(self, notification: Notification) -> None:
        """Отмечает уведомление как прочитанное"""
        notification.is_read = True
        # notification.read_at = datetime.now(timezone.utc)  # Можно добавить позже
        await self.session.commit()
        await self.session.refresh(notification)

    async def get_user_notifications(self, user_id: uuid.UUID) -> Sequence[str]:
        """Получает только заголовки всех уведомления пользователя."""
        result = await self.session.execute(
            select(Notification.title)
            .where(Notification.recipient_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()
