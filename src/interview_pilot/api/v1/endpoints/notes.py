from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from starlette import status

from interview_pilot.api.deps import CacheDep, CurrentActiveUserDep, DbSessionDep, MessageQueueDep
from interview_pilot.modules.notes import service
from interview_pilot.modules.notes.schemas import (
    NoteCreate,
    NoteListParams,
    NotePage,
    NoteRead,
    NoteUpdate,
)

router = APIRouter()


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
    message_queue: MessageQueueDep,
) -> NoteRead:
    return await service.create_note(payload, current_user, session, cache, message_queue)


@router.get("", response_model=NotePage)
async def list_notes(
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    question_id: Annotated[int | None, Query(ge=1)] = None,
    keyword: str | None = None,
) -> NotePage:
    params = NoteListParams(page=page, size=size, question_id=question_id, keyword=keyword)
    return await service.list_notes(params, current_user, session)


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: int,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
) -> NoteRead:
    return await service.get_note(note_id, current_user, session)


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: int,
    payload: NoteUpdate,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
    message_queue: MessageQueueDep,
) -> NoteRead:
    return await service.update_note(note_id, payload, current_user, session, cache, message_queue)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
    message_queue: MessageQueueDep,
) -> None:
    await service.delete_note(note_id, current_user, session, cache, message_queue)
