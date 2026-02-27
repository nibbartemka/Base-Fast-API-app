import asyncio
from typing import AsyncGenerator

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    AsyncSession,
                                    async_sessionmaker)
import pytest_asyncio

from main import app
from app.core import get_async_session, Base
from app.models import Department, Employee


TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_session):
    def override_get_db():
        yield test_session
    app.dependency_overrides[get_async_session] = override_get_db
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
