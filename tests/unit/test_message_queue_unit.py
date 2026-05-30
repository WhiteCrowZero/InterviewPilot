from __future__ import annotations

import asyncio

from interview_pilot.core.message_queue import DomainEvent, MemoryMessageQueue


def test_memory_message_queue_publish_and_consume_event() -> None:
    async def scenario() -> None:
        queue = MemoryMessageQueue()
        event = DomainEvent(
            event_type="question.created",
            user_id=1,
            payload={"question_id": 10},
        )

        await queue.publish(event)
        consumed = await queue.consume(timeout_seconds=1)

        assert consumed == event

    asyncio.run(scenario())


def test_memory_message_queue_returns_none_when_timeout() -> None:
    async def scenario() -> None:
        queue = MemoryMessageQueue()

        consumed = await queue.consume(timeout_seconds=0)

        assert consumed is None

    asyncio.run(scenario())


def test_domain_event_has_created_at_default() -> None:
    event = DomainEvent(event_type="note.created", user_id=1)

    assert event.payload == {}
    assert event.created_at.tzinfo is not None
