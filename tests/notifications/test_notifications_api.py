import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.v1.notifications.exceptions import NotificationNotFoundError
from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.schemas import NotificationStatus, NotificationResponse
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


# POST notifications/create_notification
def test_create_notification(
    notification_sample: dict,
    notification_service_override,
):
    """Тест создания уведомления с изолированными зависимостями."""
    mock_repo, _ = notification_service_override

    created_notification = Notification(**notification_sample)
    mock_repo.create_notification.return_value = created_notification

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

    mock_repo.create_notification.assert_awaited_once()


# GET notifications/get_notification_by_id
def test_get_notification_success(
    notification_sample: dict,
    notification_service_override,
) -> None:
    mock_repo, _ = notification_service_override
    mock_repo.get_notification_by_id.return_value = Notification(**notification_sample)

    response = client.get(
        f"{settings.api_v1_prefix}/notifications/get_notification/{notification_sample['id']}",
    )

    assert response.status_code == 200
    mock_repo.get_notification_by_id.assert_awaited_once_with(notification_sample["id"])


def test_get_notification_not_found(
    notification_sample: dict,
    notification_service_override,
) -> None:
    mock_repo, _ = notification_service_override
    mock_repo.get_notification_by_id.side_effect = NotificationNotFoundError(
        notification_sample["id"]
    )

    response = client.get(
        f"{settings.api_v1_prefix}/notifications/get_notification/{notification_sample['id']}",
    )

    assert response.status_code == 404
    mock_repo.get_notification_by_id.assert_awaited_once_with(notification_sample["id"])


# GET notifications/get_user_notifications
def test_user_notifications(
    notification_sample: dict,
    notification_service_override,
) -> None:
    """Тест: получение всех уведомлений пользователя"""
    mock_repo, _ = notification_service_override
    # Репозиторий должен возвращать нам только заголовки уведомлений
    mock_repo.get_user_notifications.return_value = [
        notification_sample["title"],
        notification_sample["title"],
        notification_sample["title"],
    ]

    response = client.get(
        f"{settings.api_v1_prefix}/notifications/get_user_notifications/{notification_sample['id']}",
    )

    assert response.status_code == 200
    mock_repo.get_user_notifications.assert_awaited_once_with(notification_sample["id"])


def test_user_notifications_no_notifications(
    notification_sample: dict,
    notification_service_override,
) -> None:
    """Тест: получение пустого списка всех уведомлений пользователя"""
    mock_repo, _ = notification_service_override
    mock_repo.get_user_notifications.return_value = []

    response = client.get(
        f"{settings.api_v1_prefix}/notifications/get_user_notifications/{notification_sample['id']}",
    )

    assert response.status_code == 200
    assert response.json() == []
    mock_repo.get_user_notifications.assert_awaited_once_with(notification_sample["id"])


# PATCH notifications/mark_notification_as_read
def test_mark_notification_as_read(
    notification_sample: dict,
    notification_service_override,
):
    """Тест: обновление уведомления при прочтении"""
    notification = Notification(**notification_sample)
    mock_repo, _ = notification_service_override
    mock_repo.get_notification_by_id.return_value = notification

    async def mark_as_read(notification_to_update: Notification):
        notification_to_update.is_read = True

    mock_repo.mark_notification_as_read.side_effect = mark_as_read

    response = client.patch(
        f"{settings.api_v1_prefix}/notifications/mark_notification_as_read/{notification_sample['id']}",
    )

    assert response.status_code == 200

    data = response.json()
    assert data["is_read"] is True
    assert data["status"] == NotificationStatus.SENT

    mock_repo.get_notification_by_id.assert_awaited_once_with(notification_sample["id"])
    mock_repo.mark_notification_as_read.assert_awaited_once_with(notification)


def test_mark_notification_as_read_not_found(
    notification_sample: dict, notification_service_override
) -> None:
    """Тест: ручка mark_notification_as_read возвращает 404, если уведомление не найдено."""
    mock_repo, _ = notification_service_override
    mock_repo.get_notification_by_id.return_value = None

    response = client.patch(
        f"{settings.api_v1_prefix}/notifications/mark_notification_as_read/{notification_sample['id']}",
    )
    assert response.status_code == 404
    mock_repo.get_notification_by_id.assert_awaited_once_with(notification_sample["id"])


# DELETE notifications/delete_notification
def test_delete_notification_success(notification_sample: dict, notification_service_override):
    """Тест ручки для удаления сообщений (случай: уведомление найдено)."""
    mock_repo, _ = notification_service_override
    mock_repo.get_notification_by_id.return_value = Notification(**notification_sample)
    response = client.delete(
        f"{settings.api_v1_prefix}/notifications/delete_notification/{notification_sample['id']}",
    )

    assert response.status_code == 204
    mock_repo.get_notification_by_id.assert_awaited_once_with(notification_sample["id"])
    mock_repo.delete_notification.assert_awaited_once_with(notification_sample["id"])


def test_delete_notification_not_found(
    notification_sample: dict, notification_service_override
):
    """Тест ручки для удаления сообщений (случай: уведомление не найдено)."""
    mock_repo, _ = notification_service_override
    mock_repo.get_notification_by_id.side_effect = NotificationNotFoundError(
        notification_sample["id"]
    )

    response = client.delete(
        f"{settings.api_v1_prefix}/notifications/delete_notification/{notification_sample['id']}",
    )

    assert response.status_code == 404
    mock_repo.get_notification_by_id.assert_awaited_once_with(notification_sample["id"])
