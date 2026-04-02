import uuid

from fastapi import APIRouter, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.auth.dependencies import verify_service_token
from src.api.v1.notifications.dependencies import get_notification_service
from src.api.v1.notifications.repository import NotificationRepository
from src.api.v1.notifications.schemas import NotificationMarkAsRead, NotificationCreate
from src.api.v1.notifications.service import NotificationService
from src.database import get_db_session

router = APIRouter(
    prefix="/notifications", dependencies=[Depends(verify_service_token)]
)


@router.post("/create_notification", status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationCreate,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.create_notification(notification)


@router.get("/get_notification/{notification_id}")
async def get_notification_by_id(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.get_notification_by_id(notification_id)


@router.get("/get_user_notifications/{user_id}")
async def get_user_notifications(
    user_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.get_user_notifications(user_id)


@router.patch("/mark_notification_as_read/{notification_id}")
async def mark_notification_as_read(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
):
    # Оставляю схему для будущего расширения - добавления тела запроса с доп. полями (read_at, ...)
    mark_as_read_data = NotificationMarkAsRead(notification_id=notification_id)
    return await service.mark_notification_as_read(mark_as_read_data)
