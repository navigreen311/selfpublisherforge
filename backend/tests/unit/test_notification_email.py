"""Unit tests for the SMTP email channel (email_channel.py).

Tests cover:
- send_email when SMTP is not configured (returns False)
- send_email success via mocked SMTP
- send_email handling SMTP errors gracefully
- Template structure validation
- send_template_email end-to-end dispatch (with _build_email mocked)
- Subject override in send_template_email

Note: The HTML templates embed CSS that contains literal curly braces (e.g.
``body { font-family: ... }``).  Python's ``str.format_map`` interprets
those as replacement fields, so calling ``_build_email`` without escaping
raises ``KeyError``.  Tests that need rendered output therefore mock
``_build_email`` at the call-site where it is consumed (``send_template_email``).
"""

from __future__ import annotations

import smtplib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.notifications.email_channel import (
    _DEFAULT_CONTEXT,
    EMAIL_TEMPLATES,
    _wrap_template,
    send_email,
    send_template_email,
)

# ===========================================================================
# Template structure tests
# ===========================================================================


class TestEmailTemplates:
    """Tests for the email template registry and structure."""

    def test_all_expected_templates_exist(self):
        """Verify all expected template keys are registered."""
        expected = {"welcome", "password_reset", "invitation", "report_ready"}
        assert set(EMAIL_TEMPLATES.keys()) == expected

    def test_all_templates_have_subject_and_html(self):
        """Every template must have at least 'subject' and 'html' keys."""
        for name, template in EMAIL_TEMPLATES.items():
            assert "subject" in template, f"Template '{name}' missing 'subject'"
            assert "html" in template, f"Template '{name}' missing 'html'"

    def test_all_templates_have_text_fallback(self):
        """Every template should have a plaintext fallback."""
        for name, template in EMAIL_TEMPLATES.items():
            assert "text" in template, f"Template '{name}' missing 'text'"

    def test_welcome_subject_contains_welcome(self):
        """Welcome template subject should include the word Welcome."""
        subject_template = EMAIL_TEMPLATES["welcome"]["subject"]
        assert "Welcome" in subject_template

    def test_password_reset_subject_contains_reset(self):
        """Password reset template subject should reference reset."""
        subject_template = EMAIL_TEMPLATES["password_reset"]["subject"]
        assert "Reset" in subject_template or "reset" in subject_template

    def test_invitation_subject_references_org(self):
        """Invitation template subject should contain the org_name placeholder."""
        subject_template = EMAIL_TEMPLATES["invitation"]["subject"]
        assert "{org_name}" in subject_template

    def test_report_ready_subject_mentions_report(self):
        """Report ready subject should mention report."""
        subject_template = EMAIL_TEMPLATES["report_ready"]["subject"]
        assert "report" in subject_template.lower()

    def test_welcome_text_interpolation(self):
        """The welcome plaintext template should interpolate name correctly."""
        text_template = EMAIL_TEMPLATES["welcome"]["text"]
        rendered = text_template.format_map({**_DEFAULT_CONTEXT, "name": "Alice"})
        assert "Alice" in rendered

    def test_password_reset_text_interpolation(self):
        """The password reset plaintext template should interpolate name and reset_url."""
        text_template = EMAIL_TEMPLATES["password_reset"]["text"]
        ctx = {**_DEFAULT_CONTEXT, "name": "Bob", "reset_url": "https://example.com/reset/abc"}
        rendered = text_template.format_map(ctx)
        assert "Bob" in rendered
        assert "https://example.com/reset/abc" in rendered

    def test_invitation_text_interpolation(self):
        """The invitation plaintext template should interpolate org_name and role."""
        text_template = EMAIL_TEMPLATES["invitation"]["text"]
        ctx = {
            **_DEFAULT_CONTEXT,
            "name": "Carol",
            "org_name": "Acme Publishing",
            "role": "editor",
            "invite_url": "https://example.com/invite/xyz",
        }
        rendered = text_template.format_map(ctx)
        assert "Acme Publishing" in rendered
        assert "editor" in rendered or "Carol" in rendered

    def test_report_ready_text_interpolation(self):
        """The report ready plaintext template should interpolate report_name."""
        text_template = EMAIL_TEMPLATES["report_ready"]["text"]
        ctx = {
            **_DEFAULT_CONTEXT,
            "name": "Dave",
            "report_name": "Sales Q4",
            "download_url": "https://example.com/dl/report",
        }
        rendered = text_template.format_map(ctx)
        assert "Sales Q4" in rendered
        assert "https://example.com/dl/report" in rendered

    def test_default_context_has_all_common_keys(self):
        """_DEFAULT_CONTEXT should provide fallback values for common placeholders."""
        required_keys = {"name", "dashboard_url", "reset_url", "invite_url",
                         "download_url", "preferences_url", "org_name", "role",
                         "report_name", "expiry_hours", "expiry_days", "year"}
        assert required_keys.issubset(set(_DEFAULT_CONTEXT.keys()))

    def test_wrap_template_returns_html_string(self):
        """_wrap_template should produce an HTML document skeleton."""
        result = _wrap_template("<p>Hello</p>")
        assert result.startswith("<!DOCTYPE html>")
        assert "SelfPublisherForge" in result
        assert "<p>Hello</p>" in result


# ===========================================================================
# send_email tests (SMTP transport)
# ===========================================================================


