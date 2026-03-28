import uuid

import pytest

from src.api.v1.notifications.models import Notification


@pytest.fixture
def sample_notification_data() -> dict:
    """Фикстура с данными для уведомления."""
    return {
        "id": uuid.uuid4(),
        "recipient_id": uuid.uuid4(),
        "title": "Test Notification",
        "body": "Текст уведомления",
    }


def test_notification_model_creation(sample_notification_data: dict) -> None:
    notification = Notification(**sample_notification_data)

    assert notification.id == sample_notification_data["id"]
    assert notification.recipient_id == sample_notification_data["recipient_id"]
    assert notification.title == sample_notification_data["title"]
    assert notification.body == sample_notification_data["body"]
