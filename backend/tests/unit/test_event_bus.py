"""Unit tests for the Redis event bus: publishing, subscribing, and dead letter handling."""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.event_types import BaseEvent, EventType, EventPublisher
from app.core.events import (
    RedisEventPublisher,
    RedisEventSubscriber,
    _serialize_event,
    _deserialize_event,
    STREAM_PREFIX,
    GLOBAL_STREAM,
    DLQ_STREAM,
)
from app.tasks.dead_letter import DeadLetter, DeadLetterQueue


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_event(
    event_type: EventType = EventType.USER_REGISTERED,
    org_id=None,
    actor_id=None,
) -> BaseEvent:
    return BaseEvent(
        event_type=event_type,
        org_id=org_id or uuid4(),
        actor_id=actor_id or uuid4(),
        actor_type="user",
        timestamp=datetime.now(timezone.utc),
        data={"foo": "bar"},
    )


def _async_redis_mock():
    """Return an AsyncMock mimicking redis.asyncio.Redis.

    ``pipeline()`` is a *sync* method in redis.asyncio that returns a Pipeline
    whose individual commands (xadd, execute, etc.) are async.  We model that
    with a MagicMock for pipeline() itself and AsyncMock for the commands on the
    pipeline object.
    """
    mock = AsyncMock()
    pipe = MagicMock()  # pipeline object — attribute access is sync
    pipe.xadd = MagicMock()  # xadd on pipeline is buffered (sync)
    pipe.execute = AsyncMock(return_value=[b"1234-0", b"5678-0"])
    # pipeline() is a regular sync method
    mock.pipeline = MagicMock(return_value=pipe)
    return mock


# ========================================================================
# Serialization / deserialization
# ========================================================================

class TestSerialization:

    def test_serialize_produces_flat_dict(self):
        event = _make_event()
        fields = _serialize_event(event)

        assert isinstance(fields, dict)
        assert fields["event_type"] == event.event_type.value
        assert fields["org_id"] == str(event.org_id)
        assert "_raw" in fields

    def test_roundtrip(self):
        event = _make_event(event_type=EventType.AI_GENERATION_STARTED)
        fields = _serialize_event(event)
        restored = _deserialize_event(fields)

        assert restored.event_type == event.event_type
        assert restored.org_id == event.org_id
        assert restored.data == event.data

    def test_deserialize_from_bytes(self):
        event = _make_event()
        fields = _serialize_event(event)
        # Simulate Redis returning bytes
        byte_fields = {k.encode(): v.encode() for k, v in fields.items()}
        restored = _deserialize_event(byte_fields)

        assert restored.event_type == event.event_type


# ========================================================================
# RedisEventPublisher
# ========================================================================

class TestRedisEventPublisher:

    @pytest.mark.asyncio
    async def test_publish_writes_to_two_streams(self):
        """RedisEventPublisher publishes to the correct Pub/Sub channel."""
        redis_mock = AsyncMock()
        redis_mock.publish = AsyncMock(return_value=1)

        publisher = RedisEventPublisher(redis_url="redis://localhost")
        publisher._redis = redis_mock  # inject mock directly

        event = _make_event()
        await publisher.publish(event)

        expected_channel = f"events:{event.event_type.value}"
        redis_mock.publish.assert_called_once()
        actual_channel = redis_mock.publish.call_args[0][0]
        assert actual_channel == expected_channel

    @pytest.mark.asyncio
    async def test_publish_returns_message_id(self):
        """RedisEventPublisher.publish returns None (Pub/Sub, no message id)."""
        redis_mock = AsyncMock()
        redis_mock.publish = AsyncMock(return_value=1)

        publisher = RedisEventPublisher(redis_url="redis://localhost")
        publisher._redis = redis_mock  # inject mock directly

        event = _make_event()
        result = await publisher.publish(event)
        assert result is None

    @pytest.mark.asyncio
    async def test_publisher_implements_interface(self):
        """RedisEventPublisher must satisfy the EventPublisher interface."""
        assert issubclass(RedisEventPublisher, EventPublisher)


# ========================================================================
# RedisEventSubscriber
# ========================================================================

