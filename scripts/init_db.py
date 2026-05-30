from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import interview_pilot.db.models  # noqa: E402,F401
from interview_pilot.core.config import settings  # noqa: E402
from interview_pilot.core.security import hash_password  # noqa: E402
from interview_pilot.db.base import Base  # noqa: E402
from interview_pilot.modules.auth.models import User  # noqa: E402
from interview_pilot.modules.questions.models import Question  # noqa: E402

SEED_USERS = [
    {
        "username": "alice",
        "email": "alice@example.com",
        "password": "strong-password",
    },
    {
        "username": "bob",
        "email": "bob@example.com",
        "password": "strong-password",
    },
]

SEED_QUESTIONS = [
    {
        "owner": "alice",
        "title": "What is a database transaction?",
        "answer": "A transaction is a group of operations that either all succeed or all fail.",
        "category": "database",
        "difficulty": 2,
        "tags": ["sql", "transaction"],
    },
    {
        "owner": "alice",
        "title": "What does FastAPI Depends do?",
        "answer": "It declares dependencies for FastAPI to resolve during request handling.",
        "category": "backend",
        "difficulty": 2,
        "tags": ["fastapi"],
    },
    {
        "owner": "bob",
        "title": "What is a covering index?",
        "answer": "A covering index contains all columns required by a query.",
        "category": "database",
        "difficulty": 3,
        "tags": ["sql", "index"],
    },
]


async def ensure_user(session: AsyncSession, username: str, email: str, password: str) -> User:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )
    session.add(user)
    await session.flush()
    return user


async def ensure_question(
    session: AsyncSession,
    *,
    owner: User,
    title: str,
    answer: str,
    category: str,
    difficulty: int,
    tags: list[str],
) -> Question:
    result = await session.execute(
        select(Question).where(Question.user_id == owner.id, Question.title == title)
    )
    question = result.scalar_one_or_none()
    if question is not None:
        return question

    question = Question(
        user_id=owner.id,
        title=title,
        answer=answer,
        category=category,
        difficulty=difficulty,
        tags=tags,
    )
    session.add(question)
    await session.flush()
    return question


async def init_database(reset: bool) -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        if reset:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        users_by_name: dict[str, User] = {}
        for seed_user in SEED_USERS:
            user = await ensure_user(session, **seed_user)
            users_by_name[user.username] = user

        for seed_question in SEED_QUESTIONS:
            owner_name = seed_question["owner"]
            await ensure_question(
                session,
                owner=users_by_name[owner_name],
                title=seed_question["title"],
                answer=seed_question["answer"],
                category=seed_question["category"],
                difficulty=seed_question["difficulty"],
                tags=seed_question["tags"],
            )

        await session.commit()

    await engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize the development database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables before creating them and inserting seed data.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(init_database(reset=args.reset))
    print(f"Database initialized: {settings.database_url}")


if __name__ == "__main__":
    main()
