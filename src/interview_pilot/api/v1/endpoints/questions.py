from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from starlette import status

from interview_pilot.api.deps import CacheDep, CurrentActiveUserDep, DbSessionDep, MessageQueueDep
from interview_pilot.modules.questions import service
from interview_pilot.modules.questions.schemas import (
    QuestionCategoryReportRow,
    QuestionCreate,
    QuestionListParams,
    QuestionPage,
    QuestionRead,
    QuestionUpdate,
)

router = APIRouter()


@router.post(
    "",
    response_model=QuestionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    payload: QuestionCreate,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
    message_queue: MessageQueueDep,
) -> QuestionRead:
    return await service.create_question(payload, current_user, session, cache, message_queue)


@router.get("", response_model=QuestionPage)
async def list_questions(
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    difficulty_min: Annotated[int | None, Query(ge=1, le=5)] = None,
    difficulty_max: Annotated[int | None, Query(ge=1, le=5)] = None,
    keyword: str | None = None,
) -> QuestionPage:
    params = QuestionListParams(
        page=page,
        size=size,
        category=category,
        difficulty_min=difficulty_min,
        difficulty_max=difficulty_max,
        keyword=keyword,
    )
    return await service.list_questions(params, current_user, session)


@router.get("/reports/category-summary", response_model=list[QuestionCategoryReportRow])
async def get_category_summary_report(
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
) -> list[QuestionCategoryReportRow]:
    return await service.get_category_report(current_user, session)


@router.get("/{question_id}", response_model=QuestionRead)
async def get_question(
    question_id: int,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
) -> QuestionRead:
    return await service.get_question(question_id, current_user, session)


@router.patch("/{question_id}", response_model=QuestionRead)
async def update_question(
    question_id: int,
    payload: QuestionUpdate,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
    message_queue: MessageQueueDep,
) -> QuestionRead:
    return await service.update_question(
        question_id, payload, current_user, session, cache, message_queue
    )


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
    message_queue: MessageQueueDep,
) -> None:
    await service.delete_question(question_id, current_user, session, cache, message_queue)
