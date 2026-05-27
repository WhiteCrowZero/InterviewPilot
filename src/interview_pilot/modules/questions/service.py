from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from interview_pilot.modules.questions import repository
from interview_pilot.modules.questions.schemas import (
    QuestionCategoryReportRow,
    QuestionCreate,
    QuestionRead,
)


async def create_question(payload: QuestionCreate, session: AsyncSession) -> QuestionRead:
    title = payload.title.strip()
    answer = payload.answer.strip()

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="题目标题不能为空",
        )

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="题目答案不能为空",
        )

    cleaned_payload = QuestionCreate(
        title=title,
        answer=answer,
        category=payload.category,
        difficulty=payload.difficulty,
        tags=payload.tags,
    )

    return await repository.create_question(cleaned_payload, session)


async def list_questions(session: AsyncSession) -> list[QuestionRead]:
    return await repository.list_questions(session)


async def get_category_report(session: AsyncSession) -> list[QuestionCategoryReportRow]:
    return await repository.get_category_report(session)
