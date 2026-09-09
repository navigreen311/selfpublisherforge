"""Unit tests for RedisEventPublisher, event serialization, and singleton access.

Validates:
- RedisEventPublisher.publish() with mocked Redis Pub/Sub
- Publish handles Redis connection failure gracefully (no exception raised)
- Event serialization (model_dump_json used as Pub/Sub payload)
- Channel naming convention (events:{event_type})
- get_event_publisher() singleton behaviour
- EventPublisher base class raises NotImplementedError
- _serialize_event / _deserialize_event for the Streams-based layer
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.event_types import BaseEvent, EventPublisher, EventType
from app.core.events import (
    DLQ_STREAM,
    GLOBAL_STREAM,
    STREAM_PREFIX,
    RedisEventPublisher,
    _deserialize_event,
    _serialize_event,
    get_event_publisher,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ORG_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
_ACTOR_ID = UUID("11111111-2222-3333-4444-555555555555")
_TIMESTAMP = datetime(2025, 7, 1, 12, 0, 0, tzinfo=UTC)


def _make_event(
    event_type: EventType = EventType.USER_REGISTERED,
    org_id: UUID | None = None,
    actor_id: UUID | None = None,
    data: dict | None = None,
) -> BaseEvent:
    return BaseEvent(
        event_type=event_type,
        org_id=org_id or _ORG_ID,
        actor_id=actor_id or _ACTOR_ID,
        actor_type="user",
        timestamp=_TIMESTAMP,
        data=data or {"foo": "bar"},
    )


def _make_redis_pubsub_mock():
    """Return an AsyncMock mimicking redis.asyncio.Redis with publish()."""
    mock = AsyncMock()
    mock.publish = AsyncMock(return_value=1)  # returns number of subscribers
    return mock


# =========================================================================
# EventPublisher base class
# =========================================================================

class TestEventPublisherInterface:
    """The base EventPublisher should raise NotImplementedError."""

    @pytest.mark.asyncio
    async def test_publish_raises_not_implemented(self):
        publisher = EventPublisher()
        event = _make_event()
        with pytest.raises(NotImplementedError):
            await publisher.publish(event)

    def test_publisher_is_instantiable(self):
        """The base class can be instantiated (not truly abstract)."""
        publisher = EventPublisher()
        assert publisher is not None

    @pytest.mark.asyncio
    async def test_subclass_can_override_publish(self):
        published: list[BaseEvent] = []

        class InMemory(EventPublisher):
            async def publish(self, event: BaseEvent) -> None:
                published.append(event)

        pub = InMemory()
        event = _make_event()
        await pub.publish(event)
        assert len(published) == 1
        assert published[0] is event


# =========================================================================
# Event serialization (_serialize_event / _deserialize_event for Streams)
# =========================================================================

class TestEventSerialization:

    def test_serialize_produces_flat_string_dict(self):
        event = _make_event()
        fields = _serialize_event(event)

        assert isinstance(fields, dict)
        for key, value in fields.items():
            assert isinstance(key, str), f"Key {key!r} is not a string"
            assert isinstance(value, str), f"Value for {key!r} is not a string"

    def test_serialize_event_type_value(self):
        event = _make_event(event_type=EventType.AI_GENERATION_STARTED)
        fields = _serialize_event(event)
        assert fields["event_type"] == "ai.generation.started"

    def test_serialize_org_id_as_string(self):
        event = _make_event()
        fields = _serialize_event(event)
        assert fields["org_id"] == str(_ORG_ID)

    def test_serialize_actor_id_as_string(self):
        event = _make_event()
        fields = _serialize_event(event)
        assert fields["actor_id"] == str(_ACTOR_ID)

    def test_serialize_timestamp_is_iso(self):
        event = _make_event()
        fields = _serialize_event(event)
        assert "T" in fields["timestamp"]  # ISO-8601 has 'T' separator

    def test_serialize_contains_raw_field(self):
        event = _make_event()
        fields = _serialize_event(event)
        assert "_raw" in fields
        parsed = json.loads(fields["_raw"])
        assert parsed["event_type"] == event.event_type.value

    def test_serialize_data_is_json_string(self):
        event = _make_event(data={"key": "value", "count": 42})
        fields = _serialize_event(event)
        data = json.loads(fields["data"])
        assert data["key"] == "value"
        assert data["count"] == 42

    def test_roundtrip_serialization(self):
        event = _make_event(event_type=EventType.BOOK_CREATED, data={"title": "My Book"})
        fields = _serialize_event(event)
        restored = _deserialize_event(fields)

        assert restored.event_type == event.event_type
        assert restored.org_id == event.org_id
        assert restored.actor_id == event.actor_id
        assert restored.data == event.data

    def test_roundtrip_from_bytes(self):
        """Simulate Redis returning byte-encoded fields."""
        event = _make_event()
        fields = _serialize_event(event)
        byte_fields = {k.encode(): v.encode() for k, v in fields.items()}
        restored = _deserialize_event(byte_fields)

        assert restored.event_type == event.event_type
        assert restored.org_id == event.org_id

    def test_serialize_handles_uuid_in_data(self):
        """UUIDs inside the data payload should be serialized to strings."""
        uid = uuid4()
        event = _make_event(data={"ref_id": str(uid)})
        fields = _serialize_event(event)
        data = json.loads(fields["data"])
        assert data["ref_id"] == str(uid)

    def test_model_dump_json_produces_valid_json(self):
        """BaseEvent.model_dump_json() should return parseable JSON."""
        event = _make_event(data={"budget": 500})
        raw = event.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["event_type"] == "user.registered"
        assert parsed["data"]["budget"] == 500


# =========================================================================
# Channel naming convention (Pub/Sub + Streams)
# =========================================================================

class TestChannelNaming:

    def test_pubsub_channel_format(self):
        """RedisEventPublisher uses ``events:{event_type.value}`` for channels."""
        event = _make_event(event_type=EventType.PROJECT_CREATED)
        expected_channel = f"events:{event.event_type.value}"
        assert expected_channel == "events:project.created"

    @pytest.mark.parametrize("event_type", list(EventType))
    def test_pubsub_channel_per_event_type(self, event_type: EventType):
        """Every event type should produce ``events:<value>``."""
        channel = f"events:{event_type.value}"
        assert channel.startswith("events:")
        assert "." in channel  # event types use dot notation

    def test_stream_prefix_format(self):
        assert STREAM_PREFIX == "spf:events:"

    def test_global_stream_name(self):
        assert GLOBAL_STREAM == "spf:events:all"

    def test_dlq_stream_name(self):
        assert DLQ_STREAM == "spf:events:dlq"

    @pytest.mark.parametrize("event_type", list(EventType))
    def test_per_type_stream_uses_event_value(self, event_type: EventType):
        """Each event type stream should be ``spf:events:{event_type.value}``."""
        expected = f"spf:events:{event_type.value}"
        assert f"{STREAM_PREFIX}{event_type.value}" == expected


# =========================================================================
# RedisEventPublisher.publish() -- Pub/Sub based
# =========================================================================

class TestRedisEventPublisherPublish:

    @pytest.mark.asyncio
    async def test_publish_calls_redis_publish(self):
        redis_mock = _make_redis_pubsub_mock()
        publisher = RedisEventPublisher()
        publisher._redis = redis_mock

        event = _make_event()
        await publisher.publish(event)

        redis_mock.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_publish_uses_correct_channel(self):
        redis_mock = _make_redis_pubsub_mock()
        publisher = RedisEventPublisher()
        publisher._redis = redis_mock

        event = _make_event(event_type=EventType.PROJECT_CREATED)
        await publisher.publish(event)

        call_args = redis_mock.publish.call_args
        channel = call_args[0][0]
        assert channel == "events:project.created"

    @pytest.mark.asyncio
    async def test_publish_sends_json_payload(self):
        redis_mock = _make_redis_pubsub_mock()
        publisher = RedisEventPublisher()
        publisher._redis = redis_mock

        event = _make_event(data={"key": "val"})
        await publisher.publish(event)

        call_args = redis_mock.publish.call_args
        payload = call_args[0][1]
        parsed = json.loads(payload)
        assert parsed["event_type"] == "user.registered"
        assert parsed["data"]["key"] == "val"

    @pytest.mark.asyncio
    async def test_publish_payload_is_model_dump_json(self):
        """The payload sent to Redis should match event.model_dump_json()."""
        redis_mock = _make_redis_pubsub_mock()
        publisher = RedisEventPublisher()
        publisher._redis = redis_mock

        event = _make_event()
        await publisher.publish(event)

        call_args = redis_mock.publish.call_args
        payload = call_args[0][1]
        assert payload == event.model_dump_json()

    @pytest.mark.asyncio
    async def test_publish_returns_none(self):
        redis_mock = _make_redis_pubsub_mock()
        publisher = RedisEventPublisher()
        publisher._redis = redis_mock

        event = _make_event()
        result = await publisher.publish(event)
        assert result is None

    @pytest.mark.asyncio
    async def test_publish_handles_connection_failure_gracefully(self):
        """When Redis.publish() raises, the error should be caught and logged."""
        redis_mock = _make_redis_pubsub_mock()
        redis_mock.publish = AsyncMock(side_effect=ConnectionError("Redis down"))
        publisher = RedisEventPublisher()
        publisher._redis = redis_mock

        event = _make_event()
        # Should NOT raise -- error is swallowed
        await publisher.publish(event)

    @pytest.mark.asyncio
    async def test_publish_handles_generic_exception_gracefully(self):
        """Any exception during publish should be caught."""
        redis_mock = _make_redis_pubsub_mock()
        redis_mock.publish = AsyncMock(side_effect=RuntimeError("unexpected"))
        publisher = RedisEventPublisher()
        publisher._redis = redis_mock

        event = _make_event()
        await publisher.publish(event)  # Should not raise

    @pytest.mark.asyncio
    async def test_publish_different_event_types_use_different_channels(self):
        redis_mock = _make_redis_pubsub_mock()
        publisher = RedisEventPublisher()
        publisher._redis = redis_mock

        event1 = _make_event(event_type=EventType.USER_LOGIN)
        event2 = _make_event(event_type=EventType.BOOK_CREATED)

        await publisher.publish(event1)
        await publisher.publish(event2)

        assert redis_mock.publish.call_count == 2
        channels = [call[0][0] for call in redis_mock.publish.call_args_list]
        assert "events:user.login" in channels
        assert "events:book.created" in channels

    @pytest.mark.asyncio
    async def test_publish_logs_error_on_failure(self):
        """Verify that the error handler logs the failure."""
        redis_mock = _make_redis_pubsub_mock()
        redis_mock.publish = AsyncMock(side_effect=ConnectionError("Redis down"))
        publisher = RedisEventPublisher()
        publisher._redis = redis_mock

        event = _make_event()

        with patch("app.core.events.logger") as mock_logger:
            await publisher.publish(event)
            mock_logger.error.assert_called_once()


# =========================================================================
# RedisEventPublisher -- lazy initialization
# =========================================================================

class TestRedisEventPublisherInit:

    def test_default_init_no_redis_url(self):
        publisher = RedisEventPublisher()
        assert publisher._redis_url is None
        assert publisher._redis is None

    def test_init_with_redis_url(self):
        publisher = RedisEventPublisher(redis_url="redis://custom:6379/0")
        assert publisher._redis_url == "redis://custom:6379/0"
        assert publisher._redis is None

    @pytest.mark.asyncio
    async def test_get_redis_creates_client_lazily(self):
        """_get_redis() should create the Redis client on first call."""
        publisher = RedisEventPublisher(redis_url="redis://localhost:6379/0")

        with patch("app.core.events.aioredis") as mock_aioredis:
            mock_client = AsyncMock()
            mock_aioredis.Redis.from_url.return_value = mock_client

            client = await publisher._get_redis()

            mock_aioredis.Redis.from_url.assert_called_once_with("redis://localhost:6379/0")
            assert client is mock_client

    @pytest.mark.asyncio
    async def test_get_redis_returns_cached_client(self):
        """Subsequent calls to _get_redis() should return the same client."""
        publisher = RedisEventPublisher()
        fake_client = AsyncMock()
        publisher._redis = fake_client

        client = await publisher._get_redis()
        assert client is fake_client

    @pytest.mark.asyncio
    async def test_get_redis_uses_settings_when_no_url(self):
        """When redis_url is None, falls back to settings.REDIS_URL."""
        publisher = RedisEventPublisher()

        with patch("app.core.events.aioredis") as mock_aioredis:
            mock_client = AsyncMock()
            mock_aioredis.Redis.from_url.return_value = mock_client

            with patch("app.config.get_settings") as mock_settings_fn:
                mock_settings = MagicMock()
                mock_settings.REDIS_URL = "redis://from-settings:6379/0"
                mock_settings_fn.return_value = mock_settings

                await publisher._get_redis()

                mock_aioredis.Redis.from_url.assert_called_once_with(
                    "redis://from-settings:6379/0"
                )


# =========================================================================
# RedisEventPublisher is a proper EventPublisher subclass
# =========================================================================

class TestRedisEventPublisherInterface:

    def test_is_subclass_of_event_publisher(self):
        assert issubclass(RedisEventPublisher, EventPublisher)

    def test_instance_is_event_publisher(self):
        publisher = RedisEventPublisher()
        assert isinstance(publisher, EventPublisher)

    def test_redis_starts_as_none(self):
        publisher = RedisEventPublisher()
        assert publisher._redis is None


# =========================================================================
# get_event_publisher() singleton
# =========================================================================

class TestGetEventPublisher:

    def test_returns_event_publisher_instance(self):
        with patch("app.core.events._publisher", None):
            publisher = get_event_publisher()
            assert isinstance(publisher, EventPublisher)
            assert isinstance(publisher, RedisEventPublisher)

    def test_returns_same_instance_on_repeated_calls(self):
        with patch("app.core.events._publisher", None):
            pub1 = get_event_publisher()
            pub2 = get_event_publisher()
            assert pub1 is pub2

    def test_creates_redis_event_publisher(self):
        with patch("app.core.events._publisher", None):
            publisher = get_event_publisher()
            assert type(publisher) is RedisEventPublisher
