import uuid
from typing import Optional, Sequence

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.schemas import NotificationCreate, NotificationStatus


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(
        self, notification_data: NotificationCreate
    ) -> Notification:
        """Создает уведомление в БД."""
        notification = Notification(**notification_data.model_dump())

        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)

        return notification

    async def get_notification_by_id(
        self, notification_id: uuid.UUID
    ) -> Optional[Notification]:
        """Получает уведомление по ID."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.deleted_at.is_(None),
        )

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
            .where(
                Notification.recipient_id == user_id,
                Notification.deleted_at.is_(None),
            )
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()

    async def update_status(
        self, notification_id: uuid.UUID, status: NotificationStatus
    ) -> None:
        """Обновляет статус уведомления в базе данных."""
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(status=status, updated_at=func.now())
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_notification(self, notification_id: uuid.UUID) -> bool:
        """
        Soft delete уведомления.

        Returns:
            True — уведомление найдено и удалено
            False — уведомление не найдено
        """
        notification = await self.get_notification_by_id(notification_id)
        if notification is None:
            return False

        await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(deleted_at=func.now())
        )
        await self.session.commit()
        return True
