"""Event emitter for webhook dispatch.

Signs outgoing payloads with HMAC-SHA256 using each endpoint's signing secret
and attaches the signature via the ``X-Webhook-Signature`` header.

Spec 8B, lines 1054-1074.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.webhooks.models import Webhook, WebhookDelivery

logger = logging.getLogger(__name__)

# Attempt budget (1 initial + retries) -- backoff: 0s, 5s, 30s.
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = [0, 5, 30]
_REQUEST_TIMEOUT = 10.0


def generate_secret() -> str:
    """Return a fresh signing secret (whsec_<random>)."""
    return f"whsec_{secrets.token_urlsafe(32)}"


def mask_secret(secret: str) -> str:
    """Return a display-safe preview of a signing secret."""
    if not secret:
        return ""
    if len(secret) <= 10:
        return "***"
    return f"{secret[:8]}...{secret[-4:]}"


def sign_payload(secret: str, payload_bytes: bytes) -> str:
    """Compute the HMAC-SHA256 signature header value."""
    digest = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def build_event(event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Construct a fully-formed event envelope per spec 8B."""
    return {
        "id": f"evt_{secrets.token_hex(12)}",
        "type": event_type,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": data,
    }


async def _deliver_once(
    client: httpx.AsyncClient,
    webhook: Webhook,
    event: dict[str, Any],
) -> tuple[int | None, str | None, int | None, bool, str | None]:
    """Perform a single HTTP POST attempt. Returns (status, body, latency_ms, delivered, error)."""
    payload_bytes = json.dumps(event, separators=(",", ":")).encode("utf-8")
    signature = sign_payload(webhook.secret, payload_bytes)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": event["type"],
        "X-Webhook-Event-Id": event["id"],
        "User-Agent": "SelfPublisherForge-Webhooks/1.0",
    }

    start = time.monotonic()
    try:
        resp = await client.post(str(webhook.url), content=payload_bytes, headers=headers)
        latency_ms = int((time.monotonic() - start) * 1000)
        body = (resp.text or "")[:2048]
        delivered = 200 <= resp.status_code < 300
        return resp.status_code, body, latency_ms, delivered, None
    except httpx.HTTPError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        return None, None, latency_ms, False, str(exc)[:512]


async def deliver_to_webhook(
    db: AsyncSession,
    webhook: Webhook,
    event: dict[str, Any],
    *,
    retries: bool = True,
) -> WebhookDelivery:
    """Deliver an event to a single webhook, with retries + persisted log."""
    attempts = _MAX_ATTEMPTS if retries else 1
    last_status: int | None = None
    last_body: str | None = None
    last_latency: int | None = None
    last_error: str | None = None
    delivered = False
    attempt_num = 0

    async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
        for i in range(attempts):
            if i > 0:
                await asyncio.sleep(_BACKOFF_SECONDS[min(i, len(_BACKOFF_SECONDS) - 1)])
            attempt_num = i + 1
            (
                last_status,
                last_body,
                last_latency,
                delivered,
                last_error,
            ) = await _deliver_once(client, webhook, event)
            if delivered:
                break

    log = WebhookDelivery(
        webhook_id=webhook.id,
        event_type=event["type"],
        event_id=event.get("id"),
        payload=event,
        status_code=last_status,
        response_body=last_body,
        latency_ms=last_latency,
        attempt=attempt_num,
        delivered=delivered,
        error=last_error,
    )
    db.add(log)

    # Update endpoint health counters.
    webhook.last_triggered_at = datetime.now(timezone.utc)
    webhook.last_status_code = last_status
    webhook.last_error = last_error
    if delivered:
        webhook.failure_count = 0
    else:
        webhook.failure_count = (webhook.failure_count or 0) + 1

    try:
        await db.flush()
    except Exception as exc:  # noqa: BLE001
        logger.warning("webhook delivery log flush failed: %s", exc)

    return log


async def emit_event(
    db: AsyncSession,
    *,
    org_id: UUID,
    event_type: str,
    data: dict[str, Any],
) -> list[WebhookDelivery]:
    """Emit an event to every active webhook in ``org_id`` subscribed to ``event_type``.

    Best-effort: failures never raise to the caller.
    """
    try:
        stmt = select(Webhook).where(
            Webhook.org_id == org_id,
            Webhook.active.is_(True),
            Webhook.events.any(event_type),
        )
        result = await db.execute(stmt)
        webhooks = list(result.scalars().all())
    except Exception as exc:  # noqa: BLE001
        logger.warning("emit_event: failed to query webhooks: %s", exc)
        return []

    if not webhooks:
        return []

    event = build_event(event_type, data)
    deliveries: list[WebhookDelivery] = []
    for webhook in webhooks:
        try:
            delivery = await deliver_to_webhook(db, webhook, event)
            deliveries.append(delivery)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "emit_event: delivery failed for webhook %s: %s", webhook.id, exc
            )
    return deliveries
