"""Event publisher/subscriber that bridges the shared EventPublisher interface
with Redis pub/sub for real-time WebSocket fanout.

Usage from other modules::

    from app.modules.realtime.events import publish_to_channel, subscribe_to_channel

    await publish_to_channel(WSChannel.AGENTS, org_id, {
        "type": "task_progress",
        "task_id": "abc",
        "progress": 42,
    })
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from app.config import get_settings
from app.modules.realtime.schemas import WSChannel

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore[assignment]


def _channel_key(channel: WSChannel, room_id: str) -> str:
    return f"ws:{channel.value}:{room_id}"


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

async def publish_to_channel(
    channel: WSChannel,
    room_id: str,
    event: dict[str, Any],
    *,
    redis_url: str | None = None,
) -> None:
    """Publish *event* to the Redis pub/sub channel for ``(channel, room_id)``.

    The ``ConnectionManager``'s listener will pick the message up and relay it
    to all connected WebSocket clients.
    """
    if aioredis is None:
        logger.warning("redis.asyncio not available; cannot publish event")
        return

    url = redis_url or get_settings().REDIS_URL
    redis = aioredis.from_url(url, decode_responses=True)
    try:
        payload = {
            "type": event.get("type", "unknown"),
            "channel": channel.value,
            "room_id": room_id,
            "data": event.get("data", event),
            "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat()),
        }
        await redis.publish(_channel_key(channel, room_id), json.dumps(payload, default=str))
    finally:
        await redis.close()


# ---------------------------------------------------------------------------
# Subscribe (async iterator)
# ---------------------------------------------------------------------------

async def subscribe_to_channel(
    channel: WSChannel,
    room_id: str,
    *,
    redis_url: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Async generator that yields messages from the Redis pub/sub channel for
    ``(channel, room_id)``."""
    if aioredis is None:
        logger.warning("redis.asyncio not available; cannot subscribe")
        return

    url = redis_url or get_settings().REDIS_URL
    redis = aioredis.from_url(url, decode_responses=True)
    pubsub = redis.pubsub()
    channel_key = _channel_key(channel, room_id)
    await pubsub.subscribe(channel_key)
    try:
        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            try:
                yield json.loads(raw["data"])
            except json.JSONDecodeError:
                logger.warning("Ignoring non-JSON pub/sub message")
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel_key)
        await pubsub.close()
        await redis.close()


# ---------------------------------------------------------------------------
# Integration with shared EventPublisher interface
# ---------------------------------------------------------------------------

class RealtimeEventPublisher:
    """Concrete ``EventPublisher`` that pushes events to the WebSocket layer
    via Redis pub/sub.

    Import ``shared.types.events.BaseEvent`` and ``EventPublisher`` at runtime
    so that the shared package is not a hard import-time dependency.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url

    async def publish(self, event: Any) -> None:
        """Publish a ``BaseEvent`` to the appropriate WebSocket channel.

        The mapping from ``EventType`` to ``WSChannel`` is intentionally broad:
        agent events -> AGENTS channel, analytics -> ANALYTICS, publishing ->
        PUBLISHING.  Everything else is silently ignored.
        """
        from shared.types.events import BaseEvent  # type: ignore[import-untyped]

        if not isinstance(event, BaseEvent):
            return

        event_type_value: str = event.event_type.value
        channel: WSChannel | None = None
        room_id: str = str(event.org_id)

        if event_type_value.startswith("agent."):
            channel = WSChannel.AGENTS
        elif event_type_value.startswith("analytics."):
            channel = WSChannel.ANALYTICS
        elif event_type_value.startswith("publishing."):
            channel = WSChannel.PUBLISHING

        if channel is None:
            return

        await publish_to_channel(
            channel,
            room_id,
            {
                "type": event_type_value,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
            },
            redis_url=self._redis_url,
        )
