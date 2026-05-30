from __future__ import annotations

import asyncio
import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 测试默认不依赖外部 Redis，也不自动启动后台 worker。
# 这样普通 API 测试更稳定：写操作产生的事件会留在内存队列里，方便断言。
os.environ.setdefault("CACHE_BACKEND", "memory")
os.environ.setdefault("MESSAGE_QUEUE_BACKEND", "memory")
os.environ.setdefault("ENABLE_BACKGROUND_WORKER", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-interview-pilot")

import interview_pilot.db.models  # noqa: F401,E402  # 注册所有 SQLAlchemy model
from interview_pilot.api.deps import get_session  # noqa: E402
from interview_pilot.core.cache import MemoryCacheBackend, configure_cache_backend  # noqa: E402
from interview_pilot.core.config import settings  # noqa: E402
from interview_pilot.core.message_queue import (  # noqa: E402
    MemoryMessageQueue,
    configure_message_queue,
)
from interview_pilot.db.base import Base  # noqa: E402
from interview_pilot.main import app  # noqa: E402
from interview_pilot.realtime.manager import websocket_manager  # noqa: E402

API_PREFIX = "/api/v1"


async def _rebuild_database(database_url: str) -> None:
    engine = create_async_engine(database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def _make_client(tmp_path: Path, *, enable_background_worker: bool) -> Generator[TestClient]:
    """
    为每个测试创建独立的 TestClient。核心目的：
    1. 每个测试使用自己的 SQLite 文件，互不污染。
    2. 每个测试使用新的内存缓存和内存队列。
    3. 普通测试默认关闭后台 worker；需要测 WebSocket 事件流时再打开。
    """
    database_path = tmp_path / "interview_pilot_test.db"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    asyncio.run(_rebuild_database(database_url))

    previous_enable_worker = settings.enable_background_worker
    previous_cache_backend = settings.cache_backend
    previous_queue_backend = settings.message_queue_backend

    settings.enable_background_worker = enable_background_worker
    settings.cache_backend = "memory"
    settings.message_queue_backend = "memory"

    configure_cache_backend(MemoryCacheBackend())
    configure_message_queue(MemoryMessageQueue())
    websocket_manager.reset_for_tests()
    app.dependency_overrides.clear()

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        websocket_manager.reset_for_tests()
        configure_cache_backend(MemoryCacheBackend())
        configure_message_queue(MemoryMessageQueue())
        asyncio.run(engine.dispose())
        settings.enable_background_worker = previous_enable_worker
        settings.cache_backend = previous_cache_backend
        settings.message_queue_backend = previous_queue_backend


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient]:
    yield from _make_client(tmp_path, enable_background_worker=False)


@pytest.fixture
def client_with_worker(tmp_path: Path) -> Generator[TestClient]:
    yield from _make_client(tmp_path, enable_background_worker=True)
