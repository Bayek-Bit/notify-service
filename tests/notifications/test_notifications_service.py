import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

import pytest

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
from src.api.v1.notifications.service import NotificationService


@pytest.fixture
def sample_notification_data() -> dict:
    """Фикстура с данными для уведомления (без id, тк он генерируется)."""
    return {
        "recipient_id": uuid.uuid4(),
        "title": "Test Notification",
        "body": "Текст уведомления",
    }


@pytest.fixture
def notification_sample() -> dict:
    notification_id = uuid.uuid4()
    recipient_id = uuid.uuid4()

    return {
        "id": notification_id,
        "recipient_id": recipient_id,
        "title": "Test",
        "body": "Test body",
        "status": NotificationStatus.DELIVERED,
        "is_read": False,
        # "read_at": None,
        "created_at": datetime.now(timezone.utc),
        "deleted_at": None,
    }


@pytest.fixture
def mock_repository() -> MagicMock:
    """Мокированный репозиторий."""
    repo = MagicMock()
    repo.create_notification = AsyncMock()
    repo.get_user_by_id = AsyncMock()
    repo.get_user_notifications = AsyncMock()
    repo.get_notification_by_id = AsyncMock()
    repo.mark_notification_as_read = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_create_notification(
    sample_notification_data: dict,
    notification_full: Notification,
    notification_service_override,
):
    """Тест: создание уведомления"""
    mock_repo, mock_queue = notification_service_override

    mock_repo.create_notification.return_value = notification_full

    notification_service = NotificationService(mock_repo, mock_queue)
    result = await notification_service.create_notification(
        NotificationCreate(**sample_notification_data)
    )

    assert isinstance(result, NotificationResponse)
    assert result.id == notification_full.id


@pytest.mark.asyncio
async def test_send_notification_success(
    sample_notification_data: dict,
    notification_service_override,
) -> None:
    """Тест успешного отправления уведомления"""
    mock_repo, mock_queue = notification_service_override

    recipient_id = sample_notification_data["recipient_id"]

    # Нашли пользователя в БД
    mock_repo.get_user_by_id.return_value = {"user_id": recipient_id}

    # Успешно отправили сообщение
    mock_queue.send_notification_task.return_value = True

    notification_service = NotificationService(mock_repo, mock_queue)

    result = await notification_service._send_notification(
        notification=NotificationCreate(**sample_notification_data)
    )

    assert result is True

    mock_queue.send_notification_task.assert_awaited_once()

    # Требуется сервис пользователей.
    # mock_repo.get_user_by_id.assert_awaited_once_with(user_id=recipient_id)


# Если добавлять интеграцию с сервисом пользователей - раскомментить тест.
# @pytest.mark.asyncio
# async def test_send_notification_user_not_found(
#     sample_notification_data: dict, notification_service_override
# ) -> None:
#     """Тест ошибки при попытке отправить уведомление несуществующему пользователю"""
#     mock_repo, mock_queue = notification_service_override
#
#     # Случай, когда пользователь не найден в БД
#     mock_repo.get_user_by_id.return_value = None
#
#     notification_service = NotificationService(mock_repo, mock_queue)
#
#     with pytest.raises(UserNotFoundError) as exc_info:
#         # Использует мок репозитория
#         await notification_service._send_notification(
#             notification=NotificationCreate(**sample_notification_data)
#         )
#     assert exc_info.value.user_id == sample_notification_data["recipient_id"]


@pytest.mark.asyncio
async def test_get_user_notifications_empty(
    sample_notification_data: dict,
    notification_service_override,
) -> None:
    """Тест на получение пустого списка, если у пользователя нет уведомлений"""
    mock_repo, mock_queue = notification_service_override

    mock_repo.get_user_notifications.return_value = []

    notification_service = NotificationService(mock_repo, mock_queue)

    user_notifications = await notification_service.get_user_notifications(
        sample_notification_data["recipient_id"]
    )

    assert user_notifications == []

    mock_repo.get_user_notifications.assert_called_once_with(
        sample_notification_data["recipient_id"]
    )


@pytest.mark.asyncio
async def test_mark_notification_as_read(
    notification_sample: dict,
    notification_service_override,
) -> None:
    """Тест is_read флага при прочтении уведомления пользователем."""
    mock_repo, mock_queue = notification_service_override

    mock_notification = Notification(
        id=notification_sample["id"],
        recipient_id=notification_sample["recipient_id"],
        title=notification_sample["title"],
        body=notification_sample["body"],
        is_read=False,  # Изначально не прочитано
        deleted_at=notification_sample["deleted_at"],
        created_at=notification_sample["created_at"],
    )

    mock_repo.get_notification_by_id.return_value = mock_notification

    # Мокаем mark_notification_as_read так, чтобы он менял объект
    async def mock_mark_as_read(notification: Notification):
        notification.is_read = True

    mock_repo.mark_notification_as_read = AsyncMock(side_effect=mock_mark_as_read)

    notification_service = NotificationService(mock_repo, mock_queue)

    result = await notification_service.mark_notification_as_read(
        NotificationMarkAsRead(notification_id=notification_sample["id"])
    )

    assert isinstance(result, NotificationResponse)
    assert result.id == notification_sample["id"]
    assert result.is_read is True


@pytest.mark.asyncio
async def test_mark_as_read_notification_not_found(
    notification_sample: dict,
    notification_service_override,
) -> None:
    """Тест ошибки в случае не найденного сообщения при попытке изменить статус is_read."""
    mock_repo, mock_queue = notification_service_override

    mock_repo.get_notification_by_id.return_value = None

    notification_service = NotificationService(mock_repo, mock_queue)

    with pytest.raises(NotificationNotFoundError):
        await notification_service.mark_notification_as_read(
            NotificationMarkAsRead(notification_id=notification_sample["id"])
        )
