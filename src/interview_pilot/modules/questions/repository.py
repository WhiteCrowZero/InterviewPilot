from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from interview_pilot.modules.questions.models import Question
from interview_pilot.modules.questions.schemas import (
    QuestionCategoryReportRow,
    QuestionCreate,
    QuestionRead,
    QuestionUpdate,
)


async def create_question(
    payload: QuestionCreate,
    user_id: int,
    session: AsyncSession,
) -> QuestionRead:
    question = Question(
        user_id=user_id,
        title=payload.title,
        answer=payload.answer,
        category=payload.category,
        difficulty=payload.difficulty,
        tags=payload.tags,
    )
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return QuestionRead.model_validate(question)


async def list_questions(user_id: int, session: AsyncSession) -> list[QuestionRead]:
    result = await session.execute(
        select(Question).where(Question.user_id == user_id).order_by(Question.id)
    )
    questions = result.scalars().all()
    return [QuestionRead.model_validate(question) for question in questions]


async def get_question(question_id: int, user_id: int, session: AsyncSession) -> QuestionRead | None:
    result = await session.execute(
        select(Question).where(Question.id == question_id, Question.user_id == user_id)
    )
    question = result.scalar_one_or_none()
    if question is None:
        return None
    return QuestionRead.model_validate(question)


async def update_question(
    question_id: int,
    payload: QuestionUpdate,
    user_id: int,
    session: AsyncSession,
) -> QuestionRead | None:
    result = await session.execute(
        select(Question).where(Question.id == question_id, Question.user_id == user_id)
    )
    question = result.scalar_one_or_none()
    if question is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    await session.commit()
    await session.refresh(question)
    return QuestionRead.model_validate(question)


async def delete_question(question_id: int, user_id: int, session: AsyncSession) -> bool:
    result = await session.execute(
        select(Question).where(Question.id == question_id, Question.user_id == user_id)
    )
    question = result.scalar_one_or_none()
    if question is None:
        return False

    await session.delete(question)
    await session.commit()
    return True


async def get_category_report(user_id: int, session: AsyncSession) -> list[QuestionCategoryReportRow]:
    report_sql = text(
        """
        WITH normalized AS (SELECT category,
                                   difficulty,
                                   LENGTH(answer)                              AS answer_length,
                                   created_at,
                                   CASE WHEN difficulty >= 4 THEN 1 ELSE 0 END AS hard_question
                            FROM questions
                            WHERE user_id = :user_id),
             category_summary AS (SELECT category,
                                         COUNT(*)           AS question_count,
                                         AVG(difficulty)    AS avg_difficulty,
                                         AVG(answer_length) AS avg_answer_length,
                                         SUM(hard_question) AS hard_question_count,
                                         MAX(created_at)    AS latest_created_at
                                  FROM normalized
                                  GROUP BY category)
        SELECT category,
               question_count,
               ROUND(avg_difficulty, 2)    AS avg_difficulty,
               ROUND(avg_answer_length, 2) AS avg_answer_length,
               hard_question_count,
               latest_created_at,
               DENSE_RANK()                   OVER (
                ORDER BY question_count DESC, avg_difficulty DESC, category ASC
            ) AS volume_rank
        FROM category_summary
        ORDER BY volume_rank ASC, category ASC
        """
    )
    result = await session.execute(report_sql, {"user_id": user_id})
    rows = result.mappings().all()
    return [QuestionCategoryReportRow.model_validate(row) for row in rows]
