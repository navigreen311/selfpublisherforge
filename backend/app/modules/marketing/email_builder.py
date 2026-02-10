"""Email sequence builder with templates, scheduling, and personalization.

Provides pre-built email templates for common book marketing scenarios
and utilities for building custom email sequences.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from app.models.marketing import EmailTemplateType
from app.modules.marketing.schemas import (
    EmailSequenceCreate,
    EmailTemplateCreate,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email Templates
# ---------------------------------------------------------------------------

WELCOME_TEMPLATE = {
    "subject": "Welcome! Your free preview of {book_title} is here",
    "body_html": """
<html>
<body>
<h1>Welcome, {reader_name}!</h1>
<p>Thank you for your interest in <strong>{book_title}</strong>.</p>
<p>As promised, here is your free preview chapter. I hope you enjoy it!</p>
<p><a href="{preview_link}">Download Your Preview</a></p>
<p>I am so excited to share this story with you. Stay tuned for the official
launch date announcement.</p>
<p>Happy reading,<br/>{author_name}</p>
</body>
</html>
""",
    "body_text": (
        "Welcome, {reader_name}!\n\n"
        "Thank you for your interest in {book_title}.\n\n"
        "As promised, here is your free preview chapter: {preview_link}\n\n"
        "I am so excited to share this story with you. Stay tuned for the official "
        "launch date announcement.\n\n"
        "Happy reading,\n{author_name}"
    ),
}

LAUNCH_ANNOUNCEMENT_TEMPLATE = {
    "subject": "It is HERE! {book_title} is now available!",
    "body_html": """
<html>
<body>
<h1>{book_title} is NOW LIVE!</h1>
<p>Dear {reader_name},</p>
<p>The day has finally arrived! <strong>{book_title}</strong> is now available for
purchase.</p>
<p><a href="{buy_link}" style="background-color:#4CAF50;color:white;padding:14px 25px;
text-decoration:none;display:inline-block;border-radius:5px;">Get Your Copy Now</a></p>
<p>{book_description}</p>
<p>Thank you for being part of this journey. Your support means the world to me.</p>
<p>Best,<br/>{author_name}</p>
</body>
</html>
""",
    "body_text": (
        "{book_title} is NOW LIVE!\n\n"
        "Dear {reader_name},\n\n"
        "The day has finally arrived! {book_title} is now available for purchase.\n\n"
        "Get your copy here: {buy_link}\n\n"
        "{book_description}\n\n"
        "Thank you for being part of this journey.\n\n"
        "Best,\n{author_name}"
    ),
}

FOLLOW_UP_TEMPLATE = {
    "subject": "How are you enjoying {book_title}?",
    "body_html": """
<html>
<body>
<p>Hi {reader_name},</p>
<p>I hope you are enjoying <strong>{book_title}</strong>!</p>
<p>I wanted to check in and share some bonus content with you:</p>
<ul>
<li>Behind-the-scenes look at my writing process</li>
<li>Character inspiration board</li>
<li>Deleted scenes</li>
</ul>
<p><a href="{bonus_link}">Access Your Bonus Content</a></p>
<p>If you have finished reading, I would love to hear your thoughts.
Feel free to reply to this email!</p>
<p>Warm regards,<br/>{author_name}</p>
</body>
</html>
""",
    "body_text": (
        "Hi {reader_name},\n\n"
        "I hope you are enjoying {book_title}!\n\n"
        "I wanted to check in and share some bonus content with you:\n"
        "- Behind-the-scenes look at my writing process\n"
        "- Character inspiration board\n"
        "- Deleted scenes\n\n"
        "Access your bonus content: {bonus_link}\n\n"
        "If you have finished reading, I would love to hear your thoughts.\n\n"
        "Warm regards,\n{author_name}"
    ),
}

REVIEW_REQUEST_TEMPLATE = {
    "subject": "Would you leave a quick review for {book_title}?",
    "body_html": """
