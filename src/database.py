# DB connection related stuff
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy import func

from src.config import settings


class Base(DeclarativeBase):
    """Базовый класс для моделей"""
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"



# Инициализация движка БД
engine = create_async_engine(settings.db.DATABASE_URL, echo=settings.db.ECHO)
session_factory = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость FastAPI для получения сессии БД"""
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Инициализация таблиц (для development)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)