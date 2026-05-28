from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from interview_pilot.modules.auth.models import User
from interview_pilot.modules.questions import repository
from interview_pilot.modules.questions.schemas import (
    QuestionCategoryReportRow,
    QuestionCreate,
    QuestionRead,
    QuestionUpdate,
)


async def create_question(
    payload: QuestionCreate,
    current_user: User,
    session: AsyncSession,
) -> QuestionRead:
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

    return await repository.create_question(cleaned_payload, current_user.id, session)


async def list_questions(current_user: User, session: AsyncSession) -> list[QuestionRead]:
    return await repository.list_questions(current_user.id, session)


async def get_question(question_id: int, current_user: User, session: AsyncSession) -> QuestionRead:
    question = await repository.get_question(question_id, current_user.id, session)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在",
        )
    return question


async def update_question(
    question_id: int,
    payload: QuestionUpdate,
    current_user: User,
    session: AsyncSession,
) -> QuestionRead:
    update_data = payload.model_dump(exclude_unset=True)

    if "title" in update_data:
        title = payload.title.strip() if payload.title is not None else ""
        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="题目标题不能为空",
            )
        update_data["title"] = title

    if "answer" in update_data:
        answer = payload.answer.strip() if payload.answer is not None else ""
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="题目答案不能为空",
            )
        update_data["answer"] = answer

    cleaned_payload = QuestionUpdate(**update_data)
    question = await repository.update_question(question_id, cleaned_payload, current_user.id, session)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在",
        )
    return question


async def delete_question(question_id: int, current_user: User, session: AsyncSession) -> None:
    deleted = await repository.delete_question(question_id, current_user.id, session)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在",
        )


async def get_category_report(
    current_user: User,
    session: AsyncSession,
) -> list[QuestionCategoryReportRow]:
    return await repository.get_category_report(current_user.id, session)
