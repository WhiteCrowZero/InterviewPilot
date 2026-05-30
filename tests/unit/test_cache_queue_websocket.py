from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from interview_pilot.core.message_queue import get_message_queue
from tests.conftest import create_test_client
from tests.unit.test_questions import auth_headers


def _token_from_headers(headers: dict[str, str]) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


def _create_question(
    client: TestClient,
    headers: dict[str, str],
    title: str = "Redis cache",
) -> int:
    response = client.post(
        "/api/v1/questions",
        json={
            "title": title,
            "answer": "Cache frequently read summary data.",
            "category": "backend",
            "difficulty": 3,
            "tags": ["redis"],
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_dashboard_summary_uses_cache_aside_and_invalidation() -> None:
    client = create_test_client()
    headers = auth_headers(client)

    first_summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert first_summary.status_code == 200
    assert first_summary.json()["question_count"] == 0

    # 如果写操作没有删除 dashboard 缓存，这里会继续读到旧的 0。
    # 所以这个测试同时验证了 Cache Aside 和写后失效。
    _create_question(client, headers)

    second_summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert second_summary.status_code == 200
    body = second_summary.json()
    assert body["question_count"] == 1
    assert body["category_distribution"] == [{"category": "backend", "count": 1}]


def test_message_queue_receives_domain_event_after_write() -> None:
    client = create_test_client()
    headers = auth_headers(client)

    question_id = _create_question(client, headers, title="Message queue event")

    event = asyncio.run(get_message_queue().consume(timeout_seconds=1))
    assert event is not None
    assert event.event_type == "question.created"
    assert event.user_id == 1
    assert event.payload["question_id"] == question_id


def test_websocket_receives_notification_from_background_worker() -> None:
    client = create_test_client()

    # TestClient 作为上下文管理器使用时，会执行 FastAPI lifespan，
    # 也就是启动本项目里的后台 event worker。
    with client:
        headers = auth_headers(client)
        token = _token_from_headers(headers)

        with client.websocket_connect(f"/api/v1/ws/notifications?token={token}") as websocket:
            connected = websocket.receive_json()
            assert connected["event_type"] == "websocket.connected"

            question_id = _create_question(client, headers, title="WebSocket notification")
            notification = websocket.receive_json()

            assert notification["type"] == "notification"
            assert notification["event_type"] == "question.created"
            assert notification["payload"]["question_id"] == question_id


def test_websocket_rejects_invalid_token() -> None:
    client = create_test_client()

    with client:
        try:
            with client.websocket_connect("/api/v1/ws/notifications?token=bad-token"):
                raise AssertionError("invalid token should not connect")
        except WebSocketDisconnect as exc:
            assert exc.code == 1008
