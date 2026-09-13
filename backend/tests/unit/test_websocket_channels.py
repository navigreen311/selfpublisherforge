"""Unit tests for WebSocket channel subscriptions and message routing.

Tests cover:
- Subscribe to channel
- Unsubscribe from channel
- Channel message routing
- Channel permissions (can't subscribe to other org's channels)
- Manuscript editing channel (WRITING)
- Notification channel (AGENTS)
- Pricing updates channel (ANALYTICS)
- Publishing updates channel (PUBLISHING)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from app.modules.realtime.manager import ConnectionManager
from app.modules.realtime.schemas import WSChannel

# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------


class FakeWebSocket:
    """Minimal WebSocket for testing."""

    def __init__(self) -> None:
        self.accepted = False
        self.sent_messages: list[dict[str, Any]] = []

        from starlette.websockets import WebSocketState

        self.client_state = WebSocketState.CONNECTED

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: dict[str, Any]) -> None:
        self.sent_messages.append(data)


# ---------------------------------------------------------------------------
# Tests — Channel Subscription
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscribe_to_writing_channel() -> None:
    """Test subscribing to writing channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]

    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 1


@pytest.mark.asyncio
async def test_subscribe_to_agents_channel() -> None:
    """Test subscribing to agents channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]

    assert mgr.get_connection_count(WSChannel.AGENTS, "org-1") == 1


@pytest.mark.asyncio
async def test_subscribe_to_analytics_channel() -> None:
    """Test subscribing to analytics channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.ANALYTICS, "org-1")  # type: ignore[arg-type]

    assert mgr.get_connection_count(WSChannel.ANALYTICS, "org-1") == 1


@pytest.mark.asyncio
async def test_subscribe_to_publishing_channel() -> None:
    """Test subscribing to publishing channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.PUBLISHING, "book-1")  # type: ignore[arg-type]

    assert mgr.get_connection_count(WSChannel.PUBLISHING, "book-1") == 1


@pytest.mark.asyncio
async def test_subscribe_to_multiple_channels() -> None:
    """Test single client subscribing to multiple channels."""
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await mgr.connect(ws1, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.connect(ws2, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]

    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 1
    assert mgr.get_connection_count(WSChannel.AGENTS, "org-1") == 1


# ---------------------------------------------------------------------------
# Tests — Unsubscribe from Channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unsubscribe_from_channel() -> None:
    """Test unsubscribing removes connection from channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 1

    await mgr.disconnect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.WRITING, "book-1") == 0


