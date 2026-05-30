from __future__ import annotations

import asyncio

from interview_pilot.core.message_queue import MessageQueue
from interview_pilot.realtime.manager import WebSocketConnectionManager


async def run_event_worker(
    message_queue: MessageQueue,
    websocket_manager: WebSocketConnectionManager,
) -> None:
    """
    消息队列消费者。

    学习重点：生产者和消费者解耦。
    - service 层只负责 publish 事件，不关心有没有 WebSocket 在线。
    - worker 层负责 consume 事件，并把事件转成实时通知。
    """
    while True:
        try:
            event = await message_queue.consume(timeout_seconds=1)
            if event is None:
                continue
            await websocket_manager.send_to_user(
                event.user_id,
                {
                    "type": "notification",
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat(),
                },
            )
        except asyncio.CancelledError:
            break
        except Exception:
            # 学习重点：worker 不能因为一条坏消息直接退出。
            # 真实项目应写日志、告警、重试或死信队列；这里先保证学习项目稳定运行。
            await asyncio.sleep(0.2)
