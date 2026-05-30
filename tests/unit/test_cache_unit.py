from __future__ import annotations

import asyncio

import interview_pilot.core.cache as cache_module
from interview_pilot.core.cache import MemoryCacheBackend


def test_memory_cache_get_set_and_delete_json() -> None:
    async def scenario() -> None:
        cache = MemoryCacheBackend()
        await cache.set_json("question:1", {"title": "Redis"}, ttl_seconds=60)

        assert await cache.get_json("question:1") == {"title": "Redis"}

        await cache.delete("question:1")
        assert await cache.get_json("question:1") is None

    asyncio.run(scenario())


def test_memory_cache_delete_by_prefix_only_deletes_matching_keys() -> None:
    async def scenario() -> None:
        cache = MemoryCacheBackend()
        await cache.set_json("dashboard:user:1:summary", {"count": 1}, ttl_seconds=60)
        await cache.set_json("dashboard:user:2:summary", {"count": 2}, ttl_seconds=60)

        await cache.delete_by_prefix("dashboard:user:1:")

        assert await cache.get_json("dashboard:user:1:summary") is None
        assert await cache.get_json("dashboard:user:2:summary") == {"count": 2}

    asyncio.run(scenario())


def test_memory_cache_respects_ttl(monkeypatch) -> None:
    current_time = {"value": 1000.0}
    monkeypatch.setattr(cache_module.time, "time", lambda: current_time["value"])

    async def scenario() -> None:
        cache = MemoryCacheBackend()
        await cache.set_json("short", "value", ttl_seconds=10)

        assert await cache.get_json("short") == "value"
        current_time["value"] = 1011.0
        assert await cache.get_json("short") is None

    asyncio.run(scenario())
