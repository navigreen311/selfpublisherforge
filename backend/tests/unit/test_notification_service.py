"""Unit tests for the notification service layer and email module."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.notifications.email import (
    EMAIL_TEMPLATES,
    _build_html,
    send_transactional_email,
)
from app.modules.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationType,
)
from app.modules.notifications.schemas import (
    CreateNotification,
    NotificationOut,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    PreferenceItem,
    UnreadCountOut,
)


# ===================================================================
# Schema validation tests
# ===================================================================


class TestCreateNotificationSchema:
    """Validate the CreateNotification Pydantic model."""

    def test_valid_payload(self):
        uid = uuid.uuid4()
        oid = uuid.uuid4()
        payload = CreateNotification(
            user_id=uid,
            org_id=oid,
            type=NotificationType.INFO,
            title="Test title",
            message="Body text",
            data={"key": "value"},
        )
        assert payload.user_id == uid
        assert payload.org_id == oid
        assert payload.type == NotificationType.INFO
        assert payload.title == "Test title"
        assert payload.data == {"key": "value"}

    def test_default_type_is_info(self):
        payload = CreateNotification(
            user_id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            title="Hello",
            message="World",
        )
        assert payload.type == NotificationType.INFO

    def test_title_max_length(self):
        with pytest.raises(Exception):
            CreateNotification(
                user_id=uuid.uuid4(),
                org_id=uuid.uuid4(),
                title="A" * 256,  # exceeds 255
                message="msg",
            )

    def test_optional_data_defaults_to_none(self):
        payload = CreateNotification(
            user_id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            title="T",
            message="M",
        )
        assert payload.data is None


class TestNotificationOutSchema:
    """Validate the NotificationOut Pydantic model."""

    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        nid = uuid.uuid4()
        uid = uuid.uuid4()
        oid = uuid.uuid4()
        n = MagicMock()
        n.id = nid
        n.org_id = oid
        n.user_id = uid
        n.type = NotificationType.SUCCESS
        n.title = "Done"
        n.message = "Completed"
        n.data = None
        n.read_at = None
        n.created_at = now
        out = NotificationOut.model_validate(n, from_attributes=True)
        assert out.id == nid
        assert out.type == NotificationType.SUCCESS
        assert out.read_at is None


class TestUnreadCountOutSchema:
    def test_basic(self):
        out = UnreadCountOut(unread_count=5)
        assert out.unread_count == 5


class TestPreferenceSchemas:
    def test_preference_item(self):
        item = PreferenceItem(
            channel=NotificationChannel.EMAIL,
            category="marketing",
            enabled=False,
        )
        assert item.channel == NotificationChannel.EMAIL
        assert item.enabled is False

    def test_preference_update(self):
        update = NotificationPreferenceUpdate(
            preferences=[
                PreferenceItem(
                    channel=NotificationChannel.IN_APP,
                    category="alerts",
                    enabled=True,
                ),
            ]
        )
        assert len(update.preferences) == 1


# ===================================================================
# Enum tests
# ===================================================================


class TestNotificationEnums:
    def test_notification_types(self):
        assert NotificationType.INFO.value == "info"
        assert NotificationType.AI_COMPLETE.value == "ai_complete"
        assert NotificationType.PUBLISH_STATUS.value == "publish_status"
        assert NotificationType.TEAM_INVITE.value == "team_invite"

    def test_channels(self):
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.IN_APP.value == "in_app"
        assert NotificationChannel.PUSH.value == "push"


# ===================================================================
# Email template tests
# ===================================================================


class TestEmailTemplates:
    """Tests for the email template builder."""

    def test_all_expected_templates_exist(self):
        expected = {
            "welcome",
            "verification",
            "password_reset",
            "team_invite",
            "ai_task_complete",
            "publishing_status",
        }
        assert set(EMAIL_TEMPLATES.keys()) == expected

    def test_build_html_welcome(self):
        subject, html = _build_html("welcome", {"name": "Alice"})
        assert "Alice" in html
        assert "Welcome" in subject

    def test_build_html_verification(self):
        subject, html = _build_html(
            "verification",
            {"name": "Bob", "verification_url": "https://example.com/verify"},
        )
        assert "Bob" in html
        assert "https://example.com/verify" in html

    def test_build_html_password_reset(self):
        subject, html = _build_html(
            "password_reset",
            {"name": "Carol", "reset_url": "https://example.com/reset"},
        )
        assert "Carol" in html
        assert "Reset" in subject

    def test_build_html_team_invite(self):
        subject, html = _build_html(
            "team_invite",
            {"name": "Dave", "org_name": "Acme", "invite_url": "https://example.com/invite"},
        )
        assert "Acme" in subject
        assert "Acme" in html

    def test_build_html_ai_task_complete(self):
        subject, html = _build_html(
            "ai_task_complete",
            {"name": "Eve", "task_name": "Chapter Gen", "result_url": "https://example.com/result"},
        )
        assert "Chapter Gen" in html
        assert "AI" in subject

    def test_build_html_publishing_status(self):
        subject, html = _build_html(
            "publishing_status",
            {
                "name": "Frank",
                "book_title": "My Book",
                "status": "published",
                "book_url": "https://example.com/book",
            },
        )
        assert "My Book" in subject
        assert "published" in html

    def test_build_html_unknown_template_raises(self):
        with pytest.raises(ValueError, match="Unknown email template"):
            _build_html("nonexistent_template", {})


class TestSendTransactionalEmail:
    """Tests for the SendGrid integration wrapper."""

    @patch("app.modules.notifications.email.SendGridAPIClient")
    @patch("app.modules.notifications.email.get_settings")
    def test_send_email_success(self, mock_settings, mock_sg_cls):
        settings = MagicMock()
        settings.SENDGRID_API_KEY = "SG.test_key"
        settings.FROM_EMAIL = "noreply@test.com"
        mock_settings.return_value = settings

        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_sg_cls.return_value.send.return_value = mock_response

        result = send_transactional_email(
            to_email="user@example.com",
            template_name="welcome",
            context={"name": "Test User"},
        )
        assert result is True
        mock_sg_cls.return_value.send.assert_called_once()

    @patch("app.modules.notifications.email.SendGridAPIClient")
    @patch("app.modules.notifications.email.get_settings")
    def test_send_email_failure_status(self, mock_settings, mock_sg_cls):
        settings = MagicMock()
        settings.SENDGRID_API_KEY = "SG.test_key"
        settings.FROM_EMAIL = "noreply@test.com"
        mock_settings.return_value = settings

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_sg_cls.return_value.send.return_value = mock_response

        result = send_transactional_email(
            to_email="user@example.com",
            template_name="welcome",
            context={"name": "User"},
        )
        assert result is False

    @patch("app.modules.notifications.email.SendGridAPIClient")
    @patch("app.modules.notifications.email.get_settings")
    def test_send_email_exception(self, mock_settings, mock_sg_cls):
        settings = MagicMock()
        settings.SENDGRID_API_KEY = "SG.test_key"
        settings.FROM_EMAIL = "noreply@test.com"
        mock_settings.return_value = settings

        mock_sg_cls.return_value.send.side_effect = Exception("connection error")

        result = send_transactional_email(
            to_email="user@example.com",
            template_name="welcome",
            context={"name": "User"},
        )
        assert result is False

    @patch("app.modules.notifications.email.SendGridAPIClient")
    @patch("app.modules.notifications.email.get_settings")
    def test_subject_override(self, mock_settings, mock_sg_cls):
        settings = MagicMock()
        settings.SENDGRID_API_KEY = "SG.test_key"
        settings.FROM_EMAIL = "noreply@test.com"
        mock_settings.return_value = settings

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_sg_cls.return_value.send.return_value = mock_response

        result = send_transactional_email(
            to_email="user@example.com",
            template_name="welcome",
            context={"name": "User"},
            subject_override="Custom Subject",
        )
        assert result is True


# ===================================================================
# Service layer unit tests (mocked DB)
# ===================================================================


class TestNotificationServiceCreateNotification:
    """Test create_notification with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_create_notification(self):
        from app.modules.notifications.service import create_notification

        uid = uuid.uuid4()
        oid = uuid.uuid4()
        payload = CreateNotification(
            user_id=uid,
            org_id=oid,
            type=NotificationType.SUCCESS,
            title="Task done",
            message="Your task completed.",
        )

        mock_db = AsyncMock()

        # After flush + refresh the notification should have attrs set
        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh = fake_refresh

        notification = await create_notification(mock_db, payload)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        assert notification.title == "Task done"
        assert notification.user_id == uid
        assert notification.org_id == oid
        assert notification.type == NotificationType.SUCCESS