class TestSendEmail:
    """Tests for the low-level send_email function."""

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_send_email_returns_false_when_not_configured(self, mock_settings):
        """If SMTP_HOST is None, send_email should log a warning and return False."""
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
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_send_email_returns_false_when_host_empty(self, mock_settings):
        """If SMTP_HOST is empty string, send_email should return False."""
        settings = MagicMock()
        settings.SMTP_HOST = ""
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
    async def test_send_email_success(self, mock_settings, mock_smtp_cls):
        """With valid SMTP config, send_email should send and return True."""
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
        mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.smtplib.SMTP")
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_send_email_success_without_credentials(self, mock_settings, mock_smtp_cls):
        """When SMTP_USER is None, login should be skipped."""
        settings = MagicMock()
        settings.SMTP_HOST = "smtp.example.com"
        settings.SMTP_PORT = 587
        settings.SMTP_FROM = "noreply@example.com"
        settings.SMTP_USER = None
        settings.SMTP_PASS = None
        mock_settings.return_value = settings

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = await send_email(
            to="recipient@example.com",
            subject="Hello",
            body_html="<p>World</p>",
        )

        assert result is True
        mock_server.login.assert_not_called()
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.smtplib.SMTP")
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_send_email_handles_smtp_error(self, mock_settings, mock_smtp_cls):
        """SMTP errors should be caught and return False."""
        settings = MagicMock()
        settings.SMTP_HOST = "smtp.example.com"
        settings.SMTP_PORT = 587
        settings.SMTP_FROM = "noreply@example.com"
        settings.SMTP_USER = "user"
        settings.SMTP_PASS = "pass"
        mock_settings.return_value = settings

        mock_smtp_cls.side_effect = smtplib.SMTPException("Connection refused")

        result = await send_email(
            to="recipient@example.com",
            subject="Hello",
            body_html="<p>World</p>",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.smtplib.SMTP")
    @patch("app.modules.notifications.email_channel.get_settings")
    async def test_send_email_html_only(self, mock_settings, mock_smtp_cls):
        """send_email with only HTML body (no text) should still succeed."""
        settings = MagicMock()
        settings.SMTP_HOST = "smtp.example.com"
        settings.SMTP_PORT = 587
        settings.SMTP_FROM = "noreply@example.com"
        settings.SMTP_USER = None
        settings.SMTP_PASS = None
        mock_settings.return_value = settings

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = await send_email(
            to="recipient@example.com",
            subject="HTML only",
            body_html="<p>HTML content only</p>",
            body_text=None,
        )

        assert result is True
        mock_server.send_message.assert_called_once()


# ===========================================================================
# send_template_email tests
# ===========================================================================


class TestSendTemplateEmail:
    """Tests for the high-level send_template_email function."""

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.send_email", new_callable=AsyncMock)
    @patch("app.modules.notifications.email_channel._build_email")
    async def test_send_template_email_dispatches(self, mock_build, mock_send_email):
        """send_template_email should resolve the template and call send_email."""
        mock_build.return_value = (
            "Welcome to SelfPublisherForge!",
            "<h2>Welcome, Tester!</h2>",
            "Welcome, Tester!",
        )
        mock_send_email.return_value = True

        result = await send_template_email(
            to="user@example.com",
            template_name="welcome",
            context={"name": "Tester", "dashboard_url": "https://app.example.com"},
        )

        assert result is True
        mock_build.assert_called_once_with("welcome", {"name": "Tester", "dashboard_url": "https://app.example.com"})
        mock_send_email.assert_awaited_once_with(
            "user@example.com",
            "Welcome to SelfPublisherForge!",
            "<h2>Welcome, Tester!</h2>",
            "Welcome, Tester!",
        )

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.send_email", new_callable=AsyncMock)
    @patch("app.modules.notifications.email_channel._build_email")
    async def test_send_template_email_subject_override(self, mock_build, mock_send_email):
        """subject_override should replace the template's default subject."""
        mock_build.return_value = (
            "Welcome to SelfPublisherForge!",
            "<h2>Welcome</h2>",
            "Welcome",
        )
        mock_send_email.return_value = True

        result = await send_template_email(
            to="user@example.com",
            template_name="welcome",
            context={"name": "Tester"},
            subject_override="Custom Subject Line",
        )

        assert result is True
        # send_email should have been called with the overridden subject
        call_args = mock_send_email.call_args
        assert call_args[0][1] == "Custom Subject Line"

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel._build_email")
    async def test_send_template_email_unknown_template_raises(self, mock_build):
        """send_template_email with an unknown template should raise ValueError."""
        mock_build.side_effect = ValueError("Unknown email template: does_not_exist")

        with pytest.raises(ValueError, match="Unknown email template"):
            await send_template_email(
                to="user@example.com",
                template_name="does_not_exist",
            )

    @pytest.mark.asyncio
    @patch("app.modules.notifications.email_channel.send_email", new_callable=AsyncMock)
    @patch("app.modules.notifications.email_channel._build_email")
    async def test_send_template_email_returns_false_on_failure(self, mock_build, mock_send_email):
        """send_template_email should propagate False from send_email."""
        mock_build.return_value = (
            "Welcome to SelfPublisherForge!",
            "<h2>Welcome</h2>",
            "Welcome",
        )
        mock_send_email.return_value = False

        result = await send_template_email(
            to="user@example.com",
            template_name="welcome",
            context={"name": "User"},
        )

        assert result is False
        mock_send_email.assert_awaited_once()
