from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX
from tests.helpers import DEFAULT_PASSWORD, auth_headers, register_user

REGISTER_PAYLOAD = {
    "username": "alice",
    "email": "alice@example.com",
    "password": DEFAULT_PASSWORD,
}


def test_register_user_returns_public_user_fields(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_invalid_email(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/auth/register",
        json={**REGISTER_PAYLOAD, "email": "not-an-email"},
    )

    assert response.status_code == 422


def test_register_rejects_duplicate_username(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "username": "alice",
            "email": "another@example.com",
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "用户名已存在"


def test_register_rejects_duplicate_email_even_with_different_username(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "username": "alice2",
            "email": "alice@example.com",
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "邮箱已存在"


def test_login_returns_bearer_access_token(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": "alice", "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 20


def test_login_accepts_email_as_identity(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": "alice@example.com", "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_login_rejects_wrong_password(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


def test_read_current_user_requires_token(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/users/me")

    assert response.status_code == 401


def test_read_current_user_with_token(client: TestClient) -> None:
    headers = auth_headers(client)

    response = client.get(f"{API_PREFIX}/users/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
