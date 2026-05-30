from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from starlette import status

from interview_pilot.api.deps import CacheDep, CurrentActiveUserDep, DbSessionDep, MessageQueueDep
from interview_pilot.modules.reviews import service
from interview_pilot.modules.reviews.schemas import (
    ReviewCreate,
    ReviewListParams,
    ReviewPage,
    ReviewRead,
    ReviewStatus,
    ReviewUpdate,
)

router = APIRouter()


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
    message_queue: MessageQueueDep,
) -> ReviewRead:
    return await service.create_review(payload, current_user, session, cache, message_queue)


@router.get("", response_model=ReviewPage)
async def list_reviews(
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    question_id: Annotated[int | None, Query(ge=1)] = None,
    status: ReviewStatus | None = None,
    keyword: str | None = None,
) -> ReviewPage:
    params = ReviewListParams(
        page=page,
        size=size,
        question_id=question_id,
        status=status,
        keyword=keyword,
    )
    return await service.list_reviews(params, current_user, session)


@router.get("/{review_id}", response_model=ReviewRead)
async def get_review(
    review_id: int,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
) -> ReviewRead:
    return await service.get_review(review_id, current_user, session)


@router.patch("/{review_id}", response_model=ReviewRead)
async def update_review(
    review_id: int,
    payload: ReviewUpdate,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
    message_queue: MessageQueueDep,
) -> ReviewRead:
    return await service.update_review(
        review_id, payload, current_user, session, cache, message_queue
    )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
    message_queue: MessageQueueDep,
) -> None:
    await service.delete_review(review_id, current_user, session, cache, message_queue)
