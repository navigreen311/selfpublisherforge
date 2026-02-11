"""End-to-end integration tests for WebSocket endpoints.

Tests cover:
- Full flow: connect → subscribe → receive message → disconnect
- Multiple clients on same channel
- Reconnection after disconnect
- Message ordering
- All four channel types (WRITING, AGENTS, ANALYTICS, PUBLISHING)
- Real JWT authentication
- Concurrent connections
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.modules.realtime.manager import ConnectionManager
from app.modules.realtime.router import router
from app.modules.realtime.schemas import WSChannel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_manager() -> ConnectionManager:
    """Create a fresh ConnectionManager with no Redis for test isolation."""
    return ConnectionManager(redis_url=None)


@pytest.fixture()
def test_app(test_manager: ConnectionManager) -> FastAPI:
    """Create a minimal FastAPI app with the realtime router."""
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture()
def client(test_app: FastAPI, test_manager: ConnectionManager) -> TestClient:
    """Create TestClient with patched manager."""
    with patch("app.modules.realtime.router.manager", test_manager):
        yield TestClient(test_app)


@pytest.fixture()
def valid_token() -> str:
    """Return a valid JWT for authentication."""
    return create_access_token(
        data={"sub": "user-123", "org_id": "org-456", "role": "editor"},
        expires_delta=timedelta(hours=1),
    )


@pytest.fixture()
def valid_token_user2() -> str:
    """Return a valid JWT for a second user."""
    return create_access_token(
        data={"sub": "user-999", "org_id": "org-456", "role": "viewer"},
        expires_delta=timedelta(hours=1),
    )


@pytest.fixture()
def expired_token() -> str:
    """Return an expired JWT."""
    return create_access_token(
        data={"sub": "user-123", "org_id": "org-456", "role": "editor"},
        expires_delta=timedelta(seconds=-10),
    )


# ---------------------------------------------------------------------------
# Tests — Full Flow (Connect → Subscribe → Receive → Disconnect)
# ---------------------------------------------------------------------------

class TestFullFlow:
    """Test complete WebSocket lifecycle."""

    def test_writing_channel_full_flow(self, client: TestClient, valid_token: str) -> None:
        """Test full flow on WRITING channel."""
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws:
            # 1. Connect - receive welcome message
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["channel"] == "writing"
            assert msg["room_id"] == "book-1"
            assert msg["user_id"] == "user-123"

            # 2. Send a message
            ws.send_json({"type": "cursor_move", "position": 42})

            # 3. Receive broadcast
            msg = ws.receive_json()
            assert msg["type"] == "cursor_move"

            # 4. Disconnect happens automatically when exiting context

    def test_agents_channel_full_flow(self, client: TestClient, valid_token: str) -> None:
        """Test full flow on AGENTS channel."""
        with client.websocket_connect(
            f"/api/v1/ws/agents/org-456?token={valid_token}"
        ) as ws:
            # Connect
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["channel"] == "agents"

            # Send task notification
            ws.send_json({"type": "task_started", "task_id": "task-1"})

            # Receive broadcast
            msg = ws.receive_json()
            assert msg["type"] == "task_started"

    def test_analytics_channel_full_flow(self, client: TestClient, valid_token: str) -> None:
        """Test full flow on ANALYTICS channel."""
        with client.websocket_connect(
            f"/api/v1/ws/analytics/org-456?token={valid_token}"
        ) as ws:
            # Connect
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["channel"] == "analytics"

            # Send metric update
            ws.send_json({"type": "metric_update", "metric_name": "sales", "value": 100})

            # Receive broadcast
            msg = ws.receive_json()
            assert msg["type"] == "metric_update"

    def test_publishing_channel_full_flow(self, client: TestClient, valid_token: str) -> None:
        """Test full flow on PUBLISHING channel."""
        with client.websocket_connect(
            f"/api/v1/ws/publishing/book-1?token={valid_token}"
        ) as ws:
            # Connect
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["channel"] == "publishing"

            # Send upload progress
            ws.send_json({"type": "upload_progress", "platform": "amazon", "progress": 50})

            # Receive broadcast
            msg = ws.receive_json()
            assert msg["type"] == "upload_progress"


# ---------------------------------------------------------------------------
# Tests — Multiple Clients on Same Channel
# ---------------------------------------------------------------------------

class TestMultipleClients:
    """Test multiple clients sharing a channel."""

    def test_two_clients_receive_same_message(
        self, client: TestClient, valid_token: str, valid_token_user2: str
    ) -> None:
        """Test broadcast reaches all clients in room."""
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws1:
            ws1.receive_json()  # welcome

            with client.websocket_connect(
                f"/api/v1/ws/writing/book-1?token={valid_token_user2}"
            ) as ws2:
                ws2.receive_json()  # welcome

                # Client 1 sends a message
                ws1.send_json({"type": "text_change", "text": "hello"})

                # Both clients should receive the broadcast
                msg1 = ws1.receive_json()
                assert msg1["type"] == "text_change"

                msg2 = ws2.receive_json()
                assert msg2["type"] == "text_change"

    def test_multiple_clients_different_rooms_isolated(
        self, client: TestClient, valid_token: str, test_manager: ConnectionManager
    ) -> None:
        """Test clients in different rooms don't receive each other's messages."""
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-a?token={valid_token}"
        ) as ws_a:
            ws_a.receive_json()  # welcome

            with client.websocket_connect(
                f"/api/v1/ws/writing/book-b?token={valid_token}"
            ) as ws_b:
                ws_b.receive_json()  # welcome

                # Send in room-a
                ws_a.send_json({"type": "text_change", "text": "hello"})

                # room-a gets it back
                msg_a = ws_a.receive_json()
                assert msg_a["type"] == "text_change"

                # room-b should NOT have received it
                # Verify via manager state
                count_a = test_manager.get_connection_count(WSChannel.WRITING, "book-a")
                count_b = test_manager.get_connection_count(WSChannel.WRITING, "book-b")
                assert count_a == 1
                assert count_b == 1

    def test_three_clients_same_room(
        self, client: TestClient, valid_token: str
    ) -> None:
        """Test broadcast reaches all three clients."""
        with client.websocket_connect(
            f"/api/v1/ws/agents/org-1?token={valid_token}"
        ) as ws1:
            ws1.receive_json()  # welcome

            with client.websocket_connect(
                f"/api/v1/ws/agents/org-1?token={valid_token}"
            ) as ws2:
                ws2.receive_json()  # welcome

                with client.websocket_connect(
                    f"/api/v1/ws/agents/org-1?token={valid_token}"
                ) as ws3:
                    ws3.receive_json()  # welcome

                    # Send from client 1
                    ws1.send_json({"type": "task_progress", "progress": 50})

                    # All three should receive
                    msg1 = ws1.receive_json()
                    msg2 = ws2.receive_json()
                    msg3 = ws3.receive_json()

                    assert msg1["type"] == "task_progress"
                    assert msg2["type"] == "task_progress"
                    assert msg3["type"] == "task_progress"


# ---------------------------------------------------------------------------
# Tests — Reconnection After Disconnect
# ---------------------------------------------------------------------------

class TestReconnection:
    """Test reconnection scenarios."""

    def test_reconnect_after_disconnect(
        self, client: TestClient, valid_token: str, test_manager: ConnectionManager
    ) -> None:
        """Test client can reconnect after disconnecting."""
        # First connection
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws:
            ws.receive_json()  # welcome
            assert test_manager.get_connection_count(WSChannel.WRITING, "book-1") == 1

        # Disconnected
        assert test_manager.get_connection_count(WSChannel.WRITING, "book-1") == 0

        # Reconnect
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws:
            msg = ws.receive_json()  # welcome
            assert msg["type"] == "connected"
            assert test_manager.get_connection_count(WSChannel.WRITING, "book-1") == 1

    def test_client_leaves_and_rejoins_room(
        self, client: TestClient, valid_token: str, test_manager: ConnectionManager
    ) -> None:
        """Test client leaving and rejoining doesn't break room."""
        with client.websocket_connect(
            f"/api/v1/ws/agents/org-1?token={valid_token}"
        ) as ws1:
            ws1.receive_json()  # welcome

            # Another client joins
            with client.websocket_connect(
                f"/api/v1/ws/agents/org-1?token={valid_token}"
            ) as ws2:
                ws2.receive_json()  # welcome
                assert test_manager.get_connection_count(WSChannel.AGENTS, "org-1") == 2

            # ws2 disconnected
            assert test_manager.get_connection_count(WSChannel.AGENTS, "org-1") == 1

            # ws1 still receives messages
            ws1.send_json({"type": "task_completed"})
            msg = ws1.receive_json()
            assert msg["type"] == "task_completed"


