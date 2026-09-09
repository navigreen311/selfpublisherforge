"""SMTP-based email channel for notification dispatch.

This module provides a lightweight SMTP transport that can be used as an
alternative (or fallback) to the SendGrid integration in ``email.py``.

When ``SMTP_HOST`` is not configured the functions degrade gracefully by
logging a warning and returning ``False``.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HTML email templates
# ---------------------------------------------------------------------------

_BASE_STYLE = """
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f7; }
  .email-wrapper { width: 100%; background-color: #f4f4f7; padding: 40px 0; }
  .email-container { max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  .email-header { background-color: #1a1a2e; padding: 24px 32px; text-align: center; }
  .email-header h1 { color: #ffffff; margin: 0; font-size: 22px; font-weight: 600; }
  .email-body { padding: 32px; color: #333333; line-height: 1.6; font-size: 15px; }
  .email-body h2 { color: #1a1a2e; margin-top: 0; font-size: 20px; }
  .email-body p { margin: 0 0 16px; }
  .btn { display: inline-block; padding: 12px 28px; background-color: #4f46e5; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; }
  .btn:hover { background-color: #4338ca; }
  .email-footer { padding: 24px 32px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; }
  .email-footer a { color: #6b7280; text-decoration: underline; }
</style>
"""


def _wrap_template(inner_html: str) -> str:
    """Wrap inner content in the shared base email layout."""
    return (
        "<!DOCTYPE html>"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        f"{_BASE_STYLE}</head><body>"
        '<div class="email-wrapper"><div class="email-container">'
        '<div class="email-header"><h1>SelfPublisherForge</h1></div>'
        f'<div class="email-body">{inner_html}</div>'
        '<div class="email-footer">'
        "<p>&copy; {year} SelfPublisherForge. All rights reserved.</p>"
        "<p>You received this email because you have an account with us. "
        '<a href="{preferences_url}">Manage email preferences</a></p>'
        "</div></div></div></body></html>"
    )


EMAIL_TEMPLATES: dict[str, dict[str, str]] = {
    "welcome": {
        "subject": "Welcome to SelfPublisherForge!",
        "html": _wrap_template(
            "<h2>Welcome, {name}!</h2>"
            "<p>Thank you for joining <strong>SelfPublisherForge</strong>. "
            "We are excited to help you on your self-publishing journey.</p>"
            "<p>Your account is ready. Head over to your dashboard to start "
            "creating, managing, and publishing your books with ease.</p>"
            '<p><a class="btn" href="{dashboard_url}">Go to Dashboard</a></p>'
            "<p>If you have any questions, feel free to reach out to our support team.</p>"
        ),
        "text": (
            "Welcome, {name}!\n\n"
            "Thank you for joining SelfPublisherForge. We are excited to help "
            "you on your self-publishing journey.\n\n"
            "Your account is ready. Head over to your dashboard to get started:\n"
            "{dashboard_url}\n\n"
            "If you have any questions, feel free to reach out to our support team.\n"
        ),
    },
    "password_reset": {
        "subject": "Reset your password",
        "html": _wrap_template(
            "<h2>Password Reset Request</h2>"
            "<p>Hi {name},</p>"
            "<p>We received a request to reset the password for your "
            "SelfPublisherForge account. Click the button below to choose "
            "a new password:</p>"
            '<p><a class="btn" href="{reset_url}">Reset Password</a></p>'
            "<p>This link will expire in <strong>{expiry_hours} hours</strong>.</p>"
            "<p>If you did not request a password reset, you can safely ignore "
            "this email. Your password will remain unchanged.</p>"
        ),
        "text": (
            "Hi {name},\n\n"
            "We received a request to reset the password for your "
            "SelfPublisherForge account.\n\n"
            "Reset your password by visiting the link below:\n"
            "{reset_url}\n\n"
            "This link will expire in {expiry_hours} hours.\n\n"
            "If you did not request a password reset, you can safely ignore "
            "this email. Your password will remain unchanged.\n"
        ),
    },
    "invitation": {
        "subject": "You've been invited to join {org_name} on SelfPublisherForge",
        "html": _wrap_template(
            "<h2>Team Invitation</h2>"
            "<p>Hi {name},</p>"
            "<p>You have been invited to join <strong>{org_name}</strong> on "
            "SelfPublisherForge as a <strong>{role}</strong>.</p>"
            "<p>Click the button below to accept the invitation and get started "
            "collaborating with your team:</p>"
            '<p><a class="btn" href="{invite_url}">Accept Invitation</a></p>'
            "<p>This invitation will expire in <strong>{expiry_days} days</strong>.</p>"
            "<p>If you were not expecting this invitation, you can safely ignore "
            "this email.</p>"
        ),
        "text": (
            "Hi {name},\n\n"
            "You have been invited to join {org_name} on SelfPublisherForge "
            "as a {role}.\n\n"
            "Accept the invitation by visiting:\n"
            "{invite_url}\n\n"
            "This invitation will expire in {expiry_days} days.\n\n"
            "If you were not expecting this invitation, you can safely ignore "
            "this email.\n"
        ),
    },
    "report_ready": {
        "subject": "Your report is ready for download",
        "html": _wrap_template(
            "<h2>Report Ready</h2>"
            "<p>Hi {name},</p>"
            "<p>Great news! Your report <strong>{report_name}</strong> has "
            "finished processing and is ready for download.</p>"
            '<p><a class="btn" href="{download_url}">Download Report</a></p>'
            "<p>This download link will remain available for "
            "<strong>{expiry_days} days</strong>.</p>"
            "<p>You can also find this report in your dashboard under "
            "<em>Reports</em>.</p>"
        ),
        "text": (
            "Hi {name},\n\n"
            'Great news! Your report "{report_name}" has finished processing '
            "and is ready for download.\n\n"
            "Download it here:\n"
            "{download_url}\n\n"
            "This download link will remain available for {expiry_days} days.\n\n"
            "You can also find this report in your dashboard under Reports.\n"
        ),
    },
}

# Default context values so templates never fail on missing keys
_DEFAULT_CONTEXT: dict[str, str] = {
    "name": "there",
    "dashboard_url": "#",
    "reset_url": "#",
    "invite_url": "#",
    "download_url": "#",
    "preferences_url": "#",
    "org_name": "an organization",
    "role": "member",
    "report_name": "Untitled Report",
    "task_name": "Untitled Task",
    "book_title": "Untitled Book",
    "status": "updated",
    "expiry_hours": "24",
    "expiry_days": "7",
    "year": "2026",
}


def _build_email(
    template_name: str,
    context: dict[str, Any] | None = None,
) -> tuple[str, str, str | None]:
    """Resolve a template into (subject, html_body, text_body).

    Raises:
        ValueError: If *template_name* is not found in ``EMAIL_TEMPLATES``.
    """
    template = EMAIL_TEMPLATES.get(template_name)
    if template is None:
        raise ValueError(f"Unknown email template: {template_name}")

    merged: dict[str, Any] = {**_DEFAULT_CONTEXT, **(context or {})}

    subject = template["subject"].format_map(merged)
    html_body = template["html"].format_map(merged)
    text_body: str | None = None
    if "text" in template:
        text_body = template["text"].format_map(merged)

    return subject, html_body, text_body


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def send_email(
    to: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> bool:
    """Send an email via SMTP.

    Uses the ``SMTP_*`` settings from the application configuration.  In
    production you would typically point these at AWS SES, Mailgun, or a
    similar relay.  If ``SMTP_HOST`` is not configured the call degrades
    gracefully (logs a warning, returns ``False``).

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body_html: HTML version of the email body.
        body_text: Optional plain-text version of the body.

    Returns:
        ``True`` if the message was accepted by the SMTP server.
    """
    settings = get_settings()
    smtp_host = settings.SMTP_HOST

    if not smtp_host:
        logger.warning(
            "SMTP not configured (SMTP_HOST is empty). " "Skipping email to %s: %s",
            to,
            subject,
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(smtp_host, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASS:
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.send_message(msg)

        logger.info("Email sent via SMTP to %s: %s", to, subject)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed when sending to %s: %s", to, subject)
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.error("SMTP recipients refused for %s: %s", to, subject)
        return False
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending email to %s: %s — %s", to, subject, exc)
        return False
    except OSError as exc:
        logger.error("Network error connecting to SMTP server for %s: %s — %s", to, subject, exc)
        return False


async def send_template_email(
    to: str,
    template_name: str,
    context: dict[str, Any] | None = None,
    *,
    subject_override: str | None = None,
) -> bool:
    """Send an email using one of the predefined templates.

    This is the high-level helper that other modules should use.  It
    resolves the template, interpolates context variables, and delegates
    to :func:`send_email`.

    Args:
        to: Recipient email address.
        template_name: A key from ``EMAIL_TEMPLATES``.
        context: Values to interpolate into the template placeholders.
        subject_override: If given, replaces the template's default subject.

    Returns:
        ``True`` if the email was sent successfully.
    """
    subject, html_body, text_body = _build_email(template_name, context)
    if subject_override:
        subject = subject_override
    return await send_email(to, subject, html_body, text_body)