class TestNotificationServiceGetUnreadCount:
    """Test get_unread_count with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_get_unread_count(self):
        from app.modules.notifications.service import get_unread_count

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 7
        mock_db.execute.return_value = mock_result

        count = await get_unread_count(mock_db, uuid.uuid4())
        assert count == 7


class TestNotificationServiceMarkAsRead:
    """Test mark_as_read with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_mark_as_read_success(self):
        from app.modules.notifications.service import mark_as_read

        nid = uuid.uuid4()
        uid = uuid.uuid4()
        mock_notification = MagicMock(spec=Notification)
        mock_notification.id = nid
        mock_notification.user_id = uid
        mock_notification.read_at = None

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notification
        mock_db.execute.return_value = mock_result

        async def fake_refresh(obj):
            pass

        mock_db.refresh = fake_refresh

        result = await mark_as_read(mock_db, nid, uid)
        assert result.read_at is not None

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self):
        from app.core.exceptions import AppException
        from app.modules.notifications.service import mark_as_read

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(AppException) as exc_info:
            await mark_as_read(mock_db, uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "NOTIFICATION_NOT_FOUND"


class TestNotificationServiceMarkAllAsRead:
    """Test mark_all_as_read with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self):
        from app.modules.notifications.service import mark_all_as_read

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_db.execute.return_value = mock_result

        count = await mark_all_as_read(mock_db, uuid.uuid4())
        assert count == 5


class TestNotificationServicePreferences:
    """Test preference service functions with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_get_preferences_empty(self):
        from app.modules.notifications.service import get_preferences

        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        prefs = await get_preferences(mock_db, uuid.uuid4())
        assert prefs == []

    @pytest.mark.asyncio
    async def test_is_preference_enabled_default_true(self):
        from app.modules.notifications.service import is_preference_enabled

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        enabled = await is_preference_enabled(
            mock_db, uuid.uuid4(), NotificationChannel.EMAIL, "marketing"
        )
        assert enabled is True

    @pytest.mark.asyncio
    async def test_is_preference_enabled_explicit_false(self):
        from app.modules.notifications.service import is_preference_enabled

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = False
        mock_db.execute.return_value = mock_result

        enabled = await is_preference_enabled(
            mock_db, uuid.uuid4(), NotificationChannel.EMAIL, "marketing"
        )
        assert enabled is False


# ===================================================================
# Celery task unit tests
# ===================================================================


class TestCeleryTasks:
    """Test Celery task functions with mocks."""

    @patch("app.modules.notifications.email.send_transactional_email", return_value=True)
    def test_send_email_task_success(self, mock_send):
        from app.tasks.notifications import send_email_task

        # Access the unbound function to call with a mock self (bind=True task)
        raw_fn = send_email_task.__wrapped__.__func__
        mock_self = MagicMock()
        mock_self.request.retries = 0
        mock_self.max_retries = 3

        result = raw_fn(
            mock_self,
            to_email="test@example.com",
            template_name="welcome",
            context={"name": "Tester"},
        )
        assert result["status"] == "sent"
        mock_send.assert_called_once_with("test@example.com", "welcome", {"name": "Tester"})

    @patch("app.modules.notifications.email.send_transactional_email", return_value=False)
    def test_send_email_task_failure_retries(self, mock_send):
        from app.tasks.notifications import send_email_task

        raw_fn = send_email_task.__wrapped__.__func__
        mock_self = MagicMock()
        mock_self.request.retries = 0
        mock_self.max_retries = 3
        mock_self.retry = MagicMock(side_effect=Exception("retry"))

        with pytest.raises(Exception, match="retry"):
            raw_fn(
                mock_self,
                to_email="test@example.com",
                template_name="welcome",
                context={"name": "Tester"},
            )