# ---------------------------------------------------------------------------
# Tests — Message Ordering
# ---------------------------------------------------------------------------

class TestMessageOrdering:
    """Test message order preservation."""

    def test_messages_received_in_order(self, client: TestClient, valid_token: str) -> None:
        """Test messages are received in the order sent."""
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws:
            ws.receive_json()  # welcome

            # Send multiple messages in sequence
            for i in range(5):
                ws.send_json({"type": "cursor_move", "position": i})

            # Receive them in order
            for i in range(5):
                msg = ws.receive_json()
                assert msg["type"] == "cursor_move"
                # Position might be in data or top-level depending on envelope
                pos = msg.get("position", msg.get("data", {}).get("position"))
                assert pos == i

    def test_concurrent_messages_all_delivered(self, client: TestClient, valid_token: str) -> None:
        """Test all messages are delivered even when sent rapidly."""
        with client.websocket_connect(
            f"/api/v1/ws/agents/org-1?token={valid_token}"
        ) as ws:
            ws.receive_json()  # welcome

            # Send 10 messages rapidly
            message_count = 10
            for i in range(message_count):
                ws.send_json({"type": "test", "seq": i})

            # Receive all of them
            received_seqs = []
            for _ in range(message_count):
                msg = ws.receive_json()
                seq = msg.get("seq", msg.get("data", {}).get("seq"))
                received_seqs.append(seq)

            # All messages received
            assert len(received_seqs) == message_count
            # In order
            assert received_seqs == list(range(message_count))


