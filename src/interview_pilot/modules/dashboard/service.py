from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from interview_pilot.core.cache import CacheBackend
from interview_pilot.core.config import settings
from interview_pilot.modules.auth.models import User
from interview_pilot.modules.dashboard import repository
from interview_pilot.modules.dashboard.schemas import DashboardSummary


def _summary_cache_key(user_id: int) -> str:
    return f"dashboard:user:{user_id}:summary"


def _summary_cache_prefix(user_id: int) -> str:
    return f"dashboard:user:{user_id}:"


async def get_dashboard_summary(
    current_user: User,
    session: AsyncSession,
    cache: CacheBackend,
) -> DashboardSummary:
    """
    Dashboard 缓存读取流程。

    学习重点：Cache Aside 模式。
    1. 先查缓存。
    2. 缓存没有，再查数据库。
    3. 查完数据库，把结果写回缓存。
    """
    cache_key = _summary_cache_key(current_user.id)
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return DashboardSummary.model_validate(cached)

    summary = await repository.get_summary_from_db(current_user.id, session)
    await cache.set_json(
        cache_key,
        summary.model_dump(mode="json"),
        ttl_seconds=settings.dashboard_cache_ttl_seconds,
    )
    return summary


async def invalidate_dashboard_cache(user_id: int, cache: CacheBackend) -> None:
    """
    删除用户 dashboard 缓存。

    学习重点：写操作后删除缓存，下一次读取时重新计算。
    这比“写操作后直接更新缓存”更简单，也不容易漏字段。
    """
    await cache.delete_by_prefix(_summary_cache_prefix(user_id))
