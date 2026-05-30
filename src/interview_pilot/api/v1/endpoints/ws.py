from __future__ import annotations

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from interview_pilot.api.deps import DbSessionDep
from interview_pilot.core.security import decode_access_token
from interview_pilot.modules.auth import repository as auth_repository
from interview_pilot.realtime.manager import websocket_manager

router = APIRouter()


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    session: DbSessionDep,
    token: str = Query(...),
) -> None:
    """
    当前用户的实时通知连接。

    学习重点：WebSocket 无法像普通 HTTP 一样直接用 Authorization 按钮调试，
    学习阶段先用 query token：/ws/notifications?token=xxx。
    生产环境更推荐在连接前由前端从安全位置读取 token，并做好 HTTPS、过期和重连。
    """
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            await websocket.close(code=1008)
            return
        user_id = int(subject)
    except (jwt.InvalidTokenError, ValueError):
        await websocket.close(code=1008)
        return

    user = await auth_repository.get_user_by_id(user_id, session)
    if user is None or not user.is_active:
        await websocket.close(code=1008)
        return

    await websocket_manager.connect(user.id, websocket)
    await websocket.send_json(
        {
            "type": "system",
            "event_type": "websocket.connected",
            "payload": {"user_id": user.id},
        }
    )

    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "system", "event_type": "pong", "payload": {}})
    except WebSocketDisconnect:
        websocket_manager.disconnect(user.id, websocket)
    finally:
        if websocket.application_state == WebSocketState.CONNECTED:
            websocket_manager.disconnect(user.id, websocket)
