"""Глобальные фикстуры для тестов."""

import asyncio
import uuid
from typing import AsyncGenerator
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
from src.api.v1.notifications.repository import NotificationRepository
from src.config import settings
from src.database import Base
from src.main import app

# ─────────────────────────────────────────────────────────────
# Конфигурация: тестовая БД
# ─────────────────────────────────────────────────────────────
TEST_DATABASE_URL = settings.db.DATABASE_URL.replace(
    "notifications", "notifications_test"
)


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
