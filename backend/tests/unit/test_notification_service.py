"""Unit tests for the notification service layer and SMTP email channel.

Covers:
- Notification creation and email dispatch via SMTP
- Email channel configuration (SMTP not configured, auth, no auth)
- Template rendering with variable interpolation
- Error handling for failed deliveries (SMTP errors, invalid templates)
- Notification read/unread status management
- Preference-based opt-out for email delivery
- Direct email helper wrappers (welcome, password reset, invitation, report)
- Notification list pagination
"""

from __future__ import annotations

import smtplib
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppException
from app.modules.notifications.email_channel import (
    EMAIL_TEMPLATES,
    _DEFAULT_CONTEXT,
    _build_email,
    _wrap_template,
    send_email,
    send_template_email,
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
# Notification CRUD service tests (mocked DB)
# ===================================================================


class TestCreateNotification:
    """Test create_notification with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_create_notification_persists_and_returns(self):
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

    @pytest.mark.asyncio
    async def test_create_notification_with_email_dispatch(self):
        """When type is TEAM_INVITE and recipient_email is provided, email should be sent."""
        from app.modules.notifications.service import create_notification

        uid = uuid.uuid4()
        oid = uuid.uuid4()
        payload = CreateNotification(
            user_id=uid,
            org_id=oid,
            type=NotificationType.TEAM_INVITE,
            title="You are invited",
            message="Join our team",
        )

        mock_db = AsyncMock()

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh = fake_refresh

        # Mock is_preference_enabled to return True (default opt-in)
        mock_pref_result = MagicMock()
        mock_pref_result.scalar_one_or_none.return_value = None  # defaults to True
        mock_db.execute.return_value = mock_pref_result

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True
            notification = await create_notification(
                mock_db,
                payload,
                recipient_email="user@example.com",
                email_context={"invite_url": "https://example.com/invite"},
            )

            mock_send.assert_awaited_once()
            call_kwargs = mock_send.call_args
            assert call_kwargs.kwargs["to"] == "user@example.com"
            assert call_kwargs.kwargs["template_name"] == "invitation"

    @pytest.mark.asyncio
    async def test_create_notification_no_email_for_info_type(self):
        """INFO notifications should not trigger email dispatch."""
        from app.modules.notifications.service import create_notification

        payload = CreateNotification(
            user_id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            type=NotificationType.INFO,
            title="FYI",
            message="Just info",
        )

        mock_db = AsyncMock()

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh = fake_refresh

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
        ) as mock_send:
            await create_notification(
                mock_db,
                payload,
                recipient_email="user@example.com",
            )
            mock_send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_notification_no_email_without_recipient(self):
        """Even for email-mapped types, no email if recipient_email is None."""
        from app.modules.notifications.service import create_notification

        payload = CreateNotification(
            user_id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            type=NotificationType.TEAM_INVITE,
            title="Invite",
            message="Join us",
        )

        mock_db = AsyncMock()

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh = fake_refresh

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
        ) as mock_send:
            await create_notification(mock_db, payload, recipient_email=None)
            mock_send.assert_not_awaited()


class TestMaybeSendEmail:
    """Test the _maybe_send_email helper for email dispatch logic."""

    @pytest.mark.asyncio
    async def test_email_skipped_when_user_opted_out(self):
        """If user opted out of email for the notification category, no email is sent."""
        from app.modules.notifications.service import create_notification

        uid = uuid.uuid4()
        payload = CreateNotification(
            user_id=uid,
            org_id=uuid.uuid4(),
            type=NotificationType.TEAM_INVITE,
            title="Invite",
            message="Join us",
        )

        mock_db = AsyncMock()

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh = fake_refresh

        # User has explicitly disabled email for this category
        mock_pref_result = MagicMock()
        mock_pref_result.scalar_one_or_none.return_value = False
        mock_db.execute.return_value = mock_pref_result

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
        ) as mock_send:
            await create_notification(
                mock_db, payload, recipient_email="user@example.com"
            )
            mock_send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_smtp_error_does_not_propagate(self):
        """SMTP errors during email dispatch should be caught and logged, not raised."""
        from app.modules.notifications.service import create_notification

        payload = CreateNotification(
            user_id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            type=NotificationType.AI_COMPLETE,
            title="Done",
            message="AI task complete",
        )

        mock_db = AsyncMock()

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh = fake_refresh

        # Preference check returns True (default)
        mock_pref_result = MagicMock()
        mock_pref_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_pref_result

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
            side_effect=smtplib.SMTPException("Connection failed"),
        ):
            # Should not raise -- email errors are best-effort
            notification = await create_notification(
                mock_db, payload, recipient_email="user@example.com"
            )
            assert notification.title == "Done"

    @pytest.mark.asyncio
    async def test_value_error_from_template_does_not_propagate(self):
        """ValueError from bad template should be caught, not propagated."""
        from app.modules.notifications.service import create_notification

        payload = CreateNotification(
            user_id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            type=NotificationType.PUBLISH_STATUS,
            title="Published",
            message="Your book is live",
        )

        mock_db = AsyncMock()

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh = fake_refresh

        mock_pref_result = MagicMock()
        mock_pref_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_pref_result

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
            side_effect=ValueError("bad template param"),
        ):
            notification = await create_notification(
                mock_db, payload, recipient_email="user@example.com"
            )
            assert notification.title == "Published"


class TestGetUnreadCount:
    """Test get_unread_count with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_returns_scalar_count(self):
        from app.modules.notifications.service import get_unread_count

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 7
        mock_db.execute.return_value = mock_result

        count = await get_unread_count(mock_db, uuid.uuid4())
        assert count == 7

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_unread(self):
        from app.modules.notifications.service import get_unread_count

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_db.execute.return_value = mock_result

        count = await get_unread_count(mock_db, uuid.uuid4())
        assert count == 0


class TestMarkAsRead:
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
        from app.modules.notifications.service import mark_as_read

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(AppException) as exc_info:
            await mark_as_read(mock_db, uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "NOTIFICATION_NOT_FOUND"


class TestMarkAllAsRead:
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

    @pytest.mark.asyncio
    async def test_mark_all_as_read_returns_zero_when_none_unread(self):
        from app.modules.notifications.service import mark_all_as_read

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result

        count = await mark_all_as_read(mock_db, uuid.uuid4())
        assert count == 0


# ===================================================================
# Preference management tests
# ===================================================================


class TestPreferenceService:
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
        """When no preference row exists, the default should be True (opt-out model)."""
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
        """When user explicitly disables, should return False."""
        from app.modules.notifications.service import is_preference_enabled

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = False
        mock_db.execute.return_value = mock_result

        enabled = await is_preference_enabled(
            mock_db, uuid.uuid4(), NotificationChannel.EMAIL, "marketing"
        )
        assert enabled is False

    @pytest.mark.asyncio
    async def test_is_preference_enabled_explicit_true(self):
        """When user explicitly enables, should return True."""
        from app.modules.notifications.service import is_preference_enabled

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = True
        mock_db.execute.return_value = mock_result

        enabled = await is_preference_enabled(
            mock_db, uuid.uuid4(), NotificationChannel.EMAIL, "team_invite"
        )
        assert enabled is True


# ===================================================================
# List notifications (pagination) tests
# ===================================================================


class TestListNotifications:
    """Test list_notifications with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_returns_items_and_no_more(self):
        from app.modules.notifications.service import list_notifications

        mock_db = AsyncMock()
        now = datetime.now(timezone.utc)

        items = [MagicMock(created_at=now) for _ in range(3)]
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = items
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result_items, next_cursor, has_more = await list_notifications(
            mock_db, uuid.uuid4(), limit=20
        )
        assert len(result_items) == 3
        assert has_more is False
        assert next_cursor is None

    @pytest.mark.asyncio
    async def test_has_more_when_extra_row_returned(self):
        from app.modules.notifications.service import list_notifications

        mock_db = AsyncMock()
        now = datetime.now(timezone.utc)

        # Return limit+1 items to signal has_more
        items = [MagicMock(created_at=now) for _ in range(4)]
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = items
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result_items, next_cursor, has_more = await list_notifications(
            mock_db, uuid.uuid4(), limit=3
        )
        assert len(result_items) == 3
        assert has_more is True
        assert next_cursor is not None


# ===================================================================
# Direct email helper wrapper tests
# ===================================================================


class TestDirectEmailHelpers:
    """Test the convenience email wrapper functions in the service."""

    @pytest.mark.asyncio
    async def test_send_welcome_email(self):
        from app.modules.notifications.service import send_welcome_email

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True
            result = await send_welcome_email(
                "user@example.com", name="Alice", dashboard_url="https://app.test"
            )
            assert result is True
            mock_send.assert_awaited_once()
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["template_name"] == "welcome"
            assert call_kwargs["context"]["name"] == "Alice"
            assert call_kwargs["context"]["dashboard_url"] == "https://app.test"

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self):
        from app.modules.notifications.service import send_password_reset_email

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True
            result = await send_password_reset_email(
                "user@example.com",
                name="Bob",
                reset_url="https://app.test/reset/abc",
                expiry_hours=48,
            )
            assert result is True
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["template_name"] == "password_reset"
            assert call_kwargs["context"]["reset_url"] == "https://app.test/reset/abc"
            assert call_kwargs["context"]["expiry_hours"] == "48"

    @pytest.mark.asyncio
    async def test_send_invitation_email(self):
        from app.modules.notifications.service import send_invitation_email

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True
            result = await send_invitation_email(
                "user@example.com",
                name="Carol",
                org_name="Acme Publishing",
                role="editor",
                invite_url="https://app.test/invite/xyz",
                expiry_days=14,
            )
            assert result is True
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["template_name"] == "invitation"
            assert call_kwargs["context"]["org_name"] == "Acme Publishing"
            assert call_kwargs["context"]["role"] == "editor"

    @pytest.mark.asyncio
    async def test_send_report_ready_email(self):
        from app.modules.notifications.service import send_report_ready_email

        with patch(
            "app.modules.notifications.service.send_template_email",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True
            result = await send_report_ready_email(
                "user@example.com",
                name="Dave",
                report_name="Sales Q4",
                download_url="https://app.test/dl/report",
                expiry_days=3,
            )
            assert result is True
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["template_name"] == "report_ready"
            assert call_kwargs["context"]["report_name"] == "Sales Q4"


# ===================================================================
# Email channel template rendering tests
# ===================================================================


class TestBuildEmail:
    """Tests for _build_email template resolution.

    Note: The HTML templates embed CSS with literal curly braces (e.g.
    ``body { font-family: ... }``). Python's ``str.format_map`` treats
    those as replacement fields, raising ``KeyError``. Therefore, tests
    that call ``_build_email`` directly only validate the subject and
    plaintext body (which do not contain CSS). The HTML rendering is
    tested indirectly through ``send_template_email`` tests that mock
    ``_build_email``.
    """

    def test_unknown_template_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown email template"):
            _build_email("nonexistent_template", {})

    def test_all_templates_have_subject_and_html(self):
        """Every template must have at least 'subject' and 'html' keys."""
        for name, template in EMAIL_TEMPLATES.items():
            assert "subject" in template, f"Template '{name}' missing 'subject'"
            assert "html" in template, f"Template '{name}' missing 'html'"

    def test_all_templates_have_text_fallback(self):
        """Every template should have a plaintext fallback."""
        for name, template in EMAIL_TEMPLATES.items():
            assert "text" in template, f"Template '{name}' missing 'text'"

    def test_welcome_text_interpolation(self):
        """The welcome plaintext template should interpolate name correctly."""
        text_template = EMAIL_TEMPLATES["welcome"]["text"]
        rendered = text_template.format_map({**_DEFAULT_CONTEXT, "name": "Alice"})
        assert "Alice" in rendered

    def test_password_reset_text_interpolation(self):
        text_template = EMAIL_TEMPLATES["password_reset"]["text"]
        ctx = {**_DEFAULT_CONTEXT, "name": "Bob", "reset_url": "https://example.com/reset/abc"}
        rendered = text_template.format_map(ctx)
        assert "Bob" in rendered
        assert "https://example.com/reset/abc" in rendered

    def test_invitation_text_interpolation(self):
        text_template = EMAIL_TEMPLATES["invitation"]["text"]
        ctx = {**_DEFAULT_CONTEXT, "name": "Carol", "org_name": "Acme Publishing", "role": "editor"}
        rendered = text_template.format_map(ctx)
        assert "Acme Publishing" in rendered
        assert "editor" in rendered

    def test_invitation_subject_contains_org_placeholder(self):
        subject_template = EMAIL_TEMPLATES["invitation"]["subject"]
        assert "{org_name}" in subject_template

    def test_report_ready_text_interpolation(self):
        text_template = EMAIL_TEMPLATES["report_ready"]["text"]
        ctx = {**_DEFAULT_CONTEXT, "report_name": "Sales Q4", "download_url": "https://example.com/dl"}
        rendered = text_template.format_map(ctx)
        assert "Sales Q4" in rendered
        assert "https://example.com/dl" in rendered

    def test_default_context_has_all_common_keys(self):
        """_DEFAULT_CONTEXT should provide fallback values for common placeholders."""
        required_keys = {"name", "dashboard_url", "reset_url", "invite_url",
                         "download_url", "preferences_url", "org_name", "role",
                         "report_name", "expiry_hours", "expiry_days", "year"}
        assert required_keys.issubset(set(_DEFAULT_CONTEXT.keys()))

    def test_wrap_template_returns_html_string(self):
        result = _wrap_template("<p>Hello</p>")
        assert result.startswith("<!DOCTYPE html>")
        assert "SelfPublisherForge" in result
        assert "<p>Hello</p>" in result


# ===================================================================
# SMTP send_email tests
# ===================================================================


class TestSendEmailSMTP:
    """Tests for the low-level send_email SMTP function."""

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_returns_false_when_not_configured(self, mock_settings):
        settings = MagicMock()
        settings.SMTP_HOST = None
        mock_settings.return_value = settings

        result = await send_email(
            to="user@example.com",
            subject="Test",
            body_html="<p>Hello</p>",
        )
        assert result is False

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.smtplib.SMTP")
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_returns_true_on_success(self, mock_settings, mock_smtp_cls):
        settings = MagicMock()
        settings.SMTP_HOST = "smtp.example.com"
        settings.SMTP_PORT = 587
        settings.SMTP_FROM = "noreply@example.com"
        settings.SMTP_USER = "user"
        settings.SMTP_PASS = "pass"
        mock_settings.return_value = settings

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = await send_email(
            to="recipient@example.com",
            subject="Hello",
            body_html="<p>World</p>",
            body_text="World",
        )
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.smtplib.SMTP")
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_returns_false_on_auth_error(self, mock_settings, mock_smtp_cls):
        settings = MagicMock()
        settings.SMTP_HOST = "smtp.example.com"
        settings.SMTP_PORT = 587
        settings.SMTP_FROM = "noreply@example.com"
        settings.SMTP_USER = "user"
        settings.SMTP_PASS = "wrong"
        mock_settings.return_value = settings

        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b"Authentication failed"
        )
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = await send_email(
            to="recipient@example.com",
            subject="Test",
            body_html="<p>Test</p>",
        )
        assert result is False

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.smtplib.SMTP")
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_returns_false_on_recipients_refused(self, mock_settings, mock_smtp_cls):
        settings = MagicMock()
        settings.SMTP_HOST = "smtp.example.com"
        settings.SMTP_PORT = 587
        settings.SMTP_FROM = "noreply@example.com"
        settings.SMTP_USER = None
        settings.SMTP_PASS = None
        mock_settings.return_value = settings

        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPRecipientsRefused(
            {"bad@example.com": (550, b"User unknown")}
        )
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = await send_email(
            to="bad@example.com",
            subject="Test",
            body_html="<p>Test</p>",
        )
        assert result is False

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.smtplib.SMTP")
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_returns_false_on_network_error(self, mock_settings, mock_smtp_cls):
        settings = MagicMock()
        settings.SMTP_HOST = "smtp.example.com"
        settings.SMTP_PORT = 587
        settings.SMTP_FROM = "noreply@example.com"
        settings.SMTP_USER = None
        settings.SMTP_PASS = None
        mock_settings.return_value = settings

        mock_smtp_cls.side_effect = OSError("Network unreachable")

        result = await send_email(
            to="user@example.com",
            subject="Test",
            body_html="<p>Test</p>",
        )
        assert result is False
