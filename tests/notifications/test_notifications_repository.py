import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.repository import NotificationRepository


@pytest.fixture
def sample_notification() -> Notification:
    return Notification(
        id=uuid.uuid4(),
        recipient_id=uuid.uuid4(),
        title="Test Notification",
        body="Test body content",
        is_read=False,
        deleted_at=None,
    )


@pytest.mark.asyncio
async def test_mark_notification_is_read(
    db_session: AsyncSession,
    notification_repo: NotificationRepository,
    sample_notification: Notification,
) -> None:
    db_session.add(sample_notification)
    await db_session.commit()
    await db_session.refresh(sample_notification)  # Для auto полей (created_at)

    await notification_repo.mark_notification_as_read(sample_notification.id)
    await db_session.refresh(sample_notification)

    assert sample_notification.is_read is True
    assert sample_notification.created_at is not None
