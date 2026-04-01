import uuid

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.auth.dependencies import verify_service_token
from src.api.v1.notifications.dependencies import get_notification_service
from src.api.v1.notifications.repository import NotificationRepository
from src.api.v1.notifications.service import NotificationService
from src.database import get_db_session

router = APIRouter(
    prefix="/notifications", dependencies=[Depends(verify_service_token)]
)


@router.get("/get_notification/{notification_id}")
async def get_notification_by_id(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.get_notification_by_id(notification_id)
