from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.notifications.repository import NotificationRepository
from src.api.v1.notifications.service import NotificationService
from src.database import get_db_session


async def get_notification_service(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationService:
    repo = NotificationRepository(session)
    return NotificationService(repo)
