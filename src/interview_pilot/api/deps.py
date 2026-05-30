from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from interview_pilot.core.cache import CacheBackend, get_cache_backend
from interview_pilot.core.message_queue import MessageQueue, get_message_queue
from interview_pilot.core.security import decode_access_token
from interview_pilot.db.session import get_db_session
from interview_pilot.modules.auth import repository as auth_repository
from interview_pilot.modules.auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_session() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_cache() -> CacheBackend:
    return get_cache_backend()


def get_event_queue() -> MessageQueue:
    return get_message_queue()


CacheDep = Annotated[CacheBackend, Depends(get_cache)]
MessageQueueDep = Annotated[MessageQueue, Depends(get_event_queue)]


async def get_current_user(token: TokenDep, session: DbSessionDep) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证登录状态",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = int(subject)
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception from None

    user = await auth_repository.get_user_by_id(user_id, session)
    if user is None:
        raise credentials_exception
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUserDep) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )
    return current_user


CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]
