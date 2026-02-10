"""Redis Streams-based event bus for inter-module communication.

Provides publish, subscribe, replay, and dead-letter handling.

If the ``shared.types.events`` package is available, its ``BaseEvent``,
``EventPublisher``, and ``EventType`` types are re-used.  Otherwise,
lightweight local definitions are provided so this module can be imported
without the shared package.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Protocol, runtime_checkable
from uuid import UUID

try:
    from shared.types.events import BaseEvent, EventPublisher, EventType  # type: ignore[import-untyped]
except ImportError:
    # ------------------------------------------------------------------
    # Fallback definitions when the shared package is not installed
    # ------------------------------------------------------------------
    from pydantic import BaseModel

    class EventType(str, Enum):  # type: ignore[no-redef]
        """Minimal set of event types for standalone operation."""
        USER_REGISTERED = "user_registered"
        USER_UPDATED = "user_updated"
        ORG_CREATED = "org_created"
        BOOK_CREATED = "book_created"
        BOOK_UPDATED = "book_updated"
        PIPELINE_STARTED = "pipeline_started"
        PIPELINE_COMPLETED = "pipeline_completed"
        BILLING_SUBSCRIPTION_CHANGED = "billing_subscription_changed"

    class BaseEvent(BaseModel):  # type: ignore[no-redef]
        """Minimal event schema for standalone operation."""
        event_type: EventType
        org_id: UUID
        actor_id: UUID
        actor_type: str = "user"
        timestamp: datetime
        data: dict[str, Any] = {}

    @runtime_checkable
    class EventPublisher(Protocol):  # type: ignore[no-redef]
        async def publish(self, event: "BaseEvent") -> str: ...

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Redis key conventions
STREAM_PREFIX = "spf:events:"
GLOBAL_STREAM = "spf:events:all"
DLQ_STREAM = "spf:events:dlq"


class _UUIDEncoder(json.JSONEncoder):
    """JSON encoder that converts UUID objects to strings."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def _serialize_event(event: BaseEvent) -> dict[str, str]:
    """Convert a BaseEvent into a flat dict suitable for XADD."""
    data = event.model_dump(mode="json")
    return {
        "event_type": event.event_type.value,
        "org_id": str(event.org_id),
        "actor_id": str(event.actor_id),
        "actor_type": event.actor_type,
        "timestamp": event.timestamp.isoformat(),
        "data": json.dumps(data.get("data", {}), cls=_UUIDEncoder),
        "_raw": json.dumps(data, cls=_UUIDEncoder),
    }


def _deserialize_event(fields: dict[bytes | str, bytes | str]) -> BaseEvent:
    """Reconstruct a BaseEvent from a Redis stream entry."""
    raw = fields.get(b"_raw") or fields.get("_raw")
    if isinstance(raw, bytes):
        raw = raw.decode()
    return BaseEvent.model_validate_json(raw)


class RedisEventPublisher(EventPublisher):
    """Publishes events into a Redis Stream.

    Each event is added to both a per-type stream (``spf:events:<event_type>``)
    and the global stream (``spf:events:all``) so consumers can subscribe to
    specific types or all events.
    """

    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client

    async def publish(self, event: BaseEvent) -> str:
        """Publish an event to Redis Streams.  Returns the stream message id."""
        fields = _serialize_event(event)
        type_stream = f"{STREAM_PREFIX}{event.event_type.value}"

        # Write to both per-type and global streams in a pipeline
        pipe = self._redis.pipeline()
        pipe.xadd(type_stream, fields)  # type: ignore[arg-type]
        pipe.xadd(GLOBAL_STREAM, fields)  # type: ignore[arg-type]
        results = await pipe.execute()

        msg_id = results[0]
        if isinstance(msg_id, bytes):
            msg_id = msg_id.decode()
        logger.info("Event published | type=%s stream_id=%s", event.event_type.value, msg_id)
        return msg_id


