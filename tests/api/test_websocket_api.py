from __future__ import annotations

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from tests.conftest import API_PREFIX
from tests.helpers import auth_headers, bearer_token


def test_websocket_rejects_invalid_token(client: TestClient) -> None:
    try:
        with client.websocket_connect(f"{API_PREFIX}/ws/notifications?token=bad-token"):
            raise AssertionError("invalid token should not connect")
    except WebSocketDisconnect as exc:
        assert exc.code == 1008


def test_websocket_accepts_valid_token_and_replies_to_ping(client: TestClient) -> None:
    headers = auth_headers(client)
    token = bearer_token(headers)

    with client.websocket_connect(f"{API_PREFIX}/ws/notifications?token={token}") as websocket:
        connected = websocket.receive_json()
        assert connected["type"] == "system"
        assert connected["event_type"] == "websocket.connected"
        assert connected["payload"]["user_id"] == 1

        websocket.send_text("ping")
        pong = websocket.receive_json()
        assert pong == {"type": "system", "event_type": "pong", "payload": {}}
