from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import create_test_client


def auth_headers(client: TestClient, username: str = "alice", email: str = "alice@example.com") -> dict[str, str]:
    password = "strong-password"
    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_create_and_list_questions() -> None:
    client = create_test_client()
    headers = auth_headers(client)

    payload = {
        "title": "What is a database transaction?",
        "answer": "A group of operations that either all succeed or all fail.",
        "category": "database",
        "difficulty": 2,
        "tags": ["sql", "transaction"],
    }

    create_response = client.post("/api/v1/questions", json=payload, headers=headers)

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == 1
    assert created["user_id"] == 1
    assert created["title"] == payload["title"]
    assert created["tags"] == payload["tags"]

    list_response = client.get("/api/v1/questions", headers=headers)

    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]
    assert listed[0]["title"] == payload["title"]


def test_get_update_and_delete_question() -> None:
    client = create_test_client()
    headers = auth_headers(client)

    payload = {
        "title": "What is dependency injection?",
        "answer": "A way to provide dependencies from outside the object.",
        "category": "backend",
        "difficulty": 2,
        "tags": ["fastapi"],
    }
    create_response = client.post("/api/v1/questions", json=payload, headers=headers)
    assert create_response.status_code == 201
    question_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/questions/{question_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["title"] == payload["title"]

    update_response = client.patch(
        f"/api/v1/questions/{question_id}",
        json={
            "title": "What is FastAPI Depends?",
            "difficulty": 3,
            "tags": ["fastapi", "dependency"],
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "What is FastAPI Depends?"
    assert updated["answer"] == payload["answer"]
    assert updated["difficulty"] == 3
    assert updated["tags"] == ["fastapi", "dependency"]

    delete_response = client.delete(f"/api/v1/questions/{question_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/questions/{question_id}", headers=headers)
    assert missing_response.status_code == 404


def test_question_detail_returns_404_when_missing() -> None:
    client = create_test_client()
    headers = auth_headers(client)

    response = client.get("/api/v1/questions/999", headers=headers)

    assert response.status_code == 404


def test_questions_require_login() -> None:
    client = create_test_client()

    response = client.get("/api/v1/questions")

    assert response.status_code == 401


def test_user_can_only_access_own_questions() -> None:
    client = create_test_client()
    alice_headers = auth_headers(client)
    bob_headers = auth_headers(client, username="bob", email="bob@example.com")

    create_response = client.post(
        "/api/v1/questions",
        json={
            "title": "Private question",
            "answer": "Private answer",
            "category": "backend",
            "difficulty": 2,
            "tags": ["fastapi"],
        },
        headers=alice_headers,
    )
    assert create_response.status_code == 201
    question_id = create_response.json()["id"]

    list_response = client.get("/api/v1/questions", headers=bob_headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    detail_response = client.get(f"/api/v1/questions/{question_id}", headers=bob_headers)
    assert detail_response.status_code == 404

    delete_response = client.delete(f"/api/v1/questions/{question_id}", headers=bob_headers)
    assert delete_response.status_code == 404

    owner_detail_response = client.get(f"/api/v1/questions/{question_id}", headers=alice_headers)
    assert owner_detail_response.status_code == 200


def test_category_summary_report_uses_raw_sql() -> None:
    client = create_test_client()
    headers = auth_headers(client)

    payloads = [
        {
            "title": "What are transaction isolation levels?",
            "answer": "Read uncommitted, read committed, repeatable read, and serializable.",
            "category": "database",
            "difficulty": 4,
            "tags": ["sql"],
        },
        {
            "title": "What is a covering index?",
            "answer": "An index that contains all columns required by a query.",
            "category": "database",
            "difficulty": 3,
            "tags": ["sql", "index"],
        },
        {
            "title": "What does FastAPI Depends do?",
            "answer": "It declares dependencies for FastAPI to resolve during request handling.",
            "category": "backend",
            "difficulty": 2,
            "tags": ["fastapi"],
        },
    ]

    for payload in payloads:
        response = client.post("/api/v1/questions", json=payload, headers=headers)
        assert response.status_code == 201

    report_response = client.get("/api/v1/questions/reports/category-summary", headers=headers)

    assert report_response.status_code == 200
    rows = report_response.json()
    assert len(rows) == 2

    database_row = rows[0]
    assert database_row["category"] == "database"
    assert database_row["question_count"] == 2
    assert database_row["hard_question_count"] == 1
    assert database_row["volume_rank"] == 1

    backend_row = rows[1]
    assert backend_row["category"] == "backend"
    assert backend_row["question_count"] == 1
    assert backend_row["volume_rank"] == 2
