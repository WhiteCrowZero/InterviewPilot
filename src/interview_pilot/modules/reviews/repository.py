from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_pilot.modules.reviews.models import Review
from interview_pilot.modules.reviews.schemas import (
    ReviewCreate,
    ReviewListParams,
    ReviewPage,
    ReviewRead,
    ReviewUpdate,
)


async def create_review(payload: ReviewCreate, user_id: int, session: AsyncSession) -> ReviewRead:
    review = Review(
        user_id=user_id,
        question_id=payload.question_id,
        status=payload.status,
        mistake_reason=payload.mistake_reason,
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)
    return ReviewRead.model_validate(review)


async def list_reviews(user_id: int, params: ReviewListParams, session: AsyncSession) -> ReviewPage:
    conditions = [Review.user_id == user_id]
    if params.question_id is not None:
        conditions.append(Review.question_id == params.question_id)
    if params.status is not None:
        conditions.append(Review.status == params.status)
    if params.keyword:
        conditions.append(Review.mistake_reason.ilike(f"%{params.keyword}%"))

    total_result = await session.execute(
        select(func.count()).select_from(Review).where(*conditions)
    )
    total = total_result.scalar_one()
    result = await session.execute(
        select(Review)
        .where(*conditions)
        .order_by(Review.id.desc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    reviews = result.scalars().all()
    return ReviewPage(
        items=[ReviewRead.model_validate(review) for review in reviews],
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size,
    )


async def get_review(review_id: int, user_id: int, session: AsyncSession) -> ReviewRead | None:
    result = await session.execute(
        select(Review).where(Review.id == review_id, Review.user_id == user_id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        return None
    return ReviewRead.model_validate(review)


async def update_review(
    review_id: int,
    payload: ReviewUpdate,
    user_id: int,
    session: AsyncSession,
) -> ReviewRead | None:
    result = await session.execute(
        select(Review).where(Review.id == review_id, Review.user_id == user_id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    await session.commit()
    await session.refresh(review)
    return ReviewRead.model_validate(review)


async def delete_review(review_id: int, user_id: int, session: AsyncSession) -> bool:
    result = await session.execute(
        select(Review).where(Review.id == review_id, Review.user_id == user_id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        return False

    await session.delete(review)
    await session.commit()
    return True
