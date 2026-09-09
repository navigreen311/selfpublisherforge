"""Redis-based event bus for inter-module communication.

Provides publish (Pub/Sub + Streams), subscribe, replay, and dead-letter handling.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, cast
from uuid import UUID

from pydantic import ValidationError

from app.core.event_types import BaseEvent, EventPublisher, EventType

try:
    import redis.asyncio as aioredis
    from redis.exceptions import ConnectionError as RedisConnectionError
    from redis.exceptions import RedisError, ResponseError
except ImportError:
    aioredis = None  # type: ignore[assignment]
    RedisConnectionError = ConnectionError  # type: ignore[misc,assignment]
    RedisError = Exception  # type: ignore[misc,assignment]
    ResponseError = Exception  # type: ignore[misc,assignment]


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
    return BaseEvent.model_validate_json(raw)  # type: ignore[arg-type]


class RedisStreamPublisher:
    """Publishes events into a Redis Stream (legacy / Streams-based).

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
        return cast("str", msg_id)


class RedisEventPublisher(EventPublisher):
    """Publishes events to Redis Pub/Sub channels.

    Uses lazy Redis connection initialization -- the connection is only
    created on the first ``publish()`` call.  Falls back to ``settings.REDIS_URL``
    when no explicit *redis_url* is provided.

    Event publishing failures are logged but **never** re-raised so that the
    caller's workflow is not interrupted by infrastructure issues.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url
        self._redis: Any = None  # redis.asyncio.Redis | None

    async def _get_redis(self) -> Any:
        """Return (and lazily create) the async Redis client."""
        if self._redis is None:
            if aioredis is None:
                raise RuntimeError("redis package is not installed -- cannot create RedisEventPublisher")
            from app.config import get_settings

            url = self._redis_url or get_settings().REDIS_URL
            self._redis = aioredis.Redis.from_url(url)
        return self._redis

    async def publish(self, event: BaseEvent) -> None:
        """Publish an event to a Redis Pub/Sub channel.

        The channel name follows the convention ``events:<event_type_value>``,
        e.g. ``events:project.created``.
        """
        try:
            redis_client = await self._get_redis()
            channel = f"events:{event.event_type.value}"
            payload = event.model_dump_json()
            await redis_client.publish(channel, payload)
            logger.debug("Published event %s to channel %s", event.event_type, channel)
        except Exception as e:
            logger.error(
                "Failed to publish event %s: %s",
                event.event_type,
                e,
                exc_info=True,
            )
            # Don't raise - event publishing should not break the caller


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
            except (RedisConnectionError, RedisError, ConnectionError, TimeoutError, OSError):
                logger.error("XREADGROUP error -- retrying in 1 s", exc_info=True)
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
            except (ValidationError, KeyError, ValueError, json.JSONDecodeError):
                logger.warning("Failed to deserialize event during replay, skipping", exc_info=True)
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
        with contextlib.suppress(ResponseError):
            # Group already exists -- expected on subsequent startups
            await self._redis.xgroup_create(stream_key, self._group, id="0", mkstream=True)

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
        except (ValidationError, KeyError, ValueError, json.JSONDecodeError, RedisError, RuntimeError) as exc:
            logger.error("Failed to process event -- sending to DLQ", exc_info=True)
            await self.send_to_dlq(
                {
                    k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
                    for k, v in fields.items()
                },
                str(exc),
            )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_publisher: EventPublisher | None = None


def get_event_publisher() -> EventPublisher:
    """Return the module-level ``RedisEventPublisher`` singleton.

    The publisher is created lazily on first call and reused for
    the lifetime of the process.
    """
    global _publisher
    if _publisher is None:
        _publisher = RedisEventPublisher()
    return _publisher
