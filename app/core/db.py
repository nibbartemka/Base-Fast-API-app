from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base

from .config import settings


# Создаем ассинхроный engine
async_engine: AsyncEngine = create_async_engine(
    settings.ASYNC_DB_URL,
    pool_size=5,
    max_overflow=10,
)

# Задаем фабрику для ассинхронных сессий со своими параметрами
AsyncSessionLocal: async_sessionmaker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# Базовый класс для моделей
Base = declarative_base()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
