from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReviewStatus = Literal["todo", "reviewing", "mastered"]


class ReviewListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    question_id: int | None = Field(default=None, ge=1)
    status: ReviewStatus | None = None
    keyword: str | None = None


class ReviewCreate(BaseModel):
    question_id: int = Field(ge=1)
    mistake_reason: str = Field(min_length=1)
    status: ReviewStatus = "todo"


class ReviewUpdate(BaseModel):
    mistake_reason: str | None = Field(default=None, min_length=1)
    status: ReviewStatus | None = None
    review_count: int | None = Field(default=None, ge=0)


class ReviewRead(BaseModel):
    id: int
    user_id: int
    question_id: int
    status: ReviewStatus
    mistake_reason: str
    review_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewPage(BaseModel):
    items: list[ReviewRead]
    total: int
    page: int
    size: int
    pages: int