<html>
<body>
<p>Hi {reader_name},</p>
<p>I hope you had a chance to finish <strong>{book_title}</strong>.</p>
<p>If you enjoyed it, would you consider leaving a quick review? Reviews make
an enormous difference for independent authors like me.</p>
<p><a href="{review_link}" style="background-color:#FF9800;color:white;padding:14px 25px;
text-decoration:none;display:inline-block;border-radius:5px;">Leave a Review</a></p>
<p>Even a few words help! Thank you so much for your support.</p>
<p>Gratefully,<br/>{author_name}</p>
</body>
</html>
""",
    "body_text": (
        "Hi {reader_name},\n\n"
        "I hope you had a chance to finish {book_title}.\n\n"
        "If you enjoyed it, would you consider leaving a quick review? Reviews make "
        "an enormous difference for independent authors like me.\n\n"
        "Leave a review here: {review_link}\n\n"
        "Even a few words help! Thank you so much for your support.\n\n"
        "Gratefully,\n{author_name}"
    ),
}

TEMPLATE_MAP: dict[EmailTemplateType, dict[str, str]] = {
    EmailTemplateType.WELCOME: WELCOME_TEMPLATE,
    EmailTemplateType.LAUNCH_ANNOUNCEMENT: LAUNCH_ANNOUNCEMENT_TEMPLATE,
    EmailTemplateType.FOLLOW_UP: FOLLOW_UP_TEMPLATE,
    EmailTemplateType.REVIEW_REQUEST: REVIEW_REQUEST_TEMPLATE,
}


def _extract_personalization_fields(template: dict[str, str]) -> list[str]:
    """Extract all {field_name} placeholders from a template."""
    fields = set()
    for key in ("subject", "body_html", "body_text"):
        text = template.get(key, "")
        matches = re.findall(r"\{(\w+)\}", text)
        fields.update(matches)
    return sorted(fields)


class EmailBuilder:
    """Builds email sequences from templates with scheduling and personalization."""

    def build_launch_sequence(
        self,
        sequence_name: str,
        book_title: str,
        author_name: str,
        launch_date: datetime,
        buy_link: str = "",
        preview_link: str = "",
        review_link: str = "",
        description: str | None = None,
    ) -> EmailSequenceCreate:
        """Build a complete launch email sequence with all four standard templates.

        Schedule:
        - Welcome: 7 days before launch
        - Launch Announcement: on launch day
        - Follow-Up: 5 days after launch
        - Review Request: 14 days after launch
        """
        default_personalization = {
            "book_title": book_title,
            "author_name": author_name,
            "buy_link": buy_link,
            "preview_link": preview_link,
            "review_link": review_link,
        }

        emails = [
            self._build_template_email(
                template_type=EmailTemplateType.WELCOME,
                order_index=0,
                delay_days=0,
                delay_hours=0,
            ),
            self._build_template_email(
                template_type=EmailTemplateType.LAUNCH_ANNOUNCEMENT,
                order_index=1,
                delay_days=7,
                delay_hours=0,
            ),
            self._build_template_email(
                template_type=EmailTemplateType.FOLLOW_UP,
                order_index=2,
                delay_days=12,
                delay_hours=0,
            ),
            self._build_template_email(
                template_type=EmailTemplateType.REVIEW_REQUEST,
                order_index=3,
                delay_days=21,
                delay_hours=0,
            ),
        ]

        return EmailSequenceCreate(
            name=sequence_name,
            description=description or f"Launch email sequence for '{book_title}'.",
            trigger_event="book.launch",
            emails=emails,
            settings={
                "book_title": book_title,
                "author_name": author_name,
                "buy_link": buy_link,
                "preview_link": preview_link,
                "review_link": review_link,
                "launch_date": launch_date.isoformat(),
            },
        )

    def build_custom_sequence(
        self,
        name: str,
        templates: list[dict[str, Any]],
        description: str | None = None,
        trigger_event: str | None = None,
    ) -> EmailSequenceCreate:
        """Build a custom email sequence from user-provided template data."""
        emails = []
        for idx, tmpl in enumerate(templates):
            template_type = tmpl.get("template_type", EmailTemplateType.CUSTOM)
            if isinstance(template_type, str):
                template_type = EmailTemplateType(template_type)

            emails.append(
                EmailTemplateCreate(
                    template_type=template_type,
                    subject=tmpl["subject"],
                    body_html=tmpl.get("body_html"),
                    body_text=tmpl.get("body_text"),
                    delay_days=tmpl.get("delay_days", 0),
                    delay_hours=tmpl.get("delay_hours", 0),
                    order_index=tmpl.get("order_index", idx),
                    personalization_fields=tmpl.get("personalization_fields"),
                )
            )

        return EmailSequenceCreate(
            name=name,
            description=description,
            trigger_event=trigger_event,
            emails=emails,
        )

    def _build_template_email(
        self,
        template_type: EmailTemplateType,
        order_index: int,
        delay_days: int = 0,
        delay_hours: int = 0,
    ) -> EmailTemplateCreate:
        """Build an EmailTemplateCreate from a pre-built template."""
        tmpl = TEMPLATE_MAP.get(template_type, {})
        fields = _extract_personalization_fields(tmpl) if tmpl else []

        return EmailTemplateCreate(
            template_type=template_type,
            subject=tmpl.get("subject", ""),
            body_html=tmpl.get("body_html"),
            body_text=tmpl.get("body_text"),
            delay_days=delay_days,
            delay_hours=delay_hours,
            order_index=order_index,
            personalization_fields=fields,
        )

    @staticmethod
    def personalize_email(
        template_html: str,
        template_text: str,
        subject: str,
        personalization: dict[str, str],
    ) -> dict[str, str]:
        """Apply personalization to an email template.

        Replaces {field_name} placeholders with actual values.
        """
        result_html = template_html or ""
        result_text = template_text or ""
        result_subject = subject or ""

        for field, value in personalization.items():
            placeholder = f"{{{field}}}"
            result_html = result_html.replace(placeholder, value)
            result_text = result_text.replace(placeholder, value)
            result_subject = result_subject.replace(placeholder, value)

        return {
            "subject": result_subject,
            "body_html": result_html,
            "body_text": result_text,
        }
