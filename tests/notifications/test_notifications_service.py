import uuid
from datetime import datetime

import pytest

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


@pytest.mark.asyncio
async def test_send_notification_success(sample_notification_data: dict) -> None:
    """Тест успешного отправления уведомления"""
    notification_service = NotificationService()

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
