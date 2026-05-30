from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field
from redis.asyncio import Redis

from interview_pilot.core.config import Settings


class DomainEvent(BaseModel):
    """
    领域事件：业务已经发生的事情。

    学习重点：
    - HTTP 请求负责“写数据库”。
    - 写完数据库后发布事件，交给后台 worker 做通知、日志、异步统计等事情。
    - 这样可以减少接口阻塞时间，也把副作用和主流程拆开。
    """

    event_type: str
    user_id: int
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MessageQueue(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...

    async def consume(self, timeout_seconds: int = 1) -> DomainEvent | None: ...

    async def close(self) -> None: ...


class MemoryMessageQueue:
    """
    测试/本地学习用消息队列。

    学习重点：它只在当前 Python 进程内有效，适合测试消息流，但不适合多进程部署。
    真实部署可以切换到 RedisListMessageQueue 或 RabbitMQ/Kafka/Celery 等方案。
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[DomainEvent] = asyncio.Queue()

    async def publish(self, event: DomainEvent) -> None:
        await self._queue.put(event)

    async def consume(self, timeout_seconds: int = 1) -> DomainEvent | None:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout_seconds)
        except TimeoutError:
            return None

    async def close(self) -> None:
        while not self._queue.empty():
            self._queue.get_nowait()


class RedisListMessageQueue:
    """
    基于 Redis List 的轻量消息队列。

    学习重点：Redis List 的 LPUSH + BRPOP 可以模拟一个简单队列。
    但它不是最完整的消息系统：没有复杂路由、重试、死信队列、消费组等能力。
    如果要更工程化，可以继续升级成 Redis Streams / RabbitMQ / Kafka / Celery。
    """

    def __init__(self, redis_url: str, queue_name: str) -> None:
        self._redis: Any = Redis.from_url(redis_url, decode_responses=True)
        self._queue_name = queue_name

    async def publish(self, event: DomainEvent) -> None:
        raw = event.model_dump_json()
        await self._redis.lpush(self._queue_name, raw)

    async def consume(self, timeout_seconds: int = 1) -> DomainEvent | None:
        item = await self._redis.brpop([self._queue_name], timeout=timeout_seconds)
        if item is None:
            return None
        _, raw = item
        data = json.loads(raw)
        return DomainEvent.model_validate(data)

    async def close(self) -> None:
        await self._redis.aclose()


_message_queue: MessageQueue = MemoryMessageQueue()


def build_message_queue(settings: Settings) -> MessageQueue:
    if settings.message_queue_backend == "redis":
        return RedisListMessageQueue(settings.redis_url, settings.message_queue_name)
    return MemoryMessageQueue()


def configure_message_queue(message_queue: MessageQueue) -> None:
    global _message_queue
    _message_queue = message_queue


def get_message_queue() -> MessageQueue:
    return _message_queue
