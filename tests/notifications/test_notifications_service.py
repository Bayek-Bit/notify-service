import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

import pytest

from src.api.v1.notifications.exceptions import (
    NotificationNotFoundError,
)
from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
    NotificationMarkAsRead,
    NotificationTask,
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
    """Тест успешной отправки задачи уведомления в очередь через _safe_send_task"""
    mock_repo, mock_queue = notification_service_override

    # Успешно отправили сообщение
    mock_queue.send_notification_task.return_value = True

    notification_service = NotificationService(mock_repo, mock_queue)

    task = NotificationTask(
        id=uuid.uuid4(),
        recipient_id=sample_notification_data["recipient_id"],
        title=sample_notification_data["title"],
        body=sample_notification_data["body"],
    )

    await notification_service._safe_send_task(task, "message")

    mock_queue.send_notification_task.assert_awaited_once_with(task, "message")


@pytest.mark.asyncio
async def test_create_notification_sends_to_queue(
    sample_notification_data,
    notification_full,
    notification_service_override,
):
    mock_repo, mock_queue = notification_service_override
    mock_repo.create_notification.return_value = notification_full
    mock_queue.send_notification_task.return_value = True

    service = NotificationService(mock_repo, mock_queue)
    await service.create_notification(NotificationCreate(**sample_notification_data))

    # Даём event loop обработать фоновые задачи
    await asyncio.sleep(0)

    mock_queue.send_notification_task.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_notification_sends_notification_with_id(
    sample_notification_data,
    notification_full,
    notification_service_override,
):
    mock_repo, mock_queue = notification_service_override
    mock_repo.create_notification.return_value = notification_full
    mock_queue.send_notification_task.return_value = True

    service = NotificationService(mock_repo, mock_queue)
    await service.create_notification(NotificationCreate(**sample_notification_data))

    await asyncio.sleep(0)

    mock_queue.send_notification_task.assert_awaited_once()

    call_args = mock_queue.send_notification_task.await_args
    sent_task = call_args.args[0]
    sent_task_type = call_args.args[1]

    assert isinstance(sent_task, NotificationTask)
    assert sent_task.id == notification_full.id
    assert sent_task.recipient_id == notification_full.recipient_id
    assert sent_task.title == notification_full.title
    assert sent_task.body == notification_full.body
    assert sent_task_type == "message"


@pytest.mark.asyncio
async def test_create_notification_sets_pending_status(
    sample_notification_data,
    notification_full,
    notification_service_override,
):
    mock_repo, mock_queue = notification_service_override

    notification_full.status = NotificationStatus.PENDING
    mock_repo.create_notification.return_value = notification_full

    service = NotificationService(mock_repo, mock_queue)

    result = await service.create_notification(
        NotificationCreate(**sample_notification_data)
    )

    assert result.status == NotificationStatus.PENDING


@pytest.mark.asyncio
async def test_create_notification_does_not_wait_for_queue(
    sample_notification_data,
    notification_full,
    notification_service_override,
):
    mock_repo, mock_queue = notification_service_override

    mock_repo.create_notification.return_value = notification_full

    async def slow_send(*args, **kwargs):
        import asyncio

        await asyncio.sleep(1)
        return True

    mock_queue.send_notification_task.side_effect = slow_send

    service = NotificationService(mock_repo, mock_queue)

    import time

    start = time.perf_counter()

    await service.create_notification(NotificationCreate(**sample_notification_data))

    duration = time.perf_counter() - start

    # Метод должен отработать быстро (<1 сек)
    assert duration < 0.1


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
