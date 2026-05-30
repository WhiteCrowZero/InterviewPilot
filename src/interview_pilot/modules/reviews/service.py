from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from interview_pilot.core.cache import CacheBackend
from interview_pilot.core.message_queue import DomainEvent, MessageQueue
from interview_pilot.modules.auth.models import User
from interview_pilot.modules.dashboard.service import invalidate_dashboard_cache
from interview_pilot.modules.questions import repository as question_repository
from interview_pilot.modules.reviews import repository
from interview_pilot.modules.reviews.schemas import (
    ReviewCreate,
    ReviewListParams,
    ReviewPage,
    ReviewRead,
    ReviewUpdate,
)


async def _publish_review_event(
    message_queue: MessageQueue,
    event_type: str,
    current_user: User,
    review: ReviewRead | None = None,
    review_id: int | None = None,
) -> None:
    await message_queue.publish(
        DomainEvent(
            event_type=event_type,
            user_id=current_user.id,
            payload={
                "review_id": review.id if review is not None else review_id,
                "question_id": review.question_id if review is not None else None,
                "status": review.status if review is not None else None,
            },
        )
    )


async def create_review(
    payload: ReviewCreate,
    current_user: User,
    session: AsyncSession,
    cache: CacheBackend,
    message_queue: MessageQueue,
) -> ReviewRead:
    mistake_reason = payload.mistake_reason.strip()
    if not mistake_reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="错题原因不能为空")

    # 学习重点：这里检查的是权限边界，不只是外键存在性。
    question = await question_repository.get_question(payload.question_id, current_user.id, session)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

    review = await repository.create_review(
        ReviewCreate(
            question_id=payload.question_id,
            mistake_reason=mistake_reason,
            status=payload.status,
        ),
        current_user.id,
        session,
    )
    await invalidate_dashboard_cache(current_user.id, cache)
    await _publish_review_event(message_queue, "review.created", current_user, review)
    return review


async def list_reviews(
    params: ReviewListParams,
    current_user: User,
    session: AsyncSession,
) -> ReviewPage:
    return await repository.list_reviews(current_user.id, params, session)


async def get_review(review_id: int, current_user: User, session: AsyncSession) -> ReviewRead:
    review = await repository.get_review(review_id, current_user.id, session)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题记录不存在")
    return review


async def update_review(
    review_id: int,
    payload: ReviewUpdate,
    current_user: User,
    session: AsyncSession,
    cache: CacheBackend,
    message_queue: MessageQueue,
) -> ReviewRead:
    update_data = payload.model_dump(exclude_unset=True)
    if "mistake_reason" in update_data:
        mistake_reason = (
            payload.mistake_reason.strip() if payload.mistake_reason is not None else ""
        )
        if not mistake_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="错题原因不能为空")
        update_data["mistake_reason"] = mistake_reason

    review = await repository.update_review(
        review_id,
        ReviewUpdate(**update_data),
        current_user.id,
        session,
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题记录不存在")
    await invalidate_dashboard_cache(current_user.id, cache)
    await _publish_review_event(message_queue, "review.updated", current_user, review)
    return review


async def delete_review(
    review_id: int,
    current_user: User,
    session: AsyncSession,
    cache: CacheBackend,
    message_queue: MessageQueue,
) -> None:
    deleted = await repository.delete_review(review_id, current_user.id, session)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题记录不存在")
    await invalidate_dashboard_cache(current_user.id, cache)
    await _publish_review_event(message_queue, "review.deleted", current_user, review_id=review_id)
