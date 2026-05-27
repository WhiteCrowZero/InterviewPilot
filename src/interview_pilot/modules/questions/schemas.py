from datetime import datetime
from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    answer: str = Field(min_length=1)
    category: str = Field(default="general")
    difficulty: int = Field(default=1, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)


class QuestionRead(BaseModel):
    id: int
    title: str
    answer: str
    category: str
    difficulty: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionCategoryReportRow(BaseModel):
    category: str
    question_count: int
    avg_difficulty: float
    avg_answer_length: float
    hard_question_count: int
    latest_created_at: datetime
    volume_rank: int
