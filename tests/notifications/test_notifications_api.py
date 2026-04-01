import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.v1.notifications.exceptions import NotificationNotFoundError
from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.schemas import NotificationStatus
from src.config import settings
from src.main import app

client = TestClient(app)


@pytest.fixture
def notification_sample() -> dict:
    notification_id = uuid.uuid4()
    recipient_id = uuid.uuid4()

    return {
        "id": notification_id,
        "recipient_id": recipient_id,
        "title": "Test",
        "body": "Test body",
        "status": NotificationStatus.DELIVERED.value,
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
        "deleted_at": None,
    }


@patch("src.api.v1.notifications.service.NotificationRepository.get_notification_by_id")
def test_get_notification_success(
    mock_get_notification: AsyncMock,
    notification_sample: dict,
) -> None:
    mock_get_notification.return_value = Notification(**notification_sample)

    response = client.get(
        f"{settings.api_v1_prefix}/notifications/get_notification/{notification_sample['id']}",
    )

    assert response.status_code == 200
    mock_get_notification.assert_called_once()


@patch("src.api.v1.notifications.service.NotificationService.get_notification_by_id")
def test_get_notification_not_found(
    mock_get_notification: AsyncMock,
    notification_sample: dict,
) -> None:
    mock_get_notification.side_effect = NotificationNotFoundError(
        notification_sample["id"]
    )

    response = client.get(
        f"{settings.api_v1_prefix}/notifications/get_notification/{notification_sample['id']}",
    )

    assert response.status_code == 404
    mock_get_notification.assert_called_once()


@patch("src.api.v1.notifications.service.NotificationRepository.get_user_notifications")
def test_user_notifications(
    mock_get_user_notifications: AsyncMock,
    notification_sample: dict,
) -> None:
    """Тест: получение всех уведомлений пользователя"""
    # Репозиторий должен возвращать нам только заголовки уведомлений
    mock_get_user_notifications.return_value = [
        notification_sample["title"],
        notification_sample["title"],
        notification_sample["title"],
    ]

    response = client.get(
        f"{settings.api_v1_prefix}/notifications/get_user_notifications/{notification_sample['id']}",
    )

    assert response.status_code == 200
    mock_get_user_notifications.assert_called_once()