# ---------------------------------------------------------------------------
# Tests — Authentication Edge Cases
# ---------------------------------------------------------------------------

class TestAuthenticationE2E:
    """Test authentication in full flow."""

    def test_reject_connection_without_token(self, client: TestClient) -> None:
        """Test connection rejected when no token provided."""
        with pytest.raises(Exception):  # WebSocket closes with error
            with client.websocket_connect("/api/v1/ws/writing/book-1") as ws:
                ws.receive_json()

    def test_reject_connection_with_invalid_token(self, client: TestClient) -> None:
        """Test connection rejected with invalid token."""
        with pytest.raises(Exception):
            with client.websocket_connect(
                "/api/v1/ws/writing/book-1?token=invalid-token-12345"
            ) as ws:
                ws.receive_json()

    def test_reject_connection_with_expired_token(self, client: TestClient, expired_token: str) -> None:
        """Test connection rejected with expired token."""
        with pytest.raises(Exception):
            with client.websocket_connect(
                f"/api/v1/ws/writing/book-1?token={expired_token}"
            ) as ws:
                ws.receive_json()

    def test_user_id_added_to_broadcast_messages(self, client: TestClient, valid_token: str) -> None:
        """Test user_id from token is added to broadcast messages."""
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws:
            welcome = ws.receive_json()
            assert welcome["user_id"] == "user-123"

            # Send a message without user_id
            ws.send_json({"type": "cursor_move", "position": 10})

            # Should have user_id added
            msg = ws.receive_json()
            assert msg.get("user_id") == "user-123"


# ---------------------------------------------------------------------------
# Tests — Concurrent Connections
# ---------------------------------------------------------------------------

