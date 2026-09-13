"""Integration tests for the notifications API endpoints.

These tests exercise the full FastAPI router with a mocked database session
and mocked authentication, simulating how a real client would interact with
the notification endpoints.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.modules.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationType,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_USER_ID = uuid.uuid4()
TEST_ORG_ID = uuid.uuid4()
TEST_USER = {"user_id": TEST_USER_ID, "org_id": TEST_ORG_ID, "role": "admin"}


def _make_notification(
    *,
    nid: uuid.UUID | None = None,
    read: bool = False,
    n_type: NotificationType = NotificationType.INFO,
) -> MagicMock:
    """Helper to build a mock Notification object."""
    n = MagicMock(spec=Notification)
    n.id = nid or uuid.uuid4()
    n.org_id = TEST_ORG_ID
    n.user_id = TEST_USER_ID
    n.type = n_type
    n.title = "Test Notification"
    n.message = "This is a test"
    n.data = {"action": "test"}
    n.read_at = datetime.now(UTC) if read else None
    n.created_at = datetime.now(UTC)
    return n


def _make_preference(
    *,
    channel: NotificationChannel = NotificationChannel.EMAIL,
    category: str = "marketing",
    enabled: bool = True,
) -> MagicMock:
    """Helper to build a mock NotificationPreference object."""
    p = MagicMock(spec=NotificationPreference)
    p.id = uuid.uuid4()
    p.user_id = TEST_USER_ID
    p.channel = channel
    p.category = category
    p.enabled = enabled
    return p


def _build_app():
    """Build a minimal FastAPI app with the notification router mounted."""
    from fastapi import FastAPI

    from app.modules.notifications.router import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/notifications", tags=["notifications"])
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestListNotifications:
    """GET /api/v1/notifications"""

    @patch("app.modules.notifications.router.service")
    @patch("app.modules.notifications.router.get_current_user")
    @patch("app.modules.notifications.router.get_db")
    async def test_list_empty(self, mock_get_db, mock_auth, mock_service):
        mock_auth.return_value = TEST_USER
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        mock_service.list_notifications = AsyncMock(return_value=([], None, False))

        app = _build_app()
        # Override dependencies
        app.dependency_overrides[
            __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: TEST_USER
        app.dependency_overrides[__import__("app.database", fromlist=["get_db"]).get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/notifications")

        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["has_more"] is False

    @patch("app.modules.notifications.router.service")
    async def test_list_with_items(self, mock_service):
        n1 = _make_notification()
        n2 = _make_notification(read=True)
        mock_service.list_notifications = AsyncMock(return_value=([n1, n2], "2024-01-01T00:00:00+00:00", True))

        app = _build_app()
        mock_db = AsyncMock()
        app.dependency_overrides[
            __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: TEST_USER
        app.dependency_overrides[__import__("app.database", fromlist=["get_db"]).get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/notifications?limit=2")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["has_more"] is True
        assert body["next_cursor"] is not None


@pytest.mark.asyncio
class TestMarkNotificationRead:
    """PATCH /api/v1/notifications/{id}/read"""

    @patch("app.modules.notifications.router.service")
    async def test_mark_as_read(self, mock_service):
        nid = uuid.uuid4()
        n = _make_notification(nid=nid, read=True)
        mock_service.mark_as_read = AsyncMock(return_value=n)

        app = _build_app()
        mock_db = AsyncMock()
        app.dependency_overrides[
            __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: TEST_USER
        app.dependency_overrides[__import__("app.database", fromlist=["get_db"]).get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch(f"/api/v1/notifications/{nid}/read")

        assert resp.status_code == 200
        body = resp.json()
        assert body["read_at"] is not None


@pytest.mark.asyncio
class TestMarkAllRead:
    """POST /api/v1/notifications/read-all"""

    @patch("app.modules.notifications.router.service")
    async def test_mark_all_read(self, mock_service):
        mock_service.mark_all_as_read = AsyncMock(return_value=3)

        app = _build_app()
        mock_db = AsyncMock()
        app.dependency_overrides[
            __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: TEST_USER
        app.dependency_overrides[__import__("app.database", fromlist=["get_db"]).get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/notifications/read-all")

        assert resp.status_code == 200
        body = resp.json()
        assert "3" in body["message"]


@pytest.mark.asyncio
class TestUnreadCount:
    """GET /api/v1/notifications/unread-count"""

    @patch("app.modules.notifications.router.service")
    async def test_unread_count(self, mock_service):
        mock_service.get_unread_count = AsyncMock(return_value=12)

        app = _build_app()
        mock_db = AsyncMock()
        app.dependency_overrides[
            __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: TEST_USER
        app.dependency_overrides[__import__("app.database", fromlist=["get_db"]).get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/notifications/unread-count")

        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 12


@pytest.mark.asyncio
class TestGetPreferences:
    """GET /api/v1/notifications/preferences"""

    @patch("app.modules.notifications.router.service")
    async def test_get_preferences_empty(self, mock_service):
        mock_service.get_preferences = AsyncMock(return_value=[])

        app = _build_app()
        mock_db = AsyncMock()
        app.dependency_overrides[
            __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: TEST_USER
        app.dependency_overrides[__import__("app.database", fromlist=["get_db"]).get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/notifications/preferences")

        assert resp.status_code == 200
        assert resp.json() == []

    @patch("app.modules.notifications.router.service")
    async def test_get_preferences_with_items(self, mock_service):
        p1 = _make_preference(channel=NotificationChannel.EMAIL, category="alerts", enabled=True)
        p2 = _make_preference(channel=NotificationChannel.IN_APP, category="alerts", enabled=False)
        mock_service.get_preferences = AsyncMock(return_value=[p1, p2])

        app = _build_app()
        mock_db = AsyncMock()
        app.dependency_overrides[
            __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: TEST_USER
        app.dependency_overrides[__import__("app.database", fromlist=["get_db"]).get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/notifications/preferences")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        channels = {item["channel"] for item in data}
        assert "email" in channels
        assert "in_app" in channels


@pytest.mark.asyncio
class TestUpdatePreferences:
    """PATCH /api/v1/notifications/preferences"""

    @patch("app.modules.notifications.router.service")
    async def test_update_preferences(self, mock_service):
        p = _make_preference(channel=NotificationChannel.EMAIL, category="marketing", enabled=False)
        mock_service.upsert_preferences = AsyncMock(return_value=[p])

        app = _build_app()
        mock_db = AsyncMock()
        app.dependency_overrides[
            __import__("app.core.dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: TEST_USER
        app.dependency_overrides[__import__("app.database", fromlist=["get_db"]).get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch(
                "/api/v1/notifications/preferences",
                json={
                    "preferences": [
                        {"channel": "email", "category": "marketing", "enabled": False},
                    ]
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["enabled"] is False
