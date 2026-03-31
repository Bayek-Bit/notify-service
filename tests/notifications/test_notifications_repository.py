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


@pytest.fixture
def sample_user_notification_list() -> dict:
    """Фикстура: создает список уведомлений для одного пользователя"""
    recipient_id = uuid.uuid4()

    notification_list = []
    for i in range(3):
        notification = Notification(
            id=uuid.uuid4(),
            recipient_id=recipient_id,
            title="Test Notification",
            body="Test body content",
            is_read=False,
            deleted_at=None,
        )
        notification_list.append(notification)

    return {
        "user_id": recipient_id,
        "notifications": notification_list,
    }


@pytest.mark.asyncio
async def test_mark_notification_is_read(
    db_session: AsyncSession,
    notification_repo: NotificationRepository,
    sample_notification: Notification,
) -> None:
    """
    Тест: отметка уведомления как прочитанного.

    Проверяет, что:
    1. Уведомление создаётся в БД
    2. Метод mark_notification_as_read обновляет is_read
    3. Изменения сохраняются и читаются из БД

    После теста транзакция откатывается (данные не остаются)
    """

    db_session.add(sample_notification)
    await db_session.commit()
    await db_session.refresh(sample_notification)  # Для auto полей (created_at)

    await notification_repo.mark_notification_as_read(sample_notification)
    await db_session.refresh(sample_notification)

    assert sample_notification.is_read is True
    assert sample_notification.created_at is not None


@pytest.mark.asyncio
async def test_get_notification_by_id_success(
    db_session: AsyncSession,
    notification_repo: NotificationRepository,
    sample_notification: Notification,
) -> None:
    """Тест: уведомление найдено"""
    db_session.add(sample_notification)
    await db_session.commit()

    get_notification = await notification_repo.get_notification_by_id(
        notification_id=sample_notification.id
    )

    assert isinstance(get_notification, Notification)
    assert get_notification == sample_notification


@pytest.mark.asyncio
async def test_get_notification_by_id_not_found(
    db_session: AsyncSession,
    notification_repo: NotificationRepository,
    sample_notification: Notification,
) -> None:
    """Тест: уведомление не найдено"""
    get_null_notification = await notification_repo.get_notification_by_id(
        notification_id=uuid.uuid4()
    )

    assert get_null_notification is None


@pytest.mark.asyncio
async def test_get_user_notifications(
    db_session: AsyncSession,
    notification_repo: NotificationRepository,
    sample_user_notification_list: dict,
) -> None:
    """Тест: получение уведомлений пользователя"""
    for i in sample_user_notification_list["notifications"]:
        db_session.add(i)
    await db_session.commit()

    user_id = sample_user_notification_list["user_id"]

    notifications = await notification_repo.get_user_notifications(user_id)

    assert len(notifications) == 3


@pytest.mark.asyncio
async def test_get_user_notifications_not_found(
    notification_repo: NotificationRepository,
) -> None:
    """Тест: получение уведомлений пользователя, у которого их нет"""
    user_id = uuid.uuid4()

    notifications = await notification_repo.get_user_notifications(user_id)

    assert notifications == []