@pytest.mark.asyncio
async def test_unsubscribe_cleans_up_channel() -> None:
    """Test unsubscribing last client cleans up channel."""
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await mgr.connect(ws1, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.connect(ws2, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]

    await mgr.disconnect(ws1, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.AGENTS, "org-1") == 1

    await mgr.disconnect(ws2, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    assert mgr.get_connection_count(WSChannel.AGENTS, "org-1") == 0
    assert (WSChannel.AGENTS, "org-1") not in mgr.active_connections


# ---------------------------------------------------------------------------
# Tests — Channel Message Routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_message_routes_to_correct_channel() -> None:
    """Test messages only go to the specified channel."""
    mgr = ConnectionManager()
    ws_writing = FakeWebSocket()
    ws_agents = FakeWebSocket()

    await mgr.connect(ws_writing, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.connect(ws_agents, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]

    # Send to WRITING channel
    await mgr.broadcast(WSChannel.WRITING, "book-1", {"type": "text_change"})

    assert len(ws_writing.sent_messages) == 1
    assert len(ws_agents.sent_messages) == 0


@pytest.mark.asyncio
async def test_message_routes_to_correct_room() -> None:
    """Test messages only go to the specified room ID."""
    mgr = ConnectionManager()
    ws_room_a = FakeWebSocket()
    ws_room_b = FakeWebSocket()

    await mgr.connect(ws_room_a, WSChannel.WRITING, "book-a")  # type: ignore[arg-type]
    await mgr.connect(ws_room_b, WSChannel.WRITING, "book-b")  # type: ignore[arg-type]

    # Send to room-a
    await mgr.broadcast(WSChannel.WRITING, "book-a", {"type": "cursor_move"})

    assert len(ws_room_a.sent_messages) == 1
    assert len(ws_room_b.sent_messages) == 0


@pytest.mark.asyncio
async def test_broadcast_to_all_in_same_channel() -> None:
    """Test broadcast sends to all subscribers in same channel."""
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()
    ws3 = FakeWebSocket()

    await mgr.connect(ws1, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.connect(ws2, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.connect(ws3, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]

    await mgr.broadcast(WSChannel.AGENTS, "org-1", {"type": "task_started"})

    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 1
    assert len(ws3.sent_messages) == 1


# ---------------------------------------------------------------------------
# Tests — WRITING Channel (Manuscript Editing)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_writing_channel_cursor_move() -> None:
    """Test cursor_move events on writing channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.WRITING,
        "book-1",
        {
            "type": "cursor_move",
            "user_id": "user-1",
            "position": 42,
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "cursor_move"


@pytest.mark.asyncio
async def test_writing_channel_text_change() -> None:
    """Test text_change events on writing channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.WRITING,
        "book-1",
        {
            "type": "text_change",
            "user_id": "user-1",
            "offset": 10,
            "length": 5,
            "text": "hello",
            "revision": 3,
        },
    )

    assert len(ws.sent_messages) == 1
    msg = ws.sent_messages[0]
    assert msg["type"] == "text_change"


@pytest.mark.asyncio
async def test_writing_channel_ai_suggestion() -> None:
    """Test ai_suggestion events on writing channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.WRITING,
        "book-1",
        {
            "type": "ai_suggestion",
            "suggestion_id": "sug-1",
            "text": "Consider rephrasing...",
            "position": 100,
            "confidence": 0.85,
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "ai_suggestion"


@pytest.mark.asyncio
async def test_writing_channel_save_ack() -> None:
    """Test save_ack events on writing channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.WRITING,
        "book-1",
        {
            "type": "save_ack",
            "revision": 5,
            "saved_at": datetime.now(UTC).isoformat(),
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "save_ack"


# ---------------------------------------------------------------------------
# Tests — AGENTS Channel (Notifications)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agents_channel_task_started() -> None:
    """Test task_started events on agents channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.AGENTS,
        "org-1",
        {
            "type": "task_started",
            "task_id": "task-1",
            "task_type": "content_generation",
            "agent_name": "writer_agent",
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "task_started"


@pytest.mark.asyncio
async def test_agents_channel_task_progress() -> None:
    """Test task_progress events on agents channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.AGENTS,
        "org-1",
        {
            "type": "task_progress",
            "task_id": "task-1",
            "progress": 50.0,
            "message": "Halfway done",
        },
    )

    assert len(ws.sent_messages) == 1
    msg = ws.sent_messages[0]
    assert msg["type"] == "task_progress"


@pytest.mark.asyncio
async def test_agents_channel_task_completed() -> None:
    """Test task_completed events on agents channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.AGENTS,
        "org-1",
        {
            "type": "task_completed",
            "task_id": "task-1",
            "result_summary": "Generated 5000 words",
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "task_completed"


@pytest.mark.asyncio
async def test_agents_channel_task_failed() -> None:
    """Test task_failed events on agents channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.AGENTS,
        "org-1",
        {
            "type": "task_failed",
            "task_id": "task-1",
            "error": "API rate limit exceeded",
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "task_failed"


@pytest.mark.asyncio
async def test_agents_channel_budget_alert() -> None:
    """Test budget_alert events on agents channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.AGENTS,
        "org-1",
        {
            "type": "budget_alert",
            "current_spend": 95.0,
            "budget_limit": 100.0,
            "alert_type": "warning",
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "budget_alert"


# ---------------------------------------------------------------------------
# Tests — ANALYTICS Channel (Pricing Updates)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analytics_channel_metric_update() -> None:
    """Test metric_update events on analytics channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.ANALYTICS, "org-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.ANALYTICS,
        "org-1",
        {
            "type": "metric_update",
            "metric_name": "sales",
            "value": 150.0,
            "dimensions": {"book_id": "book-1", "platform": "amazon"},
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "metric_update"


@pytest.mark.asyncio
async def test_analytics_channel_alert_triggered() -> None:
    """Test alert_triggered events on analytics channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.ANALYTICS, "org-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.ANALYTICS,
        "org-1",
        {
            "type": "alert_triggered",
            "alert_id": "alert-1",
            "severity": "high",
            "message": "Sales dropped below threshold",
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "alert_triggered"


@pytest.mark.asyncio
async def test_analytics_channel_report_ready() -> None:
    """Test report_ready events on analytics channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.ANALYTICS, "org-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.ANALYTICS,
        "org-1",
        {
            "type": "report_ready",
            "report_id": "report-1",
            "report_type": "monthly_sales",
            "download_url": "https://example.com/report.pdf",
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "report_ready"


# ---------------------------------------------------------------------------
# Tests — PUBLISHING Channel (Updates)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publishing_channel_validation_progress() -> None:
    """Test validation_progress events on publishing channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.PUBLISHING, "book-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.PUBLISHING,
        "book-1",
        {
            "type": "validation_progress",
            "step": "checking_cover",
            "total_steps": 5,
            "current_step": 2,
            "passed": True,
            "message": "Cover dimensions valid",
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "validation_progress"


@pytest.mark.asyncio
async def test_publishing_channel_upload_progress() -> None:
    """Test upload_progress events on publishing channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.PUBLISHING, "book-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.PUBLISHING,
        "book-1",
        {
            "type": "upload_progress",
            "platform": "amazon",
            "progress": 75.0,
            "file_name": "book.epub",
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "upload_progress"


@pytest.mark.asyncio
async def test_publishing_channel_listing_synced() -> None:
    """Test listing_synced events on publishing channel."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.PUBLISHING, "book-1")  # type: ignore[arg-type]
    await mgr.broadcast(
        WSChannel.PUBLISHING,
        "book-1",
        {
            "type": "listing_synced",
            "platform": "amazon",
            "listing_url": "https://amazon.com/dp/B123",
            "status": "live",
        },
    )

    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "listing_synced"


# ---------------------------------------------------------------------------
# Tests — Channel Permissions (Organization Scoping)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_channel_isolation_between_orgs() -> None:
    """Test messages don't leak between different organizations."""
    mgr = ConnectionManager()
    ws_org1 = FakeWebSocket()
    ws_org2 = FakeWebSocket()

    await mgr.connect(ws_org1, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]
    await mgr.connect(ws_org2, WSChannel.AGENTS, "org-2")  # type: ignore[arg-type]

    # Send to org-1
    await mgr.broadcast(WSChannel.AGENTS, "org-1", {"type": "task_started", "task_id": "t1"})

    assert len(ws_org1.sent_messages) == 1
    assert len(ws_org2.sent_messages) == 0


@pytest.mark.asyncio
async def test_channel_isolation_between_books() -> None:
    """Test messages don't leak between different books."""
    mgr = ConnectionManager()
    ws_book1 = FakeWebSocket()
    ws_book2 = FakeWebSocket()

    await mgr.connect(ws_book1, WSChannel.WRITING, "book-1")  # type: ignore[arg-type]
    await mgr.connect(ws_book2, WSChannel.WRITING, "book-2")  # type: ignore[arg-type]

    # Send to book-1
    await mgr.broadcast(WSChannel.WRITING, "book-1", {"type": "text_change"})

    assert len(ws_book1.sent_messages) == 1
    assert len(ws_book2.sent_messages) == 0


@pytest.mark.asyncio
async def test_multiple_orgs_same_channel() -> None:
    """Test multiple organizations can use same channel type."""
    mgr = ConnectionManager()
    ws_org1 = FakeWebSocket()
    ws_org2 = FakeWebSocket()

    await mgr.connect(ws_org1, WSChannel.ANALYTICS, "org-1")  # type: ignore[arg-type]
    await mgr.connect(ws_org2, WSChannel.ANALYTICS, "org-2")  # type: ignore[arg-type]

    # Each org receives its own messages
    await mgr.broadcast(WSChannel.ANALYTICS, "org-1", {"type": "metric_update", "org": "1"})
    await mgr.broadcast(WSChannel.ANALYTICS, "org-2", {"type": "metric_update", "org": "2"})

    assert len(ws_org1.sent_messages) == 1
    assert ws_org1.sent_messages[0].get("org") == "1"

    assert len(ws_org2.sent_messages) == 1
    assert ws_org2.sent_messages[0].get("org") == "2"


# ---------------------------------------------------------------------------
# Tests — Message Ordering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_message_ordering_preserved() -> None:
    """Test messages are received in the order they are sent."""
    mgr = ConnectionManager()
    ws = FakeWebSocket()

    await mgr.connect(ws, WSChannel.AGENTS, "org-1")  # type: ignore[arg-type]

    # Send multiple messages in sequence
    for i in range(5):
        await mgr.broadcast(WSChannel.AGENTS, "org-1", {"type": "test", "seq": i})

    assert len(ws.sent_messages) == 5
    for i, msg in enumerate(ws.sent_messages):
        assert msg["seq"] == i