class RedisEventSubscriber:
    """Subscribes to events from Redis Streams using consumer groups.

    Supports:
    * Filtering by one or more ``EventType`` values
    * Automatic consumer-group creation
    * Dead-letter forwarding for unhandled exceptions in callbacks
    """

    def __init__(
        self,
        redis_client: Any,
        group_name: str,
        consumer_name: str,
    ) -> None:
        self._redis = redis_client
        self._group = group_name
        self._consumer = consumer_name

    async def subscribe(
        self,
        event_types: list[EventType],
        callback: Callable[[BaseEvent], Awaitable[None]],
        *,
        batch_size: int = 10,
        block_ms: int = 5000,
        poll_iterations: int | None = None,
    ) -> None:
        """Listen for events and invoke *callback* for each one.

        Parameters
        ----------
        event_types:
            Which event types to listen to.
        callback:
            Async callable invoked for each event.
        batch_size:
            Number of messages read per XREADGROUP call.
        block_ms:
            How long (ms) to block waiting for new messages.
        poll_iterations:
            If set, stop after this many read cycles (useful for tests).
        """
        streams: dict[str, str] = {}
        for et in event_types:
            stream_key = f"{STREAM_PREFIX}{et.value}"
            await self._ensure_group(stream_key)
            streams[stream_key] = ">"

        iterations = 0
        while poll_iterations is None or iterations < poll_iterations:
            iterations += 1
            try:
                results = await self._redis.xreadgroup(
                    groupname=self._group,
                    consumername=self._consumer,
                    streams=streams,  # type: ignore[arg-type]
                    count=batch_size,
                    block=block_ms,
                )
            except Exception:
                logger.exception("XREADGROUP error -- retrying in 1 s")
                await asyncio.sleep(1)
                continue

            if not results:
                continue

            for _stream_name, messages in results:
                for msg_id, fields in messages:
                    await self._handle_message(msg_id, fields, callback, _stream_name)

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------
    async def replay_events(
        self,
        event_type: EventType,
        start: str = "0",
        end: str = "+",
        count: int = 100,
    ) -> list[BaseEvent]:
        """Replay (read) events from a type-specific stream without consuming.

        Useful for debugging and auditing.
        """
        stream_key = f"{STREAM_PREFIX}{event_type.value}"
        raw = await self._redis.xrange(stream_key, min=start, max=end, count=count)
        events: list[BaseEvent] = []
        for _msg_id, fields in raw:
            try:
                events.append(_deserialize_event(fields))
            except Exception:
                logger.warning("Failed to deserialize event during replay, skipping")
        return events

    # ------------------------------------------------------------------
    # Dead-letter
    # ------------------------------------------------------------------
    async def send_to_dlq(self, original_fields: dict, error: str) -> None:
        """Forward a failed event to the dead letter stream."""
        dlq_fields = dict(original_fields)
        dlq_fields["_dlq_error"] = error
        dlq_fields["_dlq_timestamp"] = str(time.time())
        await self._redis.xadd(DLQ_STREAM, dlq_fields)  # type: ignore[arg-type]
        logger.warning("Event sent to DLQ | error=%s", error)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    async def _ensure_group(self, stream_key: str) -> None:
        """Create consumer group if it does not exist, auto-creating the stream."""
        try:
            await self._redis.xgroup_create(stream_key, self._group, id="0", mkstream=True)
        except Exception:
            # Group already exists -- expected on subsequent startups
            pass

    async def _handle_message(
        self,
        msg_id: Any,
        fields: dict,
        callback: Callable[[BaseEvent], Awaitable[None]],
        stream_name: Any,
    ) -> None:
        try:
            event = _deserialize_event(fields)
            await callback(event)
            # Acknowledge on success
            if isinstance(stream_name, bytes):
                stream_name = stream_name.decode()
            if isinstance(msg_id, bytes):
                msg_id = msg_id.decode()
            await self._redis.xack(stream_name, self._group, msg_id)
        except Exception as exc:
            logger.exception("Failed to process event -- sending to DLQ")
            await self.send_to_dlq(
                {
                    k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
                    for k, v in fields.items()
                },
                str(exc),
            )