class TestRedisEventSubscriber:

    @pytest.mark.asyncio
    async def test_subscribe_creates_consumer_group(self):
        redis_mock = _async_redis_mock()
        redis_mock.xreadgroup = AsyncMock(return_value=[])
        redis_mock.xgroup_create = AsyncMock()

        subscriber = RedisEventSubscriber(redis_mock, "test-group", "consumer-1")
        callback = AsyncMock()

        await subscriber.subscribe(
            [EventType.USER_REGISTERED],
            callback,
            poll_iterations=1,
        )

        redis_mock.xgroup_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_invokes_callback(self):
        event = _make_event()
        fields = _serialize_event(event)
        byte_fields = {k.encode(): v.encode() for k, v in fields.items()}
        stream_key = f"{STREAM_PREFIX}{EventType.USER_REGISTERED.value}"

        redis_mock = _async_redis_mock()
        redis_mock.xgroup_create = AsyncMock()
        redis_mock.xack = AsyncMock()
        redis_mock.xreadgroup = AsyncMock(
            return_value=[
                (stream_key.encode(), [(b"1-0", byte_fields)])
            ]
        )

        subscriber = RedisEventSubscriber(redis_mock, "grp", "c1")
        callback = AsyncMock()

        await subscriber.subscribe(
            [EventType.USER_REGISTERED],
            callback,
            poll_iterations=1,
        )

        callback.assert_called_once()
        received_event = callback.call_args[0][0]
        assert received_event.event_type == EventType.USER_REGISTERED

    @pytest.mark.asyncio
    async def test_subscribe_acks_on_success(self):
        event = _make_event()
        fields = _serialize_event(event)
        byte_fields = {k.encode(): v.encode() for k, v in fields.items()}
        stream_key = f"{STREAM_PREFIX}{EventType.USER_REGISTERED.value}"

        redis_mock = _async_redis_mock()
        redis_mock.xgroup_create = AsyncMock()
        redis_mock.xack = AsyncMock()
        redis_mock.xreadgroup = AsyncMock(
            return_value=[
                (stream_key.encode(), [(b"1-0", byte_fields)])
            ]
        )

        subscriber = RedisEventSubscriber(redis_mock, "grp", "c1")
        callback = AsyncMock()

        await subscriber.subscribe(
            [EventType.USER_REGISTERED],
            callback,
            poll_iterations=1,
        )

        redis_mock.xack.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_sends_to_dlq_on_callback_error(self):
        event = _make_event()
        fields = _serialize_event(event)
        byte_fields = {k.encode(): v.encode() for k, v in fields.items()}
        stream_key = f"{STREAM_PREFIX}{EventType.USER_REGISTERED.value}"

        redis_mock = _async_redis_mock()
        redis_mock.xgroup_create = AsyncMock()
        redis_mock.xack = AsyncMock()
        redis_mock.xadd = AsyncMock()
        redis_mock.xreadgroup = AsyncMock(
            return_value=[
                (stream_key.encode(), [(b"1-0", byte_fields)])
            ]
        )

        subscriber = RedisEventSubscriber(redis_mock, "grp", "c1")
        callback = AsyncMock(side_effect=RuntimeError("processing failed"))

        await subscriber.subscribe(
            [EventType.USER_REGISTERED],
            callback,
            poll_iterations=1,
        )

        # Should have written to the DLQ stream
        redis_mock.xadd.assert_called_once()
        dlq_call_args = redis_mock.xadd.call_args[0]
        assert dlq_call_args[0] == DLQ_STREAM

    @pytest.mark.asyncio
    async def test_replay_events(self):
        event = _make_event(event_type=EventType.PROJECT_CREATED)
        fields = _serialize_event(event)
        byte_fields = {k.encode(): v.encode() for k, v in fields.items()}

        redis_mock = _async_redis_mock()
        redis_mock.xrange = AsyncMock(return_value=[(b"1-0", byte_fields)])

        subscriber = RedisEventSubscriber(redis_mock, "grp", "c1")
        events = await subscriber.replay_events(EventType.PROJECT_CREATED, count=10)

        assert len(events) == 1
        assert events[0].event_type == EventType.PROJECT_CREATED

    @pytest.mark.asyncio
    async def test_send_to_dlq_adds_error_fields(self):
        redis_mock = _async_redis_mock()
        redis_mock.xadd = AsyncMock()

        subscriber = RedisEventSubscriber(redis_mock, "grp", "c1")
        await subscriber.send_to_dlq({"event_type": "test"}, "some error")

        redis_mock.xadd.assert_called_once()
        dlq_fields = redis_mock.xadd.call_args[0][1]
        assert dlq_fields["_dlq_error"] == "some error"
        assert "_dlq_timestamp" in dlq_fields


# ========================================================================
# DeadLetterQueue (Redis-backed)
# ========================================================================

