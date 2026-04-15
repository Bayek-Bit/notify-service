"""Глобальные фикстуры для тестов."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncConnection,
)
from sqlalchemy.pool import NullPool

from src.api.v1.auth.dependencies import verify_service_token
from src.api.v1.notifications.dependencies import get_notification_service
from src.api.v1.notifications.models import Notification
from src.api.v1.notifications.repository import NotificationRepository
from src.api.v1.notifications.schemas import NotificationStatus
from src.api.v1.notifications.service import NotificationService
from src.config import settings
from src.database import Base
from src.main import app

# ─────────────────────────────────────────────────────────────
# Конфигурация: тестовая БД
# ─────────────────────────────────────────────────────────────
TEST_DATABASE_URL = settings.db.DATABASE_URL.replace(
    "notifications", "notifications_test"
)


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Базовый мок репозитория. Можно задавать return_value/side_effect внутри теста."""
    mock_repo = AsyncMock()

    return mock_repo


@pytest.fixture
def mock_queue_producer() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def notification_service_override(mock_repository, mock_queue_producer):
    """
    Фикстура для подмены зависимости.
    Не используйте autouse=True, если не хотите одинакового поведения во всех тестах.
    """

    def fake_get_service():
        return NotificationService(
            repo=mock_repository, queue_producer=mock_queue_producer
        )

    # Подменяем ДО выполнения теста
    app.dependency_overrides[get_notification_service] = fake_get_service

    # Возвращаем моки в тест, чтобы в нём настраивать поведение
    yield mock_repository, mock_queue_producer

    # Чистим ТОЛЬКО эту зависимость после теста
    app.dependency_overrides.pop(get_notification_service, None)


@pytest.fixture(autouse=True)
def mock_auth_for_tests():
    """Отключает проверку JWT в API-тестах через dependency_overrides (как в FastAPI)."""

    async def override_verify_service_token() -> bool:
        return True

    app.dependency_overrides[verify_service_token] = override_verify_service_token
    yield
    app.dependency_overrides.pop(verify_service_token, None)


@pytest.fixture(scope="session")
def event_loop():
    """Создаёт event loop для асинхронных фикстур."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Создаёт асинхронный движок для тестовой БД."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,  # Важно: не пулить соединения в тестах
        echo=False,  # Для отладки: echo=True
    )

    # Создаём таблицы перед всеми тестами
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Удаляем таблицы после всех тестов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронная сессия с транзакцией и откатом.

    Каждый тест работает в своей транзакции:
    - Начинается перед тестом
    - Откатывается после теста (все изменения отменяются)
    """
    # Создаём сессию
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    session = async_session()

    # Начинаем транзакцию
    await session.begin()
    try:
        yield session
    finally:
        # Транзакция откатится автоматически при выходе из begin()
        # но можно явно для ясности:
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture
async def notification_repo(db_session: AsyncSession) -> NotificationRepository:
    """Репозиторий с тестовой асинхронной сессией."""
    return NotificationRepository(session=db_session)


@pytest.fixture
def notification_full(notification_sample: dict) -> Notification:
    """Полноценный объект Notification для тестов."""
    return Notification(
        id=uuid.uuid4(),
        recipient_id=notification_sample["recipient_id"],
        title=notification_sample["title"],
        body=notification_sample["body"],
        status=NotificationStatus.PENDING,
        is_read=False,
        created_at=datetime.now(timezone.utc),
        # read_at=None,
        deleted_at=None,
    )
