from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX
from tests.helpers import auth_headers, create_note, create_question, create_review


def test_dashboard_summary_requires_login(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/dashboard/summary")

    assert response.status_code == 401


def test_dashboard_summary_counts_current_user_data(client: TestClient) -> None:
    alice_headers = auth_headers(client)
    bob_headers = auth_headers(client, username="bob", email="bob@example.com")

    alice_question = create_question(client, alice_headers, category="backend")
    create_note(client, alice_headers, question_id=alice_question["id"])
    create_review(client, alice_headers, question_id=alice_question["id"], status="reviewing")

    bob_question = create_question(client, bob_headers, category="database")
    create_review(client, bob_headers, question_id=bob_question["id"], status="mastered")

    response = client.get(f"{API_PREFIX}/dashboard/summary", headers=alice_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["question_count"] == 1
    assert body["note_count"] == 1
    assert body["review_count"] == 1
    assert body["todo_review_count"] == 0
    assert body["reviewing_review_count"] == 1
    assert body["mastered_review_count"] == 0
    assert body["category_distribution"] == [{"category": "backend", "count": 1}]


def test_dashboard_cache_is_invalidated_after_question_write(client: TestClient) -> None:
    headers = auth_headers(client)

    first_response = client.get(f"{API_PREFIX}/dashboard/summary", headers=headers)
    assert first_response.status_code == 200
    assert first_response.json()["question_count"] == 0

    create_question(client, headers, category="redis")

    second_response = client.get(f"{API_PREFIX}/dashboard/summary", headers=headers)
    assert second_response.status_code == 200
    assert second_response.json()["question_count"] == 1
    assert second_response.json()["category_distribution"] == [{"category": "redis", "count": 1}]


def test_deleting_question_cascades_notes_reviews_and_updates_dashboard(client: TestClient) -> None:
    headers = auth_headers(client)
    question = create_question(client, headers)
    create_note(client, headers, question_id=question["id"])
    create_review(client, headers, question_id=question["id"])

    before_delete = client.get(f"{API_PREFIX}/dashboard/summary", headers=headers)
    assert before_delete.status_code == 200
    assert before_delete.json()["question_count"] == 1
    assert before_delete.json()["note_count"] == 1
    assert before_delete.json()["review_count"] == 1

    delete_response = client.delete(f"{API_PREFIX}/questions/{question['id']}", headers=headers)
    assert delete_response.status_code == 204

    after_delete = client.get(f"{API_PREFIX}/dashboard/summary", headers=headers)
    assert after_delete.status_code == 200
    assert after_delete.json()["question_count"] == 0
    assert after_delete.json()["note_count"] == 0
    assert after_delete.json()["review_count"] == 0
