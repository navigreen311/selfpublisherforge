"""Unit tests for the notifications service layer."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.notifications import service
from app.modules.notifications.models import NotificationChannel, NotificationType
from app.modules.notifications.schemas import CreateNotification, PreferenceItem


@pytest.mark.asyncio
async def test_create_notification_basic():
    """Test creating a basic in-app notification."""
    mock_db = AsyncMock()
    user_id = uuid4()
    org_id = uuid4()

    payload = CreateNotification(
        user_id=user_id,
        org_id=org_id,
        type=NotificationType.INFO,
        title="Test Notification",
        message="This is a test",
        data={"key": "value"},
    )

    result = await service.create_notification(mock_db, payload)

    assert result.user_id == user_id
    assert result.title == "Test Notification"


@pytest.mark.asyncio
async def test_create_notification_with_email():
    """Test creating a notification with email dispatch."""
    mock_db = AsyncMock()
    user_id = uuid4()
    org_id = uuid4()

    payload = CreateNotification(
        user_id=user_id,
        org_id=org_id,
        type=NotificationType.TEAM_INVITE,
        title="Team Invitation",
        message="You have been invited",
    )

    with (
        patch("app.modules.notifications.service.send_template_email") as mock_email,
        patch("app.modules.notifications.service.is_preference_enabled", return_value=True),
    ):
        mock_email.return_value = True

        result = await service.create_notification(
            mock_db,
            payload,
            recipient_email="test@example.com",
        )

        assert result.type == NotificationType.TEAM_INVITE
        mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_list_notifications():
    """Test listing user notifications with pagination."""
    mock_db = AsyncMock()
    user_id = uuid4()

    mock_notifs = []
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_notifs
    mock_db.execute.return_value = mock_result

    items, next_cursor, has_more = await service.list_notifications(mock_db, user_id)

    assert items == []
    assert next_cursor is None
    assert has_more is False


@pytest.mark.asyncio
async def test_mark_as_read():
    """Test marking a notification as read."""
    mock_db = AsyncMock()
    user_id = uuid4()
    notif_id = uuid4()

    mock_notif = MagicMock()
    mock_notif.id = notif_id
    mock_notif.read_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_notif
    mock_db.execute.return_value = mock_result

    result = await service.mark_as_read(mock_db, notif_id, user_id)

    assert result.read_at is not None


@pytest.mark.asyncio
async def test_get_unread_count():
    """Test getting unread notification count."""
    mock_db = AsyncMock()
    user_id = uuid4()

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 5
    mock_db.execute.return_value = mock_result

    count = await service.get_unread_count(mock_db, user_id)

    assert count == 5


@pytest.mark.asyncio
async def test_upsert_preferences():
    """Test upserting notification preferences."""
    mock_db = AsyncMock()
    user_id = uuid4()

    items = [
        PreferenceItem(
            channel=NotificationChannel.EMAIL,
            category="ai_complete",
            enabled=False,
        )
    ]

    mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

    with patch("app.modules.notifications.service.get_preferences", return_value=[]):
        result = await service.upsert_preferences(mock_db, user_id, items)

        assert isinstance(result, list)


@pytest.mark.asyncio
async def test_is_preference_enabled_default():
    """Test preference check returns True by default."""
    mock_db = AsyncMock()
    user_id = uuid4()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    enabled = await service.is_preference_enabled(
        mock_db,
        user_id,
        NotificationChannel.EMAIL,
        "ai_complete",
    )

    assert enabled is True
