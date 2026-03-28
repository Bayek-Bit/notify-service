# TODO: test_get_user_notifications_empty, test_get_user_notifications_paginated, test_mark_notification_as_read

import uuid
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

import pytest

from src.api.v1.notifications.exceptions import UserNotFoundError
from src.api.v1.notifications.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
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
def mock_repository() -> MagicMock:
    """Мокированный репозиторий."""
    repo = MagicMock()
    repo.get_user_by_id = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_send_notification_success(
    sample_notification_data: dict, mock_repository: MagicMock
) -> None:
    """Тест успешного отправления уведомления"""
    # Нашли пользователя в БД
    mock_repository.get_user_by_id.return_value = {"user_id": uuid.uuid4()}

    notification_service = NotificationService(mock_repository)

    result = await notification_service.send_notification(
        notification=NotificationCreate(**sample_notification_data)
    )

    assert isinstance(result, NotificationResponse)
    assert result.status == NotificationStatus.PENDING
    assert result.id is not None
    assert result.recipient_id == sample_notification_data["recipient_id"]
    assert result.title == sample_notification_data["title"]
    assert result.body == sample_notification_data["body"]
    assert result.is_read is False
    assert isinstance(result.created_at, datetime)
    assert result.created_at.tzinfo is not None


@pytest.mark.asyncio
async def test_send_notification_user_not_found(
    sample_notification_data: dict, mock_repository: MagicMock
) -> None:
    """Тест ошибки при попытке отправить уведомление несуществующему пользователю"""

    # Случай, когда пользователь не найден в БД
    mock_repository.get_user_by_id.return_value = None

    notification_service = NotificationService(mock_repository)

    with pytest.raises(UserNotFoundError) as exc_info:
        # Использует мок репозитория
        await notification_service.send_notification(
            notification=NotificationCreate(**sample_notification_data)
        )
    assert exc_info.value.user_id == sample_notification_data["recipient_id"]
