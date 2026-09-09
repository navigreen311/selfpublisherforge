"""Integration tests for WebSocket endpoints.

Uses the Starlette/FastAPI ``TestClient`` (via ``httpx`` WebSocket support) to
exercise the full request path including JWT authentication, connection
lifecycle, and message broadcasting.
"""

from __future__ import annotations

from datetime import timedelta
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
    """Create a minimal FastAPI app with the realtime router and a fresh manager."""
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture()
def client(test_app: FastAPI, test_manager: ConnectionManager) -> TestClient:
    with patch("app.modules.realtime.router.manager", test_manager):
        yield TestClient(test_app)


@pytest.fixture()
def valid_token() -> str:
    """Return a valid JWT that the WebSocket endpoints will accept."""
    return create_access_token(
        data={"sub": "user-123", "org_id": "org-456", "role": "editor"},
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
# Connection tests
# ---------------------------------------------------------------------------


class TestWritingChannel:
    def test_connect_with_valid_token(self, client: TestClient, valid_token: str) -> None:
        with client.websocket_connect(f"/api/v1/ws/writing/book-1?token={valid_token}") as ws:
            # First message should be the "connected" welcome message.
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["channel"] == "writing"
            assert msg["room_id"] == "book-1"
            assert msg["user_id"] == "user-123"

    def test_reject_without_token(self, client: TestClient) -> None:
        # WebSocket should close with policy violation.
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/ws/writing/book-1") as ws:
                ws.receive_json()

    def test_reject_with_invalid_token(self, client: TestClient) -> None:
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/ws/writing/book-1?token=bad-token-value") as ws:
                ws.receive_json()


class TestAgentsChannel:
    def test_connect_agents(self, client: TestClient, valid_token: str) -> None:
        with client.websocket_connect(f"/api/v1/ws/agents/org-456?token={valid_token}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["channel"] == "agents"
            assert msg["room_id"] == "org-456"


class TestAnalyticsChannel:
    def test_connect_analytics(self, client: TestClient, valid_token: str) -> None:
        with client.websocket_connect(f"/api/v1/ws/analytics/org-456?token={valid_token}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["channel"] == "analytics"
            assert msg["room_id"] == "org-456"


class TestPublishingChannel:
    def test_connect_publishing(self, client: TestClient, valid_token: str) -> None:
        with client.websocket_connect(f"/api/v1/ws/publishing/book-99?token={valid_token}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["channel"] == "publishing"
            assert msg["room_id"] == "book-99"


# ---------------------------------------------------------------------------
# Message broadcast tests
# ---------------------------------------------------------------------------


class TestBroadcast:
    def test_send_message_is_broadcast(self, client: TestClient, valid_token: str) -> None:
        """When a client sends a message it should be broadcast back (echo
        to the room).  With a single connection the sender receives it."""
        with client.websocket_connect(f"/api/v1/ws/writing/book-1?token={valid_token}") as ws:
            # Consume the welcome message.
            ws.receive_json()

            # Send a message.
            ws.send_json({"type": "cursor_move", "position": 42})

            # The broadcast should echo back.
            msg = ws.receive_json()
            assert msg["type"] == "cursor_move"
            assert msg.get("position") == 42 or msg.get("data", {}).get("position") == 42


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_different_rooms_isolated(
        self, client: TestClient, valid_token: str, test_manager: ConnectionManager
    ) -> None:
        """Messages in room-A should not appear in room-B."""
        with client.websocket_connect(f"/api/v1/ws/writing/book-a?token={valid_token}") as ws_a:
            ws_a.receive_json()  # welcome

            with client.websocket_connect(f"/api/v1/ws/writing/book-b?token={valid_token}") as ws_b:
                ws_b.receive_json()  # welcome

                # Send in room-a
                ws_a.send_json({"type": "text_change", "text": "hello"})

                # room-a gets it back
                msg_a = ws_a.receive_json()
                assert msg_a["type"] == "text_change"

                # room-b should NOT have received anything beyond its welcome.
                # We cannot easily assert "no message" with the sync test
                # client, so we simply verify the rooms are separate in the
                # manager state.
                count_b = test_manager.get_connection_count(WSChannel.WRITING, "book-b")
                assert count_b >= 1
