from datetime import datetime

from modules.questions.schemas import QuestionCreate, QuestionRead

_next_id: int = 0
_questions: dict[int, QuestionRead] = {}


async def create_question(payload: QuestionCreate) -> QuestionRead:
    global _next_id

    now = datetime.now()

    question = QuestionRead(
        id=_next_id,
        title=payload.title,
        answer=payload.answer,
        category=payload.category,
        difficulty=payload.difficulty,
        tags=payload.tags,
        created_at=now,
        updated_at=now,
    )

    _questions[_next_id] = question
    _next_id += 1

    return question
