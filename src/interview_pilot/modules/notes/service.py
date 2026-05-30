from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from interview_pilot.core.cache import CacheBackend
from interview_pilot.core.message_queue import DomainEvent, MessageQueue
from interview_pilot.modules.auth.models import User
from interview_pilot.modules.dashboard.service import invalidate_dashboard_cache
from interview_pilot.modules.notes import repository
from interview_pilot.modules.notes.schemas import (
    NoteCreate,
    NoteListParams,
    NotePage,
    NoteRead,
    NoteUpdate,
)
from interview_pilot.modules.questions import repository as question_repository


async def _publish_note_event(
    message_queue: MessageQueue,
    event_type: str,
    current_user: User,
    note: NoteRead | None = None,
    note_id: int | None = None,
) -> None:
    await message_queue.publish(
        DomainEvent(
            event_type=event_type,
            user_id=current_user.id,
            payload={
                "note_id": note.id if note is not None else note_id,
                "question_id": note.question_id if note is not None else None,
            },
        )
    )


async def create_note(
    payload: NoteCreate,
    current_user: User,
    session: AsyncSession,
    cache: CacheBackend,
    message_queue: MessageQueue,
) -> NoteRead:
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="笔记内容不能为空")

    # 学习重点：外键只能保证 question 存在，不能保证 question 属于当前用户。
    # 所以必须带 current_user.id 查询，防止用户给别人的题目创建笔记。
    question = await question_repository.get_question(payload.question_id, current_user.id, session)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

    note = await repository.create_note(
        NoteCreate(question_id=payload.question_id, content=content),
        current_user.id,
        session,
    )
    await invalidate_dashboard_cache(current_user.id, cache)
    await _publish_note_event(message_queue, "note.created", current_user, note)
    return note


async def list_notes(
    params: NoteListParams,
    current_user: User,
    session: AsyncSession,
) -> NotePage:
    return await repository.list_notes(current_user.id, params, session)


async def get_note(note_id: int, current_user: User, session: AsyncSession) -> NoteRead:
    note = await repository.get_note(note_id, current_user.id, session)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="笔记不存在")
    return note


async def update_note(
    note_id: int,
    payload: NoteUpdate,
    current_user: User,
    session: AsyncSession,
    cache: CacheBackend,
    message_queue: MessageQueue,
) -> NoteRead:
    update_data = payload.model_dump(exclude_unset=True)
    if "content" in update_data:
        content = payload.content.strip() if payload.content is not None else ""
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="笔记内容不能为空")
        update_data["content"] = content

    note = await repository.update_note(
        note_id,
        NoteUpdate(**update_data),
        current_user.id,
        session,
    )
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="笔记不存在")
    await invalidate_dashboard_cache(current_user.id, cache)
    await _publish_note_event(message_queue, "note.updated", current_user, note)
    return note


async def delete_note(
    note_id: int,
    current_user: User,
    session: AsyncSession,
    cache: CacheBackend,
    message_queue: MessageQueue,
) -> None:
    deleted = await repository.delete_note(note_id, current_user.id, session)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="笔记不存在")
    await invalidate_dashboard_cache(current_user.id, cache)
    await _publish_note_event(message_queue, "note.deleted", current_user, note_id=note_id)
