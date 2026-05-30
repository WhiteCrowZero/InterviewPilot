from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX
from tests.helpers import auth_headers, consume_one_event, create_note, create_question


def test_create_note_requires_existing_owned_question(client: TestClient) -> None:
    alice_headers = auth_headers(client)
    bob_headers = auth_headers(client, username="bob", email="bob@example.com")
    alice_question = create_question(client, alice_headers)

    response = client.post(
        f"{API_PREFIX}/notes",
        json={"question_id": alice_question["id"], "content": "Bob should not write here."},
        headers=bob_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "题目不存在"


def test_create_note_trims_content_and_publishes_event(client: TestClient) -> None:
    headers = auth_headers(client)
    question = create_question(client, headers)
    consume_one_event()  # question.created，本测试只关心后面的 note.created

    response = client.post(
        f"{API_PREFIX}/notes",
        json={"question_id": question["id"], "content": "  Important note  "},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["content"] == "Important note"
    assert body["question_id"] == question["id"]

    event = consume_one_event()
    assert event is not None
    assert event.event_type == "note.created"
    assert event.payload["note_id"] == body["id"]
    assert event.payload["question_id"] == question["id"]


def test_create_note_rejects_blank_content_after_strip(client: TestClient) -> None:
    headers = auth_headers(client)
    question = create_question(client, headers)

    response = client.post(
        f"{API_PREFIX}/notes",
        json={"question_id": question["id"], "content": "   "},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "笔记内容不能为空"


def test_note_basic_crud_and_filtering(client: TestClient) -> None:
    headers = auth_headers(client)
    question = create_question(client, headers)
    note = create_note(client, headers, question_id=question["id"], content="Dependency note")

    list_response = client.get(f"{API_PREFIX}/notes", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    keyword_response = client.get(
        f"{API_PREFIX}/notes",
        params={"keyword": "Dependency"},
        headers=headers,
    )
    assert keyword_response.status_code == 200
    assert keyword_response.json()["items"][0]["id"] == note["id"]

    get_response = client.get(f"{API_PREFIX}/notes/{note['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["content"] == "Dependency note"

    update_response = client.patch(
        f"{API_PREFIX}/notes/{note['id']}",
        json={"content": "  Updated note  "},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["content"] == "Updated note"

    delete_response = client.delete(f"{API_PREFIX}/notes/{note['id']}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = client.get(f"{API_PREFIX}/notes/{note['id']}", headers=headers)
    assert missing_response.status_code == 404


def test_user_can_only_access_own_notes(client: TestClient) -> None:
    alice_headers = auth_headers(client)
    bob_headers = auth_headers(client, username="bob", email="bob@example.com")
    question = create_question(client, alice_headers)
    note = create_note(client, alice_headers, question_id=question["id"])

    list_response = client.get(f"{API_PREFIX}/notes", headers=bob_headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []

    get_response = client.get(f"{API_PREFIX}/notes/{note['id']}", headers=bob_headers)
    assert get_response.status_code == 404

    delete_response = client.delete(f"{API_PREFIX}/notes/{note['id']}", headers=bob_headers)
    assert delete_response.status_code == 404
