from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_pilot.modules.notes.models import Note
from interview_pilot.modules.notes.schemas import (
    NoteCreate,
    NoteListParams,
    NotePage,
    NoteRead,
    NoteUpdate,
)


async def create_note(payload: NoteCreate, user_id: int, session: AsyncSession) -> NoteRead:
    note = Note(
        user_id=user_id,
        question_id=payload.question_id,
        content=payload.content,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return NoteRead.model_validate(note)


async def list_notes(user_id: int, params: NoteListParams, session: AsyncSession) -> NotePage:
    conditions = [Note.user_id == user_id]
    if params.question_id is not None:
        conditions.append(Note.question_id == params.question_id)
    if params.keyword:
        conditions.append(Note.content.ilike(f"%{params.keyword}%"))

    total_result = await session.execute(select(func.count()).select_from(Note).where(*conditions))
    total = total_result.scalar_one()
    result = await session.execute(
        select(Note)
        .where(*conditions)
        .order_by(Note.id.desc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    notes = result.scalars().all()
    return NotePage(
        items=[NoteRead.model_validate(note) for note in notes],
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size,
    )


async def get_note(note_id: int, user_id: int, session: AsyncSession) -> NoteRead | None:
    result = await session.execute(select(Note).where(Note.id == note_id, Note.user_id == user_id))
    note = result.scalar_one_or_none()
    if note is None:
        return None
    return NoteRead.model_validate(note)


async def update_note(
    note_id: int,
    payload: NoteUpdate,
    user_id: int,
    session: AsyncSession,
) -> NoteRead | None:
    result = await session.execute(select(Note).where(Note.id == note_id, Note.user_id == user_id))
    note = result.scalar_one_or_none()
    if note is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    await session.commit()
    await session.refresh(note)
    return NoteRead.model_validate(note)


async def delete_note(note_id: int, user_id: int, session: AsyncSession) -> bool:
    result = await session.execute(select(Note).where(Note.id == note_id, Note.user_id == user_id))
    note = result.scalar_one_or_none()
    if note is None:
        return False

    await session.delete(note)
    await session.commit()
    return True
