from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from interview_pilot.api.deps import get_current_user
from interview_pilot.modules.auth.models import User
from interview_pilot.modules.auth.schemas import UserRead

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
