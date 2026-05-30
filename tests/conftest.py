import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import interview_pilot.db.models  # noqa: F401
from interview_pilot.api.deps import get_session
from interview_pilot.core.cache import MemoryCacheBackend, configure_cache_backend
from interview_pilot.core.message_queue import MemoryMessageQueue, configure_message_queue
from interview_pilot.db.base import Base
from interview_pilot.main import app
from interview_pilot.realtime.manager import websocket_manager

TEST_DATABASE_URL = "sqlite+aiosqlite:///./temps/test_interview_pilot.db"
Path("temps").mkdir(exist_ok=True)


async def _reset_database() -> None:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def create_test_client() -> TestClient:
    asyncio.run(_reset_database())
    app.dependency_overrides.clear()
    configure_cache_backend(MemoryCacheBackend())
    configure_message_queue(MemoryMessageQueue())
    websocket_manager.reset_for_tests()

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)
