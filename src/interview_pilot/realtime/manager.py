from __future__ import annotations

from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState


class WebSocketConnectionManager:
    """
    WebSocket 连接管理器。

    学习重点：HTTP 是“一问一答”；WebSocket 是“连接保持”。
    后端需要记住当前有哪些用户在线，然后才能主动推送通知。
    """

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        user_connections = self._connections.get(user_id)
        if user_connections is None:
            return
        user_connections.discard(websocket)
        if not user_connections:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: dict[str, Any]) -> None:
        """向某个用户的所有在线连接推送消息。"""
        user_connections = list(self._connections.get(user_id, set()))
        for websocket in user_connections:
            try:
                await websocket.send_json(message)
            except RuntimeError:
                self.disconnect(user_id, websocket)

    def connected_count(self, user_id: int | None = None) -> int:
        if user_id is not None:
            return len(self._connections.get(user_id, set()))
        return sum(len(items) for items in self._connections.values())

    async def close_all(self) -> None:
        for user_id, sockets in list(self._connections.items()):
            for websocket in list(sockets):
                if websocket.application_state == WebSocketState.CONNECTED:
                    await websocket.close()
                self.disconnect(user_id, websocket)

    def reset_for_tests(self) -> None:
        self._connections.clear()


websocket_manager = WebSocketConnectionManager()
