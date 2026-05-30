from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class QuestionListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    category: str | None = None
    difficulty_min: int | None = Field(default=None, ge=1, le=5)
    difficulty_max: int | None = Field(default=None, ge=1, le=5)
    keyword: str | None = None


class QuestionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    answer: str = Field(min_length=1)
    category: str = Field(default="general")
    difficulty: int = Field(default=1, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)


class QuestionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    answer: str | None = Field(default=None, min_length=1)
    category: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] | None = None


class QuestionRead(BaseModel):
    id: int
    user_id: int
    title: str
    answer: str
    category: str
    difficulty: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionPage(BaseModel):
    items: list[QuestionRead]
    total: int
    page: int
    size: int
    pages: int


class QuestionCategoryReportRow(BaseModel):
    category: str
    question_count: int
    avg_difficulty: float
    avg_answer_length: float
    hard_question_count: int
    latest_created_at: datetime
    volume_rank: int
