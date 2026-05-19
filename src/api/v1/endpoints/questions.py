from fastapi import APIRouter
from starlette import status

from modules.questions import service
from modules.questions.schemas import QuestionRead, QuestionCreate

router = APIRouter()


@router.post(
    "",
    response_model=QuestionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(payload: QuestionCreate) -> QuestionRead:
    return await service.create_question(payload)
