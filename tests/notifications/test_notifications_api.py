import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.v1.notifications.dependencies import get_notification_service
from src.api.v1.notifications.exceptions import NotificationNotFoundError
from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.schemas import NotificationStatus, NotificationResponse
from src.api.v1.notifications.service import NotificationService
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


def create_mock_repo(notification: Notification) -> AsyncMock:
    """
    Создает мок репозитория
    Мокает логику успешного получения уведомления по id и прочтения уведомления
    """
    mock_repo = AsyncMock()

    mock_repo.get_notification_by_id.return_value = notification

    async def mark_as_read(notification):
        notification.is_read = True

    mock_repo.mark_notification_as_read.side_effect = mark_as_read

    return mock_repo


# POST notifications/create_notification
def test_create_notification(notification_sample: dict):

    response = client.post(
        f"{settings.api_v1_prefix}/notifications/create_notification",
        json={
            "recipient_id": str(notification_sample["recipient_id"]),
            "title": notification_sample["title"],
            "body": notification_sample["body"],
        },
    )

    assert response.status_code == 201
    assert NotificationResponse.model_validate(response.json())


# GET notifications/get_notification_by_id
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


# GET notifications/get_user_notifications
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


@patch("src.api.v1.notifications.service.NotificationRepository.get_user_notifications")
def test_user_notifications_no_notifications(
    mock_get_user_notifications: AsyncMock,
    notification_sample: dict,
) -> None:
    """Тест: получение пустого списка всех уведомлений пользователя"""
    mock_get_user_notifications.return_value = []

    response = client.get(
        f"{settings.api_v1_prefix}/notifications/get_user_notifications/{notification_sample['id']}",
    )

    assert response.status_code == 200
    assert response.json() == []
    mock_get_user_notifications.assert_called_once()


# PATCH notifications/mark_notification_as_read
def test_mark_notification_as_read(
    notification_sample: dict,
):
    """Тест: обновление уведомления при прочтении"""
    notification = Notification(**notification_sample)
    mock_repo = create_mock_repo(notification)

    app.dependency_overrides[get_notification_service] = lambda: NotificationService(
        mock_repo
    )

    response = client.patch(
        f"{settings.api_v1_prefix}/notifications/mark_notification_as_read/{notification_sample['id']}",
    )

    assert response.status_code == 200

    data = response.json()
    assert data["is_read"] is True
    assert data["status"] == NotificationStatus.SENT

    mock_repo.mark_notification_as_read.assert_awaited_once()
