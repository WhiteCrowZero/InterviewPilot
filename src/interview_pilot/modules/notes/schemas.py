from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NoteListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    question_id: int | None = Field(default=None, ge=1)
    keyword: str | None = None


class NoteCreate(BaseModel):
    question_id: int = Field(ge=1)
    content: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)


class NoteRead(BaseModel):
    id: int
    user_id: int
    question_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotePage(BaseModel):
    items: list[NoteRead]
    total: int
    page: int
    size: int
    pages: int
