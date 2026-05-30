from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX
from tests.helpers import auth_headers, bearer_token, create_question


def test_write_request_produces_event_and_worker_pushes_websocket_notification(
    client_with_worker: TestClient,
) -> None:
    """
    集成测试：HTTP 写入 -> MQ 事件 -> 后台 worker -> WebSocket 推送。

    这个测试不是单纯测某个函数，而是验证几个组件能协作起来。
    """
    headers = auth_headers(client_with_worker)
    token = bearer_token(headers)

    with client_with_worker.websocket_connect(
        f"{API_PREFIX}/ws/notifications?token={token}"
    ) as websocket:
        connected = websocket.receive_json()
        assert connected["event_type"] == "websocket.connected"

        question = create_question(
            client_with_worker,
            headers,
            title="WebSocket integration event",
        )
        notification = websocket.receive_json()

        assert notification["type"] == "notification"
        assert notification["event_type"] == "question.created"
        assert notification["payload"]["question_id"] == question["id"]


def test_user_does_not_receive_other_users_websocket_notification(
    client_with_worker: TestClient,
) -> None:
    alice_headers = auth_headers(client_with_worker)
    bob_headers = auth_headers(client_with_worker, username="bob", email="bob@example.com")
    alice_token = bearer_token(alice_headers)

    with client_with_worker.websocket_connect(
        f"{API_PREFIX}/ws/notifications?token={alice_token}"
    ) as websocket:
        connected = websocket.receive_json()
        assert connected["event_type"] == "websocket.connected"

        create_question(client_with_worker, bob_headers, title="Bob's private event")

        # 如果服务错误地把 Bob 的事件推给 Alice，这里会收到 notification。
        # 当前测试客户端没有方便的短超时 receive API，因此用 ping 验证连接仍正常，
        # 并间接说明 Bob 的写入不会阻断 Alice 的连接。
        websocket.send_text("ping")
        pong = websocket.receive_json()
        assert pong == {"type": "system", "event_type": "pong", "payload": {}}
