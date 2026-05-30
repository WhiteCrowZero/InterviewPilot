from __future__ import annotations

from pydantic import BaseModel


class CategoryCount(BaseModel):
    category: str
    count: int


class DashboardSummary(BaseModel):
    """
    Dashboard 聚合响应。

    学习重点：这种接口通常会执行多次 COUNT / GROUP BY，
    比普通 CRUD 更适合做缓存。
    """

    question_count: int
    note_count: int
    review_count: int
    todo_review_count: int
    reviewing_review_count: int
    mastered_review_count: int
    category_distribution: list[CategoryCount]
