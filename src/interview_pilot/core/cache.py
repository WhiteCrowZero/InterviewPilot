from __future__ import annotations

import json
import time
from typing import Any, Protocol

from redis.asyncio import Redis

from interview_pilot.core.config import Settings

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


class CacheBackend(Protocol):
    """
    缓存抽象层。

    学习重点：业务代码不要直接依赖 Redis 客户端。先定义一组最小能力，
    service 层只关心 get/set/delete；至于底层是 Redis、内存、还是测试替身，
    都可以通过依赖注入切换。
    """

    async def get_json(self, key: str) -> JsonValue | None: ...

    async def set_json(self, key: str, value: JsonValue, ttl_seconds: int) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def delete_by_prefix(self, prefix: str) -> None: ...

    async def close(self) -> None: ...

'''
class CacheService:
    """缓存服务"""

    @staticmethod
    def set_value(key, val, cache="default", exp=settings.DEFAULT_EXPIRE_SECONDS):
        """设置缓存值"""
        caches[cache].set(key, val, exp)

    @staticmethod
    def validate_value(key, val, cache="default"):
        """校验缓存值"""
        cached_val = caches[cache].get(key)
        if cached_val is None:
            return False
        if val != cached_val:
            return False
        return True

    @staticmethod
    def del_value(key, cache="default"):
        """删除缓存值"""
        caches[cache].delete(key)

    @staticmethod
    def get_value(key, cache="default"):
        """获取缓存值"""
        return caches[cache].get(key)

'''


class MemoryCacheBackend:
    """
    测试/本地学习用的内存缓存。

    学习重点：内存缓存不会跨进程共享，服务重启后数据也会丢失，
    所以它不能替代 Redis；但它很适合测试，因为不需要额外启动服务。
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[float | None, str]] = {}

    async def get_json(self, key: str) -> JsonValue | None:
        item = self._store.get(key)
        if item is None:
            return None

        expire_at, raw = item
        if expire_at is not None and expire_at <= time.time():
            self._store.pop(key, None)
            return None

        return json.loads(raw)

    async def set_json(self, key: str, value: JsonValue, ttl_seconds: int) -> None:
        expire_at = time.time() + ttl_seconds if ttl_seconds > 0 else None
        self._store[key] = (expire_at, json.dumps(value, ensure_ascii=False))

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def delete_by_prefix(self, prefix: str) -> None:
        for key in list(self._store):
            if key.startswith(prefix):
                self._store.pop(key, None)

    async def close(self) -> None:
        self._store.clear()


class RedisCacheBackend:
    """
    Redis 缓存实现。

    学习重点：
    1. Redis 适合缓存“读多写少、可以短时间不完全实时”的数据。
    2. 不要把 Redis 当数据库真相来源，数据库才是最终事实。
    3. 本项目把 dashboard summary 放进 Redis；当 question/note/review 改变时删除缓存。
    """

    def __init__(self, redis_url: str) -> None:
        self._redis: Any = Redis.from_url(redis_url, decode_responses=True)

    async def get_json(self, key: str) -> JsonValue | None:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: JsonValue, ttl_seconds: int) -> None:
        await self._redis.set(key, json.dumps(value, ensure_ascii=False), ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def delete_by_prefix(self, prefix: str) -> None:
        keys: list[str] = []
        async for key in self._redis.scan_iter(match=f"{prefix}*"):
            keys.append(key)
        if keys:
            await self._redis.delete(*keys)

    async def close(self) -> None:
        await self._redis.aclose()


_cache_backend: CacheBackend = MemoryCacheBackend()


def build_cache_backend(settings: Settings) -> CacheBackend:
    if settings.cache_backend == "redis":
        return RedisCacheBackend(settings.redis_url)
    return MemoryCacheBackend()


def configure_cache_backend(cache_backend: CacheBackend) -> None:
    global _cache_backend
    _cache_backend = cache_backend


def get_cache_backend() -> CacheBackend:
    return _cache_backend
