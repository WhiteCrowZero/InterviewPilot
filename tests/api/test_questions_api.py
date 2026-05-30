from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX
from tests.helpers import auth_headers, consume_one_event, create_question


def test_questions_require_login(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/questions")

    assert response.status_code == 401


def test_create_question_trims_input_and_publishes_event(client: TestClient) -> None:
    headers = auth_headers(client)

    response = client.post(
        f"{API_PREFIX}/questions",
        json={
            "title": "  What is a database transaction?  ",
            "answer": "  A group of operations that either all succeed or all fail.  ",
            "category": "database",
            "difficulty": 2,
            "tags": ["sql", "transaction"],
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "What is a database transaction?"
    assert body["answer"] == "A group of operations that either all succeed or all fail."
    assert body["user_id"] == 1

    event = consume_one_event()
    assert event is not None
    assert event.event_type == "question.created"
    assert event.user_id == body["user_id"]
    assert event.payload["question_id"] == body["id"]


def test_create_question_rejects_blank_title_after_strip(client: TestClient) -> None:
    headers = auth_headers(client)

    response = client.post(
        f"{API_PREFIX}/questions",
        json={
            "title": "   ",
            "answer": "Valid answer",
            "category": "backend",
            "difficulty": 1,
            "tags": [],
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "题目标题不能为空"


def test_get_update_delete_question_basic_crud(client: TestClient) -> None:
    headers = auth_headers(client)
    question = create_question(client, headers)
    question_id = question["id"]

    get_response = client.get(f"{API_PREFIX}/questions/{question_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["title"] == question["title"]

    update_response = client.patch(
        f"{API_PREFIX}/questions/{question_id}",
        json={"title": "What is FastAPI Depends?", "difficulty": 3},
        headers=headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "What is FastAPI Depends?"
    assert updated["answer"] == question["answer"]
    assert updated["difficulty"] == 3

    delete_response = client.delete(f"{API_PREFIX}/questions/{question_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = client.get(f"{API_PREFIX}/questions/{question_id}", headers=headers)
    assert missing_response.status_code == 404


def test_list_questions_supports_pagination_and_filters(client: TestClient) -> None:
    headers = auth_headers(client)
    create_question(
        client,
        headers,
        title="Database transaction",
        answer="Atomic database operation.",
        category="database",
        difficulty=2,
        tags=["sql"],
    )
    create_question(
        client,
        headers,
        title="Database index",
        answer="Speeds up database lookups.",
        category="database",
        difficulty=4,
        tags=["sql"],
    )
    create_question(
        client,
        headers,
        title="FastAPI dependency",
        answer="Injects request dependencies.",
        category="backend",
        difficulty=3,
        tags=["fastapi"],
    )

    response = client.get(
        f"{API_PREFIX}/questions",
        params={"category": "database", "difficulty_min": 3, "page": 1, "size": 1},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Database index"

    keyword_response = client.get(
        f"{API_PREFIX}/questions",
        params={"keyword": "dependency"},
        headers=headers,
    )
    assert keyword_response.status_code == 200
    assert keyword_response.json()["total"] == 1
    assert keyword_response.json()["items"][0]["category"] == "backend"


def test_list_questions_rejects_invalid_difficulty_range(client: TestClient) -> None:
    headers = auth_headers(client)

    response = client.get(
        f"{API_PREFIX}/questions",
        params={"difficulty_min": 5, "difficulty_max": 1},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "最低难度不能大于最高难度"


def test_user_can_only_access_own_questions(client: TestClient) -> None:
    alice_headers = auth_headers(client)
    bob_headers = auth_headers(client, username="bob", email="bob@example.com")
    question = create_question(client, alice_headers, title="Alice private question")

    list_response = client.get(f"{API_PREFIX}/questions", headers=bob_headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []

    detail_response = client.get(f"{API_PREFIX}/questions/{question['id']}", headers=bob_headers)
    assert detail_response.status_code == 404

    delete_response = client.delete(f"{API_PREFIX}/questions/{question['id']}", headers=bob_headers)
    assert delete_response.status_code == 404

    owner_response = client.get(f"{API_PREFIX}/questions/{question['id']}", headers=alice_headers)
    assert owner_response.status_code == 200


def test_category_summary_report_aggregates_only_current_user_data(client: TestClient) -> None:
    alice_headers = auth_headers(client)
    bob_headers = auth_headers(client, username="bob", email="bob@example.com")

    create_question(client, alice_headers, category="database", difficulty=4)
    create_question(
        client,
        alice_headers,
        title="Covering index",
        category="database",
        difficulty=3,
    )
    create_question(client, alice_headers, title="Depends", category="backend", difficulty=2)
    create_question(client, bob_headers, title="Bob's Redis", category="redis", difficulty=5)

    response = client.get(f"{API_PREFIX}/questions/reports/category-summary", headers=alice_headers)

    assert response.status_code == 200
    rows = response.json()
    assert [row["category"] for row in rows] == ["database", "backend"]
    assert rows[0]["question_count"] == 2
    assert rows[0]["hard_question_count"] == 1
