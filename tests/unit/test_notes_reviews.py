from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import create_test_client
from tests.unit.test_questions import auth_headers


def create_question(client: TestClient, headers: dict[str, str], title: str = "Question") -> int:
    response = client.post(
        "/api/v1/questions",
        json={
            "title": title,
            "answer": "Answer",
            "category": "backend",
            "difficulty": 2,
            "tags": ["fastapi"],
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_notes_and_reviews_support_basic_crud_and_filters() -> None:
    client = create_test_client()
    headers = auth_headers(client)
    question_id = create_question(client, headers)

    note_response = client.post(
        "/api/v1/notes",
        json={"question_id": question_id, "content": "Remember dependency injection."},
        headers=headers,
    )
    assert note_response.status_code == 201
    note_id = note_response.json()["id"]

    review_response = client.post(
        "/api/v1/reviews",
        json={
            "question_id": question_id,
            "mistake_reason": "Confused Depends with middleware.",
            "status": "todo",
        },
        headers=headers,
    )
    assert review_response.status_code == 201
    review_id = review_response.json()["id"]

    notes_response = client.get(
        "/api/v1/notes",
        params={"question_id": question_id, "keyword": "dependency"},
        headers=headers,
    )
    assert notes_response.status_code == 200
    assert notes_response.json()["total"] == 1

    reviews_response = client.get(
        "/api/v1/reviews",
        params={"question_id": question_id, "status": "todo", "keyword": "Depends"},
        headers=headers,
    )
    assert reviews_response.status_code == 200
    assert reviews_response.json()["total"] == 1

    update_note_response = client.patch(
        f"/api/v1/notes/{note_id}",
        json={"content": "Updated note"},
        headers=headers,
    )
    assert update_note_response.status_code == 200
    assert update_note_response.json()["content"] == "Updated note"

    update_review_response = client.patch(
        f"/api/v1/reviews/{review_id}",
        json={"status": "mastered", "review_count": 1},
        headers=headers,
    )
    assert update_review_response.status_code == 200
    assert update_review_response.json()["status"] == "mastered"
    assert update_review_response.json()["review_count"] == 1


def test_deleting_question_removes_notes_and_reviews() -> None:
    client = create_test_client()
    headers = auth_headers(client)
    question_id = create_question(client, headers)

    assert (
        client.post(
            "/api/v1/notes",
            json={"question_id": question_id, "content": "Question note"},
            headers=headers,
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/reviews",
            json={"question_id": question_id, "mistake_reason": "Wrong answer"},
            headers=headers,
        ).status_code
        == 201
    )

    delete_response = client.delete(f"/api/v1/questions/{question_id}", headers=headers)
    assert delete_response.status_code == 204

    notes_response = client.get("/api/v1/notes", headers=headers)
    reviews_response = client.get("/api/v1/reviews", headers=headers)

    assert notes_response.status_code == 200
    assert notes_response.json()["items"] == []
    assert reviews_response.status_code == 200
    assert reviews_response.json()["items"] == []
