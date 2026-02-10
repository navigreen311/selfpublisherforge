# W13: Notifications — Add Email Channel Dispatch

## Files to modify
- `backend/app/modules/notifications/service.py` — Add email sending logic
- `backend/app/modules/notifications/channels.py` — NEW or modify existing email channel

## Context
The notifications module currently handles in-app notifications. It needs email dispatch capability for important events (password reset, invoice, etc.).

## Task

### 1. Read the current notifications module

Read all files in `backend/app/modules/notifications/` to understand the current architecture.

### 2. Add email channel

Create or update an email channel that can send emails via SMTP or AWS SES:

```python
# backend/app/modules/notifications/email_channel.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings

async def send_email(
    to: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> bool:
    """Send an email. Uses SMTP settings from config.

    In production, this would use AWS SES or similar.
    Falls back gracefully if email is not configured.
    """
    settings = get_settings()
    smtp_host = getattr(settings, 'SMTP_HOST', None)

    if not smtp_host:
        # Email not configured - log and return
        import logging
        logging.getLogger(__name__).warning(
            "Email not configured. Skipping email to %s: %s", to, subject
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = getattr(settings, 'SMTP_FROM', 'noreply@selfpublisherforge.com')
        msg["To"] = to

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(smtp_host, getattr(settings, 'SMTP_PORT', 587)) as server:
            server.starttls()
            smtp_user = getattr(settings, 'SMTP_USER', None)
            smtp_pass = getattr(settings, 'SMTP_PASS', None)
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Failed to send email: %s", e)
        return False
```

### 3. Add config settings

Add email config settings to `backend/app/config.py` (if not already present):
```python
SMTP_HOST: str | None = None
SMTP_PORT: int = 587
SMTP_USER: str | None = None
SMTP_PASS: str | None = None
SMTP_FROM: str = "noreply@selfpublisherforge.com"
```

### 4. Integrate with notification service

Update the notification service to dispatch emails for appropriate notification types (e.g., invitation, password reset, report completed).

### 5. Add email templates

Create basic HTML email templates as string templates for common notifications:
- Welcome email
- Password reset
- Invitation to organization
- Report ready for download
