from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_pilot.modules.auth.models import User


async def get_user_by_id(user_id: int, session: AsyncSession) -> User | None:
    return await session.get(User, user_id)


async def get_user_by_username(username: str, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(email: str, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username_or_email(identity: str, session: AsyncSession) -> User | None:
    result = await session.execute(
        select(User).where(or_(User.username == identity, User.email == identity))
    )
    return result.scalar_one_or_none()


async def create_user(
    *,
    username: str,
    email: str,
    hashed_password: str,
    session: AsyncSession,
) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
