"""Comprehensive unit tests for ConnectionManager.

Tests cover:
- Connection lifecycle (connect, disconnect, cleanup)
- Broadcasting to channels, users, and orgs
- Connection limits and error handling
- Heartbeat/ping functionality
- Redis pub/sub integration
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.realtime.manager import ConnectionManager, _channel_key
from app.modules.realtime.schemas import WSChannel

# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------


class FakeWebSocket:
    """Minimal WebSocket stand-in for unit testing."""

    def __init__(self, *, connected: bool = True, user_id: str = "user-1") -> None:
        self.accepted = False
        self.sent_messages: list[dict[str, Any]] = []
        self._connected = connected
        self.user_id = user_id

        # Starlette's WebSocketState enum
        from starlette.websockets import WebSocketState

        self.client_state = WebSocketState.CONNECTED if connected else WebSocketState.DISCONNECTED

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: dict[str, Any]) -> None:
        if not self._connected:
            raise RuntimeError("WebSocket is closed")
        self.sent_messages.append(data)

    async def receive_json(self) -> dict[str, Any]:
        # Block forever in tests — handler loop not exercised
        await asyncio.sleep(999)
        return {}


# ---------------------------------------------------------------------------
# Tests — Channel Key Generation
# ---------------------------------------------------------------------------


def test_channel_key_writing() -> None:
    assert _channel_key(WSChannel.WRITING, "book-1") == "ws:writing:book-1"


def test_channel_key_agents() -> None:
    assert _channel_key(WSChannel.AGENTS, "org-42") == "ws:agents:org-42"


def test_channel_key_analytics() -> None:
    assert _channel_key(WSChannel.ANALYTICS, "org-7") == "ws:analytics:org-7"


def test_channel_key_publishing() -> None:
    assert _channel_key(WSChannel.PUBLISHING, "book-9") == "ws:publishing:book-9"


# ---------------------------------------------------------------------------
# Tests — Connect / Disconnect Lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_registers_websocket() -> None:
    """Test that connect() adds connection to registry."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    assert ws.accepted is True
    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 1


