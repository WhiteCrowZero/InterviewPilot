from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX
from tests.helpers import auth_headers, consume_one_event, create_question, create_review


def test_create_review_requires_existing_owned_question(client: TestClient) -> None:
    alice_headers = auth_headers(client)
    bob_headers = auth_headers(client, username="bob", email="bob@example.com")
    alice_question = create_question(client, alice_headers)

    response = client.post(
        f"{API_PREFIX}/reviews",
        json={"question_id": alice_question["id"], "mistake_reason": "Not mine"},
        headers=bob_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "题目不存在"


def test_create_review_trims_reason_and_publishes_event(client: TestClient) -> None:
    headers = auth_headers(client)
    question = create_question(client, headers)
    consume_one_event()  # question.created，本测试只关心 review.created

    response = client.post(
        f"{API_PREFIX}/reviews",
        json={"question_id": question["id"], "mistake_reason": "  Missed edge cases  "},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["mistake_reason"] == "Missed edge cases"
    assert body["status"] == "todo"
    assert body["review_count"] == 0

    event = consume_one_event()
    assert event is not None
    assert event.event_type == "review.created"
    assert event.payload["review_id"] == body["id"]
    assert event.payload["question_id"] == question["id"]


def test_create_review_rejects_blank_reason_after_strip(client: TestClient) -> None:
    headers = auth_headers(client)
    question = create_question(client, headers)

    response = client.post(
        f"{API_PREFIX}/reviews",
        json={"question_id": question["id"], "mistake_reason": "   "},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "错题原因不能为空"


def test_review_basic_crud_and_filtering(client: TestClient) -> None:
    headers = auth_headers(client)
    question = create_question(client, headers)
    review = create_review(
        client,
        headers,
        question_id=question["id"],
        mistake_reason="I forgot transaction isolation.",
    )

    list_response = client.get(f"{API_PREFIX}/reviews", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    filter_response = client.get(
        f"{API_PREFIX}/reviews",
        params={"status": "todo", "keyword": "transaction"},
        headers=headers,
    )
    assert filter_response.status_code == 200
    assert filter_response.json()["items"][0]["id"] == review["id"]

    update_response = client.patch(
        f"{API_PREFIX}/reviews/{review['id']}",
        json={"status": "mastered", "review_count": 1},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "mastered"
    assert update_response.json()["review_count"] == 1

    delete_response = client.delete(f"{API_PREFIX}/reviews/{review['id']}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = client.get(f"{API_PREFIX}/reviews/{review['id']}", headers=headers)
    assert missing_response.status_code == 404


def test_user_can_only_access_own_reviews(client: TestClient) -> None:
    alice_headers = auth_headers(client)
    bob_headers = auth_headers(client, username="bob", email="bob@example.com")
    question = create_question(client, alice_headers)
    review = create_review(client, alice_headers, question_id=question["id"])

    list_response = client.get(f"{API_PREFIX}/reviews", headers=bob_headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []

    get_response = client.get(f"{API_PREFIX}/reviews/{review['id']}", headers=bob_headers)
    assert get_response.status_code == 404

    delete_response = client.delete(f"{API_PREFIX}/reviews/{review['id']}", headers=bob_headers)
    assert delete_response.status_code == 404
