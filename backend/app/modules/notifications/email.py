"""SendGrid email integration for transactional emails."""

from __future__ import annotations

import logging
from typing import Any

from python_http_client.exceptions import (
    BadRequestsError,
    ForbiddenError,
    UnauthorizedError,
)
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, From, Mail, MimeType, Subject, To

from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

EMAIL_TEMPLATES: dict[str, dict[str, str]] = {
    "welcome": {
        "subject": "Welcome to SelfPublisherForge!",
        "html": (
            "<h1>Welcome, {name}!</h1>"
            "<p>Thanks for joining SelfPublisherForge. "
            "We're excited to help you on your publishing journey.</p>"
            "<p>Get started by exploring your dashboard.</p>"
        ),
    },
    "verification": {
        "subject": "Verify your email address",
        "html": (
            "<h1>Email Verification</h1>"
            "<p>Hi {name}, please verify your email by clicking the link below:</p>"
            '<p><a href="{verification_url}">Verify Email</a></p>'
            "<p>This link expires in 24 hours.</p>"
        ),
    },
    "password_reset": {
        "subject": "Reset your password",
        "html": (
            "<h1>Password Reset</h1>"
            "<p>Hi {name}, we received a request to reset your password.</p>"
            '<p><a href="{reset_url}">Reset Password</a></p>'
            "<p>If you did not request this, please ignore this email.</p>"
        ),
    },
    "team_invite": {
        "subject": "You've been invited to join {org_name}",
        "html": (
            "<h1>Team Invitation</h1>"
            "<p>Hi {name}, you have been invited to join <strong>{org_name}</strong> "
            "on SelfPublisherForge.</p>"
            '<p><a href="{invite_url}">Accept Invitation</a></p>'
        ),
    },
    "ai_task_complete": {
        "subject": "Your AI task is complete",
        "html": (
            "<h1>AI Task Complete</h1>"
            "<p>Hi {name}, your AI task <strong>{task_name}</strong> has finished.</p>"
            '<p><a href="{result_url}">View Results</a></p>'
        ),
    },
    "publishing_status": {
        "subject": "Publishing status update: {book_title}",
        "html": (
            "<h1>Publishing Update</h1>"
            "<p>Hi {name}, the status of <strong>{book_title}</strong> "
            "has changed to <strong>{status}</strong>.</p>"
            '<p><a href="{book_url}">View Details</a></p>'
        ),
    },
}


def _build_html(template_name: str, context: dict[str, Any]) -> tuple[str, str]:
    """Resolve a template name into (subject, html) with context interpolation.

    Returns:
        Tuple of (subject, html_body).

    Raises:
        ValueError: If the template name is not recognised.
    """
    template = EMAIL_TEMPLATES.get(template_name)
    if template is None:
        raise ValueError(f"Unknown email template: {template_name}")

    subject = template["subject"].format_map(context)
    html_body = template["html"].format_map(context)
    return subject, html_body


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def send_transactional_email(
    to_email: str,
    template_name: str,
    context: dict[str, Any] | None = None,
    *,
    subject_override: str | None = None,
) -> bool:
    """Send a transactional email via SendGrid.

    Args:
        to_email: Recipient email address.
        template_name: One of the keys in ``EMAIL_TEMPLATES``.
        context: Dict of values to interpolate into the template.
        subject_override: If supplied, overrides the template subject.

    Returns:
        ``True`` if the email was accepted by SendGrid, ``False`` otherwise.
    """
    settings = get_settings()
    ctx: dict[str, Any] = context or {}

    subject_text, html_body = _build_html(template_name, ctx)
    if subject_override:
        subject_text = subject_override

    message = Mail(
        from_email=From(settings.FROM_EMAIL, "SelfPublisherForge"),
        to_emails=To(to_email),
        subject=Subject(subject_text),
        html_content=Content(MimeType.html, html_body),
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(
            "Email sent to %s (template=%s) status=%s",
            to_email,
            template_name,
            response.status_code,
        )
        return 200 <= response.status_code < 300
    except UnauthorizedError:
        logger.error(
            "SendGrid authentication failed sending to %s (template=%s). Check SENDGRID_API_KEY.",
            to_email,
            template_name,
        )
        return False
    except (ForbiddenError, BadRequestsError) as exc:
        logger.error(
            "SendGrid rejected request for %s (template=%s): %s",
            to_email,
            template_name,
            exc,
        )
        return False
    except OSError as exc:
        logger.error(
            "Network error sending email to %s (template=%s): %s",
            to_email,
            template_name,
            exc,
        )
        return False
