from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from interview_pilot.core.security import create_access_token, hash_password, verify_password
from interview_pilot.modules.auth import repository
from interview_pilot.modules.auth.models import User
from interview_pilot.modules.auth.schemas import Token, UserCreate, UserRead


async def register_user(payload: UserCreate, session: AsyncSession) -> UserRead:
    username = payload.username.strip()
    email = payload.email.strip().lower()

    if await repository.get_user_by_username(username, session) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )

    if await repository.get_user_by_email(email, session) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已存在",
        )

    user = await repository.create_user(
        username=username,
        email=email,
        hashed_password=hash_password(payload.password),
        session=session,
    )
    return UserRead.model_validate(user)


def ensure_user_can_login(user: User) -> None:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )


async def authenticate_user(
        identity: str,
        password: str,
        session: AsyncSession,
) -> User | None:
    user = await repository.get_user_by_username_or_email(identity.strip(), session)

    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def login_user(identity: str, password: str, session: AsyncSession) -> Token:
    user = await authenticate_user(identity, password, session)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ensure_user_can_login(user)

    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)
