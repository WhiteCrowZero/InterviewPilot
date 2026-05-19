from fastapi import HTTPException
from starlette import status

from modules.questions import crud
from modules.questions.schemas import QuestionCreate, QuestionRead


async def create_question(payload: QuestionCreate) -> QuestionRead:
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

    return await crud.create_question(cleaned_payload)