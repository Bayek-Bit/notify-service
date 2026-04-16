import uuid
from typing import Sequence, Annotated

from fastapi import APIRouter, status
from fastapi.params import Depends

from src.api.v1.auth.dependencies import verify_service_token
from src.api.v1.notifications.dependencies import get_notification_service
from src.api.v1.notifications.logging_service import logger
from src.api.v1.notifications.schemas import (
    NotificationMarkAsRead,
    NotificationCreate,
    NotificationResponse,
)
from src.api.v1.notifications.service import NotificationService

router = APIRouter(
    prefix="/notifications", dependencies=[Depends(verify_service_token)]
)

NotificationServiceDep = Annotated[
    NotificationService, Depends(get_notification_service)
]


@router.post("/create_notification", status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationCreate,
    service: NotificationServiceDep,
) -> NotificationResponse:
    logger.info(
        "Создание уведомления для пользователя", recipient_id=notification.recipient_id
    )
    return await service.create_notification(notification)


@router.get("/get_notification/{notification_id}")
async def get_notification_by_id(
    notification_id: uuid.UUID,
    service: NotificationServiceDep,
) -> NotificationResponse:
    logger.info("Запрос уведомления по ID", notification_id=notification_id)
    return await service.get_notification_by_id(notification_id)


@router.get("/get_user_notifications/{user_id}")
async def get_user_notifications(
    user_id: uuid.UUID,
    service: NotificationServiceDep,
) -> Sequence[str]:
    logger.info("Запрос уведомлений пользователя", user_id=user_id)
    return await service.get_user_notifications(user_id)


@router.patch("/mark_notification_as_read/{notification_id}")
async def mark_notification_as_read(
    notification_id: uuid.UUID,
    service: NotificationServiceDep,
) -> NotificationResponse:
    # Оставляю схему для будущего расширения - добавления тела запроса с доп. полями (read_at, ...)
    logger.info(
        "Изменение статуса сообщения на 'прочитано'", notification_id=notification_id
    )
    mark_as_read_data = NotificationMarkAsRead(notification_id=notification_id)
    return await service.mark_notification_as_read(mark_as_read_data)


@router.delete(
    "/delete_notification/{notification_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_notification(
    notification_id: uuid.UUID,
    service: NotificationServiceDep,
) -> None:
    logger.info("Удаление сообщения", notification_id=notification_id)
    await service.delete_notification(notification_id)