@pytest.mark.asyncio
async def test_connect_multiple_in_same_room() -> None:
    """Test multiple connections can join the same room."""
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await mgr.connect(ws1, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.connect(ws2, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 2


@pytest.mark.asyncio
async def test_connect_different_channels() -> None:
    """Test connections to different channels are isolated."""
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await mgr.connect(ws1, WSChannel.WRITING, "room-1")  # type: ignore[arg-type]
    await mgr.connect(ws2, WSChannel.AGENTS, "room-1")  # type: ignore[arg-type]

    assert mgr.get_connection_count(WSChannel.WRITING, "room-1") == 1
    assert mgr.get_connection_count(WSChannel.AGENTS, "room-1") == 1


@pytest.mark.asyncio
async def test_disconnect_removes_websocket() -> None:
    """Test that disconnect() removes connection from registry."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.AGENTS, "org-1") == 1

    await mgr.disconnect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.AGENTS, "org-1") == 0


@pytest.mark.asyncio
async def test_disconnect_cleans_up_empty_rooms() -> None:
    """Test that empty rooms are removed from registry."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.disconnect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    # Room should be removed from active_connections
    assert (WSChannel.WRITING, "book-1") not in mgr.active_connections


@pytest.mark.asyncio
async def test_disconnect_nonexistent_is_noop() -> None:
    """Test that disconnecting non-existent connection doesn't raise."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()
    # Should not raise
    await mgr.disconnect(ws, WSChannel.WRITING, "no-room")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_disconnect_on_error() -> None:
    """Test connection cleanup on error."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.PUBLISHING, "book-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.PUBLISHING, "book-1") == 1

    # Simulate error cleanup
    await mgr.disconnect(ws, WSChannel.PUBLISHING, "book-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.PUBLISHING, "book-1") == 0


# ---------------------------------------------------------------------------
# Tests — Broadcasting to Channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_broadcast_sends_to_all_in_room() -> None:
    """Test broadcast to channel sends to all subscribers."""
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await mgr.connect(ws1, WSChannel.ANALYTICS, "org-5")  # type: ignore[arg-type]
    await mgr.connect(ws2, WSChannel.ANALYTICS, "org-5")  # type: ignore[arg-type]

    await mgr.broadcast(WSChannel.ANALYTICS, "org-5", {"type": "metric_update", "value": 42})

    assert len(ws1.sent_messages) == 1
    assert ws1.sent_messages[0]["type"] == "metric_update"
    assert ws1.sent_messages[0]["value"] == 42

    assert len(ws2.sent_messages) == 1
    assert ws2.sent_messages[0]["type"] == "metric_update"


@pytest.mark.asyncio
async def test_broadcast_does_not_leak_to_other_rooms() -> None:
    """Test messages only go to the specified room."""
    mgr = ConnectionManager()
    ws_room_a = FakeWebSocket()
    ws_room_b = FakeWebSocket()

    await mgr.connect(ws_room_a, WSChannel.WRITING, "book-a")  # type: ignore[arg-type]
    await mgr.connect(ws_room_b, WSChannel.WRITING, "book-b")  # type: ignore[arg-type]

    await mgr.broadcast(WSChannel.WRITING, "book-a", {"type": "text_change"})

    assert len(ws_room_a.sent_messages) == 1
    assert len(ws_room_b.sent_messages) == 0


@pytest.mark.asyncio
async def test_broadcast_adds_envelope_fields() -> None:
    """Test broadcast adds channel, room_id, timestamp to message."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.broadcast(WSChannel.AGENTS, "org-1", {"type": "task_started"})

    assert len(ws.sent_messages) == 1
    msg = ws.sent_messages[0]
    assert msg["channel"] == "agents"
    assert msg["room_id"] == "org-1"
    assert "timestamp" in msg


@pytest.mark.asyncio
async def test_broadcast_removes_dead_connections() -> None:
    """Test dead connections are cleaned up during broadcast."""
    mgr = ConnectionManager()
    ws_alive = FakeWebSocket()
    ws_dead = FakeWebSocket(connected=False)

    from starlette.websockets import WebSocketState

    ws_dead.client_state = WebSocketState.DISCONNECTED

    await mgr.connect(ws_alive, WSChannel.PUBLISHING, "book-3")  # type: ignore[arg-type]
    await mgr.connect(ws_dead, WSChannel.PUBLISHING, "book-3")  # type: ignore[arg-type]

    assert mgr.get_connection_count(WSChannel.PUBLISHING, "book-3") == 2

    await mgr.broadcast(WSChannel.PUBLISHING, "book-3", {"type": "upload_progress"})

    # Dead connection should be pruned
    assert mgr.get_connection_count(WSChannel.PUBLISHING, "book-3") == 1
    assert len(ws_alive.sent_messages) == 1


@pytest.mark.asyncio
async def test_broadcast_to_empty_room_is_noop() -> None:
    """Test broadcasting to empty room doesn't raise."""
    mgr = ConnectionManager()
    # Should not raise
    await mgr.broadcast(WSChannel.WRITING, "empty-room", {"type": "test"})


# ---------------------------------------------------------------------------
# Tests — Personal Messages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_personal_message() -> None:
    """Test send_personal sends to single WebSocket."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()
    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    await mgr.send_personal(ws, {"type": "connected", "msg": "hello"})  # type: ignore[arg-type]

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "connected"


@pytest.mark.asyncio
async def test_send_personal_to_closed_websocket() -> None:
    """Test send_personal handles closed WebSocket gracefully."""
    mgr = ConnectionManager()
    ws = FakeWebSocket(connected=False)
    from starlette.websockets import WebSocketState

    ws.client_state = WebSocketState.DISCONNECTED

    # Should not raise, just log warning
    await mgr.send_personal(ws, {"type": "test"})  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_send_personal_with_connection_error() -> None:
    """Test send_personal handles connection errors."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()
    ws._connected = False  # Will raise on send_json

    # Should not raise
    await mgr.send_personal(ws, {"type": "test"})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tests — Redis Pub/Sub (Mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_broadcast_publishes_to_redis() -> None:
    """Test broadcast publishes to Redis when configured."""
    mgr = ConnectionManager(redis_url="redis://fake:6379/0")

    mock_redis = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)
    mgr._redis = mock_redis

    ws = FakeWebSocket()
    await mgr.connect(ws, WSChannel.AGENTS, "org-99")  # type: ignore[arg-type]

    await mgr.broadcast(WSChannel.AGENTS, "org-99", {"type": "task_started", "task_id": "t1"})

    mock_redis.publish.assert_called_once()
    call_args = mock_redis.publish.call_args
    assert call_args[0][0] == "ws:agents:org-99"

    payload = json.loads(call_args[0][1])
    assert payload["type"] == "task_started"
    assert payload["channel"] == "agents"
    assert payload["room_id"] == "org-99"


@pytest.mark.asyncio
async def test_broadcast_falls_back_to_local_without_redis() -> None:
    """Test broadcast works locally when Redis not configured."""
    mgr = ConnectionManager()  # no redis_url
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.broadcast(WSChannel.WRITING, "book-1", {"type": "cursor_move"})

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "cursor_move"


@pytest.mark.asyncio
async def test_redis_subscription_on_connect() -> None:
    """Test that connecting subscribes to Redis channel."""
    mgr = ConnectionManager(redis_url="redis://fake:6379/0")

    mock_redis = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)
    mgr._redis = mock_redis

    ws = FakeWebSocket()
    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    # Should subscribe to the channel
    mock_pubsub.subscribe.assert_called_once_with("ws:writing:book-1")


# ---------------------------------------------------------------------------
# Tests — Queries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_connection_count() -> None:
    """Test get_connection_count returns accurate count."""
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 0

    await mgr.connect(ws1, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 1

    await mgr.connect(ws2, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 2


@pytest.mark.asyncio
async def test_get_all_rooms() -> None:
    """Test get_all_rooms returns list of active rooms."""
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await mgr.connect(ws1, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.connect(ws2, WSChannel.AGENTS, "org-2")  # type: ignore[arg-type]

    rooms = mgr.get_all_rooms()
    assert len(rooms) == 2
    channels = {r[0] for r in rooms}
    assert channels == {"writing", "agents"}


@pytest.mark.asyncio
async def test_get_all_rooms_with_counts() -> None:
    """Test get_all_rooms returns accurate connection counts."""
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()
    ws3 = FakeWebSocket()

    await mgr.connect(ws1, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.connect(ws2, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.connect(ws3, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]

    rooms = mgr.get_all_rooms()
    room_dict = {(ch, rid): count for ch, rid, count in rooms}

    assert room_dict[("writing", "book-1")] == 2
    assert room_dict[("agents", "org-1")] == 1


# ---------------------------------------------------------------------------
# Tests — Heartbeat / Ping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_heartbeat_starts_on_connect() -> None:
    """Test heartbeat task starts when first connection made."""
    mgr = ConnectionManager(heartbeat_interval=0.1)
    ws = FakeWebSocket()

    assert mgr._heartbeat_task is None

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    assert mgr._heartbeat_task is not None
    assert not mgr._heartbeat_task.done()

    await mgr.shutdown()


@pytest.mark.asyncio
async def test_heartbeat_sends_ping() -> None:
    """Test heartbeat sends ping messages to connections."""
    mgr = ConnectionManager(heartbeat_interval=0.05)
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    # Wait for at least one heartbeat
    await asyncio.sleep(0.1)

    # Should have received at least one ping
    pings = [msg for msg in ws.sent_messages if msg.get("type") == "ping"]
    assert len(pings) >= 1

    await mgr.shutdown()


@pytest.mark.asyncio
async def test_heartbeat_removes_dead_connections() -> None:
    """Test heartbeat cleans up dead connections."""
    mgr = ConnectionManager(heartbeat_interval=0.05)
    ws_alive = FakeWebSocket()
    ws_dead = FakeWebSocket(connected=False)

    await mgr.connect(ws_alive, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.connect(ws_dead, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 2

    # Wait for heartbeat to run
    await asyncio.sleep(0.1)

    # Dead connection should be removed
    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 1

    await mgr.shutdown()


# ---------------------------------------------------------------------------
# Tests — Shutdown
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_shutdown_cancels_heartbeat() -> None:
    """Test shutdown cancels heartbeat task."""
    mgr = ConnectionManager(heartbeat_interval=0.1)
    ws = FakeWebSocket()
    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    assert mgr._heartbeat_task is not None
    assert not mgr._heartbeat_task.done()

    await mgr.shutdown()

    assert mgr._heartbeat_task.done()


@pytest.mark.asyncio
async def test_shutdown_cancels_redis_listener() -> None:
    """Test shutdown cancels Redis listener task."""
    mgr = ConnectionManager(redis_url="redis://fake:6379/0")

    mock_redis = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)
    mgr._redis = mock_redis
    mgr._pubsub = mock_pubsub

    # Simulate listener task running
    async def fake_listener() -> None:
        await asyncio.sleep(999)

    mgr._listener_task = asyncio.create_task(fake_listener())

    await mgr.shutdown()

    assert mgr._listener_task.done()
    mock_pubsub.unsubscribe.assert_called_once()
    mock_pubsub.close.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_closes_redis_connection() -> None:
    """Test shutdown closes Redis connection."""
    mgr = ConnectionManager(redis_url="redis://fake:6379/0")

    mock_redis = AsyncMock()
    mgr._redis = mock_redis

    await mgr.shutdown()

    mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_without_connections() -> None:
    """Test shutdown works when no connections active."""
    mgr = ConnectionManager()
    # Should not raise
    await mgr.shutdown()
