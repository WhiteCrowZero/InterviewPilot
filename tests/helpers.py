from __future__ import annotations

import asyncio
from typing import Any

from fastapi.testclient import TestClient

from interview_pilot.core.message_queue import DomainEvent, get_message_queue
from tests.conftest import API_PREFIX

DEFAULT_PASSWORD = "strong-password"


def register_user(
    client: TestClient,
    *,
    username: str = "alice",
    email: str = "alice@example.com",
    password: str = DEFAULT_PASSWORD,
) -> dict[str, Any]:
    response = client.post(
        f"{API_PREFIX}/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login_user(
    client: TestClient,
    *,
    username: str = "alice",
    password: str = DEFAULT_PASSWORD,
) -> str:
    response = client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(
    client: TestClient,
    *,
    username: str = "alice",
    email: str = "alice@example.com",
    password: str = DEFAULT_PASSWORD,
) -> dict[str, str]:
    register_user(client, username=username, email=email, password=password)
    token = login_user(client, username=username, password=password)
    return {"Authorization": f"Bearer {token}"}


def bearer_token(headers: dict[str, str]) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


def create_question(
    client: TestClient,
    headers: dict[str, str],
    *,
    title: str = "What is FastAPI dependency injection?",
    answer: str = "It provides dependencies from outside the endpoint function.",
    category: str = "backend",
    difficulty: int = 2,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    response = client.post(
        f"{API_PREFIX}/questions",
        json={
            "title": title,
            "answer": answer,
            "category": category,
            "difficulty": difficulty,
            "tags": tags or ["fastapi"],
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_note(
    client: TestClient,
    headers: dict[str, str],
    *,
    question_id: int,
    content: str = "Remember to test the permission boundary.",
) -> dict[str, Any]:
    response = client.post(
        f"{API_PREFIX}/notes",
        json={"question_id": question_id, "content": content},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_review(
    client: TestClient,
    headers: dict[str, str],
    *,
    question_id: int,
    mistake_reason: str = "I confused dependency injection with global variables.",
    status: str = "todo",
) -> dict[str, Any]:
    response = client.post(
        f"{API_PREFIX}/reviews",
        json={
            "question_id": question_id,
            "mistake_reason": mistake_reason,
            "status": status,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def consume_one_event(timeout_seconds: int = 1) -> DomainEvent | None:
    return asyncio.run(get_message_queue().consume(timeout_seconds=timeout_seconds))
