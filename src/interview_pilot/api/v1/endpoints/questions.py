from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from interview_pilot.api.deps import get_session
from interview_pilot.modules.questions import service
from interview_pilot.modules.questions.schemas import (
    QuestionCategoryReportRow,
    QuestionCreate,
    QuestionRead,
)

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "",
    response_model=QuestionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(payload: QuestionCreate, session: DbSession) -> QuestionRead:
    return await service.create_question(payload, session)


@router.get("", response_model=list[QuestionRead])
async def list_questions(session: DbSession) -> list[QuestionRead]:
    return await service.list_questions(session)


@router.get("/reports/category-summary", response_model=list[QuestionCategoryReportRow])
async def get_category_summary_report(session: DbSession) -> list[QuestionCategoryReportRow]:
    return await service.get_category_report(session)
