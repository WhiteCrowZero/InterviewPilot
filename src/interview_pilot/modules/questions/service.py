from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from interview_pilot.core.cache import CacheBackend
from interview_pilot.core.message_queue import DomainEvent, MessageQueue
from interview_pilot.modules.auth.models import User
from interview_pilot.modules.dashboard.service import invalidate_dashboard_cache
from interview_pilot.modules.questions import repository
from interview_pilot.modules.questions.schemas import (
    QuestionCategoryReportRow,
    QuestionCreate,
    QuestionListParams,
    QuestionPage,
    QuestionRead,
    QuestionUpdate,
)


async def _publish_question_event(
    message_queue: MessageQueue,
    event_type: str,
    current_user: User,
    question: QuestionRead | None = None,
    question_id: int | None = None,
) -> None:
    """
    发布题目相关事件。

    学习重点：数据库写入成功后再发布事件，避免“消息发出去了，但数据库失败了”。
    更严格的企业级做法会使用 outbox pattern，这里先用最容易理解的方式。
    """
    await message_queue.publish(
        DomainEvent(
            event_type=event_type,
            user_id=current_user.id,
            payload={
                "question_id": question.id if question is not None else question_id,
                "title": question.title if question is not None else None,
            },
        )
    )


async def create_question(
    payload: QuestionCreate,
    current_user: User,
    session: AsyncSession,
    cache: CacheBackend,
    message_queue: MessageQueue,
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

    question = await repository.create_question(cleaned_payload, current_user.id, session)
    await invalidate_dashboard_cache(current_user.id, cache)
    await _publish_question_event(message_queue, "question.created", current_user, question)
    return question


async def list_questions(
    params: QuestionListParams,
    current_user: User,
    session: AsyncSession,
) -> QuestionPage:
    if (
        params.difficulty_min is not None
        and params.difficulty_max is not None
        and params.difficulty_min > params.difficulty_max
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最低难度不能大于最高难度",
        )

    return await repository.list_questions(current_user.id, params, session)


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
    cache: CacheBackend,
    message_queue: MessageQueue,
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
    question = await repository.update_question(
        question_id,
        cleaned_payload,
        current_user.id,
        session,
    )
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在",
        )
    await invalidate_dashboard_cache(current_user.id, cache)
    await _publish_question_event(message_queue, "question.updated", current_user, question)
    return question


async def delete_question(
    question_id: int,
    current_user: User,
    session: AsyncSession,
    cache: CacheBackend,
    message_queue: MessageQueue,
) -> None:
    deleted = await repository.delete_question(question_id, current_user.id, session)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在",
        )
    await invalidate_dashboard_cache(current_user.id, cache)
    await _publish_question_event(
        message_queue,
        "question.deleted",
        current_user,
        question_id=question_id,
    )


async def get_category_report(
    current_user: User,
    session: AsyncSession,
) -> list[QuestionCategoryReportRow]:
    return await repository.get_category_report(current_user.id, session)