class TestDeadLetterQueue:

    def _make_redis_mock(self):
        """Synchronous Redis mock for DeadLetterQueue."""
        mock = MagicMock()
        pipe = MagicMock()
        pipe.execute = MagicMock(return_value=[True, True])
        mock.pipeline.return_value = pipe
        return mock

    def test_add_stores_dead_letter(self):
        redis_mock = self._make_redis_mock()
        dlq = DeadLetterQueue(redis_mock)
        dl = DeadLetter(
            source_type="task",
            source_name="app.tasks.ai_tasks.generate",
            payload={"input": "test"},
            error_message="timeout",
            error_type="TimeoutError",
        )

        dl_id = dlq.add(dl)

        assert dl_id == dl.id
        pipe = redis_mock.pipeline.return_value
        pipe.set.assert_called_once()
        pipe.zadd.assert_called_once()

    def test_get_returns_dead_letter(self):
        dl = DeadLetter(
            source_type="event",
            source_name="user.registered",
            error_message="bad data",
        )
        redis_mock = self._make_redis_mock()
        redis_mock.get = MagicMock(return_value=json.dumps(dl.to_dict()))
        dlq = DeadLetterQueue(redis_mock)

        result = dlq.get(dl.id)

        assert result is not None
        assert result.source_name == "user.registered"
        assert result.error_message == "bad data"

    def test_get_returns_none_for_missing(self):
        redis_mock = self._make_redis_mock()
        redis_mock.get = MagicMock(return_value=None)
        dlq = DeadLetterQueue(redis_mock)

        assert dlq.get("nonexistent") is None

    def test_list_returns_ordered_results(self):
        dl1 = DeadLetter(source_type="task", source_name="t1", error_message="e1")
        dl2 = DeadLetter(source_type="task", source_name="t2", error_message="e2")

        redis_mock = self._make_redis_mock()
        redis_mock.zrevrange = MagicMock(return_value=[dl1.id, dl2.id])
        redis_mock.get = MagicMock(
            side_effect=lambda key: {
                f"spf:dlq:detail:{dl1.id}": json.dumps(dl1.to_dict()),
                f"spf:dlq:detail:{dl2.id}": json.dumps(dl2.to_dict()),
            }.get(key)
        )

        dlq = DeadLetterQueue(redis_mock)
        results = dlq.list()

        assert len(results) == 2
        assert results[0].source_name == "t1"

    def test_mark_retried(self):
        dl = DeadLetter(source_type="task", source_name="t1", error_message="e1")
        redis_mock = self._make_redis_mock()
        redis_mock.get = MagicMock(return_value=json.dumps(dl.to_dict()))

        dlq = DeadLetterQueue(redis_mock)
        result = dlq.mark_retried(dl.id)

        assert result is True
        # Verify the status was updated in the saved data
        saved_data = json.loads(redis_mock.set.call_args[0][1])
        assert saved_data["status"] == "retried"

    def test_mark_discarded(self):
        dl = DeadLetter(source_type="event", source_name="ev1", error_message="e1")
        redis_mock = self._make_redis_mock()
        redis_mock.get = MagicMock(return_value=json.dumps(dl.to_dict()))

        dlq = DeadLetterQueue(redis_mock)
        result = dlq.mark_discarded(dl.id)

        assert result is True
        saved_data = json.loads(redis_mock.set.call_args[0][1])
        assert saved_data["status"] == "discarded"

    def test_mark_retried_returns_false_for_missing(self):
        redis_mock = self._make_redis_mock()
        redis_mock.get = MagicMock(return_value=None)
        dlq = DeadLetterQueue(redis_mock)

        assert dlq.mark_retried("missing") is False

    def test_remove(self):
        redis_mock = self._make_redis_mock()
        pipe = redis_mock.pipeline.return_value
        pipe.execute.return_value = [1, 1]

        dlq = DeadLetterQueue(redis_mock)
        assert dlq.remove("some-id") is True

    def test_count(self):
        redis_mock = self._make_redis_mock()
        redis_mock.zcard = MagicMock(return_value=42)

        dlq = DeadLetterQueue(redis_mock)
        assert dlq.count() == 42

    def test_purge(self):
        redis_mock = self._make_redis_mock()
        redis_mock.zcard = MagicMock(return_value=3)
        redis_mock.zrange = MagicMock(return_value=[b"id1", b"id2", b"id3"])

        pipe = redis_mock.pipeline.return_value
        pipe.execute = MagicMock(return_value=[1, 1, 1, 1])

        dlq = DeadLetterQueue(redis_mock)
        count = dlq.purge()

        assert count == 3

    def test_dead_letter_roundtrip_serialization(self):
        dl = DeadLetter(
            source_type="task",
            source_name="my.task",
            payload={"key": "value"},
            error_message="failed",
            error_type="ValueError",
            retry_count=2,
            max_retries=5,
            org_id="org-123",
            correlation_id="corr-456",
        )
        data = dl.to_dict()
        restored = DeadLetter.from_dict(data)

        assert restored.id == dl.id
        assert restored.source_name == dl.source_name
        assert restored.payload == dl.payload
        assert restored.org_id == dl.org_id
        assert restored.correlation_id == dl.correlation_id

    def test_list_filters_by_status(self):
        dl1 = DeadLetter(source_type="task", source_name="t1", error_message="e1", status="pending")
        dl2 = DeadLetter(source_type="task", source_name="t2", error_message="e2", status="retried")

        redis_mock = self._make_redis_mock()
        redis_mock.zrevrange = MagicMock(return_value=[dl1.id, dl2.id])
        redis_mock.get = MagicMock(
            side_effect=lambda key: {
                f"spf:dlq:detail:{dl1.id}": json.dumps(dl1.to_dict()),
                f"spf:dlq:detail:{dl2.id}": json.dumps(dl2.to_dict()),
            }.get(key)
        )

        dlq = DeadLetterQueue(redis_mock)
        results = dlq.list(status="pending")

        assert len(results) == 1
        assert results[0].source_name == "t1"