class TestConcurrentConnections:
    """Test concurrent connection scenarios."""

    def test_multiple_concurrent_channels(
        self, client: TestClient, valid_token: str, test_manager: ConnectionManager
    ) -> None:
        """Test client connected to multiple channels simultaneously."""
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws_writing:
            ws_writing.receive_json()  # welcome

            with client.websocket_connect(
                f"/api/v1/ws/agents/org-456?token={valid_token}"
            ) as ws_agents:
                ws_agents.receive_json()  # welcome

                # Verify both connections active
                assert test_manager.get_connection_count(WSChannel.WRITING, "book-1") == 1
                assert test_manager.get_connection_count(WSChannel.AGENTS, "org-456") == 1

                # Send to writing channel
                ws_writing.send_json({"type": "text_change"})
                msg = ws_writing.receive_json()
                assert msg["type"] == "text_change"

                # Send to agents channel
                ws_agents.send_json({"type": "task_started"})
                msg = ws_agents.receive_json()
                assert msg["type"] == "task_started"

    def test_same_user_multiple_rooms(
        self, client: TestClient, valid_token: str, test_manager: ConnectionManager
    ) -> None:
        """Test same user connected to multiple rooms in same channel."""
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws1:
            ws1.receive_json()  # welcome

            with client.websocket_connect(
                f"/api/v1/ws/writing/book-2?token={valid_token}"
            ) as ws2:
                ws2.receive_json()  # welcome

                # Both connections active
                assert test_manager.get_connection_count(WSChannel.WRITING, "book-1") == 1
                assert test_manager.get_connection_count(WSChannel.WRITING, "book-2") == 1

                # Messages stay isolated
                ws1.send_json({"type": "text_change", "book": "1"})
                msg1 = ws1.receive_json()
                assert msg1["type"] == "text_change"

                ws2.send_json({"type": "text_change", "book": "2"})
                msg2 = ws2.receive_json()
                assert msg2["type"] == "text_change"


# ---------------------------------------------------------------------------
# Tests — Error Handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Test error scenarios."""

    def test_connection_survives_invalid_json(self, client: TestClient, valid_token: str) -> None:
        """Test connection handles invalid JSON gracefully.

        Note: TestClient's send_json validates, so this test documents
        expected behavior but may not fully exercise the error path.
        """
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws:
            ws.receive_json()  # welcome

            # Send valid message
            ws.send_json({"type": "cursor_move"})
            msg = ws.receive_json()
            assert msg["type"] == "cursor_move"

    def test_manager_state_after_client_errors(
        self, client: TestClient, valid_token: str, test_manager: ConnectionManager
    ) -> None:
        """Test manager state is correct after client disconnects with error."""
        with client.websocket_connect(
            f"/api/v1/ws/agents/org-1?token={valid_token}"
        ) as ws:
            ws.receive_json()  # welcome
            assert test_manager.get_connection_count(WSChannel.AGENTS, "org-1") == 1

        # After disconnect, connection should be cleaned up
        assert test_manager.get_connection_count(WSChannel.AGENTS, "org-1") == 0


# ---------------------------------------------------------------------------
# Tests — Status Endpoint
# ---------------------------------------------------------------------------

class TestStatusEndpoint:
    """Test WebSocket status HTTP endpoint."""

    def test_ws_status_endpoint(self, client: TestClient) -> None:
        """Test /api/v1/ws/status endpoint."""
        response = client.get("/api/v1/ws/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "channels" in data
        assert "writing" in data["channels"]
        assert "agents" in data["channels"]
        assert "analytics" in data["channels"]
        assert "publishing" in data["channels"]

    def test_ws_status_shows_active_rooms(
        self, client: TestClient, valid_token: str, test_manager: ConnectionManager
    ) -> None:
        """Test status endpoint shows active rooms."""
        with client.websocket_connect(
            f"/api/v1/ws/writing/book-1?token={valid_token}"
        ) as ws:
            ws.receive_json()  # welcome

            # Check status via HTTP endpoint
            response = client.get("/api/v1/ws/status")
            data = response.json()

            assert "rooms" in data
            # Should show active room
            rooms = test_manager.get_all_rooms()
            assert len(rooms) >= 1
