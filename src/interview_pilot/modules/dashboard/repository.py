from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_pilot.modules.dashboard.schemas import CategoryCount, DashboardSummary
from interview_pilot.modules.notes.models import Note
from interview_pilot.modules.questions.models import Question
from interview_pilot.modules.reviews.models import Review


async def _count(stmt, session: AsyncSession) -> int:
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_summary_from_db(user_id: int, session: AsyncSession) -> DashboardSummary:
    """
    从数据库实时统计 dashboard。

    学习重点：缓存之前一定先有“数据库真实查询版本”。
    Redis 只是加速，不应该替代数据库查询逻辑。
    """
    question_count = await _count(
        select(func.count()).select_from(Question).where(Question.user_id == user_id),
        session,
    )
    note_count = await _count(
        select(func.count()).select_from(Note).where(Note.user_id == user_id),
        session,
    )
    review_count = await _count(
        select(func.count()).select_from(Review).where(Review.user_id == user_id),
        session,
    )

    status_result = await session.execute(
        select(Review.status.label("status"), func.count().label("count"))
        .where(Review.user_id == user_id)
        .group_by(Review.status)
    )
    status_rows = status_result.mappings().all()
    status_counts = {str(row["status"]): int(row["count"]) for row in status_rows}

    category_result = await session.execute(
        select(Question.category.label("category"), func.count().label("count"))
        .where(Question.user_id == user_id)
        .group_by(Question.category)
        .order_by(func.count().desc(), Question.category.asc())
    )
    category_rows = category_result.mappings().all()
    category_distribution = [
        CategoryCount(category=str(row["category"]), count=int(row["count"]))
        for row in category_rows
    ]

    return DashboardSummary(
        question_count=question_count,
        note_count=note_count,
        review_count=review_count,
        todo_review_count=status_counts.get("todo", 0),
        reviewing_review_count=status_counts.get("reviewing", 0),
        mastered_review_count=status_counts.get("mastered", 0),
        category_distribution=category_distribution,
    )
