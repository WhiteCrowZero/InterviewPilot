from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from interview_pilot.api.deps import get_session
from interview_pilot.modules.auth import service
from interview_pilot.modules.auth.schemas import Token, UserCreate, UserRead

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_session)]
LoginForm = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: DbSession) -> UserRead:
    return await service.register_user(payload, session)


@router.post("/login", response_model=Token)
async def login_user(form_data: LoginForm, session: DbSession) -> Token:
    return await service.login_user(form_data.username, form_data.password, session)
