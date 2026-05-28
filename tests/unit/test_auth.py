from tests.conftest import create_test_client


REGISTER_PAYLOAD = {
    "username": "alice",
    "email": "alice@example.com",
    "password": "strong-password",
}


def test_register_user() -> None:
    client = create_test_client()

    response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["username"] == REGISTER_PAYLOAD["username"]
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_invalid_email() -> None:
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/register",
        json={**REGISTER_PAYLOAD, "email": "not-an-email"},
    )

    assert response.status_code == 422


def test_register_rejects_duplicate_username() -> None:
    client = create_test_client()
    assert client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD).status_code == 201

    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": REGISTER_PAYLOAD["username"],
            "email": "another@example.com",
            "password": "strong-password",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "用户名已存在"


def test_login_returns_access_token() -> None:
    client = create_test_client()
    assert client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD).status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": REGISTER_PAYLOAD["username"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 20


def test_login_rejects_wrong_password() -> None:
    client = create_test_client()
    assert client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD).status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        data={"username": REGISTER_PAYLOAD["username"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


def test_read_current_user_with_bearer_token() -> None:
    client = create_test_client()
    assert client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD).status_code == 201
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == REGISTER_PAYLOAD["username"]
    assert body["email"] == REGISTER_PAYLOAD["email"]


def test_read_current_user_requires_token() -> None:
    client = create_test_client()

    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
