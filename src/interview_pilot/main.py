from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from interview_pilot.api.v1.router import api_router
from interview_pilot.core.cache import (
    build_cache_backend,
    configure_cache_backend,
    get_cache_backend,
)
from interview_pilot.core.config import settings
from interview_pilot.core.message_queue import (
    build_message_queue,
    configure_message_queue,
    get_message_queue,
)
from interview_pilot.realtime.manager import websocket_manager
from interview_pilot.workers.event_worker import run_event_worker


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    应用生命周期。

    学习重点：需要打开/关闭的资源，不要散落在业务代码里。
    例如 Redis 连接、消息队列、后台 worker，都适合在 lifespan 中统一管理。
    """
    cache_backend = build_cache_backend(settings)
    message_queue = build_message_queue(settings)
    configure_cache_backend(cache_backend)
    configure_message_queue(message_queue)

    worker_task: asyncio.Task[None] | None = None
    if settings.enable_background_worker:
        worker_task = asyncio.create_task(run_event_worker(message_queue, websocket_manager))

    try:
        yield
    finally:
        if worker_task is not None:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        await websocket_manager.close_all()
        await get_message_queue().close()
        await get_cache_backend().close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=f"{settings.api_prefix}/{settings.api_version}")
    return app


app = create_app()
