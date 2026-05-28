from __future__ import annotations

from fastapi import APIRouter
from starlette import status

from interview_pilot.api.deps import CurrentActiveUserDep, DbSessionDep
from interview_pilot.modules.questions import service
from interview_pilot.modules.questions.schemas import (
    QuestionCategoryReportRow,
    QuestionCreate,
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
) -> QuestionRead:
    return await service.create_question(payload, current_user, session)


@router.get("", response_model=list[QuestionRead])
async def list_questions(current_user: CurrentActiveUserDep, session: DbSessionDep) -> list[QuestionRead]:
    return await service.list_questions(current_user, session)


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
) -> QuestionRead:
    return await service.update_question(question_id, payload, current_user, session)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
        question_id: int,
        current_user: CurrentActiveUserDep,
        session: DbSessionDep,
) -> None:
    await service.delete_question(question_id, current_user, session)
