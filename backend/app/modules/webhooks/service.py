"""Webhook dispatch service.

Exposes ``dispatch_event`` as the canonical entry point for the rest of the
app to emit webhook events. The function itself is cheap: it looks up
subscribers for the given event type and schedules a Celery task per
endpoint so that HTTP delivery (with retries) happens off the request
path.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.modules.webhooks.events import is_valid_event
from app.modules.webhooks.models import WebhookEndpoint, WebhookLog

logger = logging.getLogger(__name__)

SIGNATURE_HEADER = "X-Webhook-Signature"
EVENT_ID_HEADER = "X-Webhook-Event-Id"
EVENT_TYPE_HEADER = "X-Webhook-Event-Type"
DELIVERY_TIMEOUT_SECONDS = 15


def generate_signing_secret() -> str:
    """Return a fresh signing secret in the ``whsec_<token>`` format."""
    return f"whsec_{secrets.token_urlsafe(32)}"


def sign_payload(secret: str, raw_body: bytes) -> str:
    """Return the ``sha256=<hex>`` HMAC header for the given raw body."""
    digest = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, raw_body: bytes, signature: str) -> bool:
    """Timing-safe verification helper usable by consumers / the test button."""
    expected = sign_payload(secret, raw_body)
    return hmac.compare_digest(expected, signature or "")


def build_envelope(event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrap ``data`` in the canonical webhook envelope."""
    return {
        "id": f"evt_{uuid.uuid4().hex[:16]}",
        "type": event_type,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": data,
    }


def mask_secret(secret: str) -> str:
    """Return a ``whsec_***...<last4>`` style masked version of a secret."""
    if not secret:
        return ""
    tail = secret[-4:] if len(secret) >= 8 else ""
    return f"whsec_***...{tail}"


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def dispatch_event(event_type: str, data: dict[str, Any], org_id: UUID | None = None) -> None:
    """Emit an event for delivery to all subscribed webhook endpoints.

    Synchronous helper safe to call from anywhere. Finds endpoints that are
    active and subscribed to ``event_type``, then schedules a Celery delivery
    task per endpoint. Does not block the caller.
    """
    if not is_valid_event(event_type):
        logger.warning("dispatch_event called with unknown event_type=%s", event_type)
        # Still dispatch; the catalog is advisory and consumers may add events.

    envelope = build_envelope(event_type, data)

    # Schedule Celery task; the task itself does DB lookups so that this
    # function never blocks the calling request cycle.
    try:
        from app.modules.webhooks.tasks import dispatch_event_task

        dispatch_event_task.delay(
            event_type=event_type,
            envelope=envelope,
            org_id=str(org_id) if org_id else None,
        )
    except Exception:  # pragma: no cover - celery not available in tests
        logger.exception(
            "Failed to enqueue webhook dispatch task for event=%s", event_type
        )


async def resolve_subscribers(
    db: AsyncSession, event_type: str, org_id: UUID | None = None
) -> list[WebhookEndpoint]:
    """Return all active endpoints subscribed to ``event_type``.

    If ``org_id`` is supplied, scope to that org only. Otherwise fan out
    globally (used by system-level events that span orgs; practical use here
    is opt-in since every event we ship originates from an org scope).
    """
    stmt = select(WebhookEndpoint).where(WebhookEndpoint.active.is_(True))
    if org_id is not None:
        stmt = stmt.where(WebhookEndpoint.org_id == org_id)
    result = await db.execute(stmt)
    # Filter in Python — the events column is a text[] on PostgreSQL and a
    # JSON list on SQLite (tests). Doing the membership check in Python
    # avoids dialect-specific operators (@> vs. json_each), and the typical
    # per-org endpoint count is small (tens, not thousands).
    return [e for e in result.scalars().all() if event_type in (e.events or [])]


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------


async def deliver(
    db: AsyncSession,
    endpoint: WebhookEndpoint,
    envelope: dict[str, Any],
    existing_log: WebhookLog | None = None,
) -> WebhookLog:
    """Perform a single delivery attempt and persist a log entry.

    Returns the log row (updated in place when ``existing_log`` is supplied,
    which happens on retries).
    """
    raw_body = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    signature = sign_payload(endpoint.signing_secret, raw_body)
    headers = {
        "Content-Type": "application/json",
        SIGNATURE_HEADER: signature,
        EVENT_ID_HEADER: str(envelope.get("id", "")),
        EVENT_TYPE_HEADER: str(envelope.get("type", "")),
        "User-Agent": "SelfPublisherForge-Webhooks/1.0",
    }

    start = time.monotonic()
    status_code: int | None = None
    response_body: str | None = None
    delivered = False
    try:
        async with httpx.AsyncClient(timeout=DELIVERY_TIMEOUT_SECONDS) as client:
            resp = await client.post(endpoint.url, content=raw_body, headers=headers)
            status_code = resp.status_code
            response_body = resp.text[:4096]
            delivered = 200 <= resp.status_code < 300
    except httpx.HTTPError as exc:
        response_body = f"request_error: {exc!s}"[:4096]
    latency_ms = int((time.monotonic() - start) * 1000)

    if existing_log is None:
        log = WebhookLog(
            org_id=endpoint.org_id,
            endpoint_id=endpoint.id,
            event_type=str(envelope.get("type", "")),
            payload=envelope,
            status_code=status_code,
            response_body=response_body,
            latency_ms=latency_ms,
            retries=0,
            delivered=delivered,
        )
        db.add(log)
    else:
        existing_log.status_code = status_code
        existing_log.response_body = response_body
        existing_log.latency_ms = latency_ms
        existing_log.retries += 1
        existing_log.delivered = delivered
        log = existing_log

    endpoint.last_triggered_at = datetime.now(timezone.utc)
    endpoint.last_status_code = status_code

    await db.flush()
    return log


async def deliver_test_payload(endpoint: WebhookEndpoint) -> dict[str, Any]:
    """Fire a one-shot test delivery without logging to the DB.

    Used by the "Test" button in the UI so authors can confirm their URL is
    reachable without cluttering the real log table.
    """
    envelope = build_envelope(
        "webhook.test",
        {
            "message": "Hello from SelfPublisherForge",
            "endpoint_id": str(endpoint.id),
        },
    )
    raw_body = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    signature = sign_payload(endpoint.signing_secret, raw_body)
    headers = {
        "Content-Type": "application/json",
        SIGNATURE_HEADER: signature,
        EVENT_TYPE_HEADER: "webhook.test",
    }

    start = time.monotonic()
    status_code: int | None = None
    response_body: str | None = None
    try:
        async with httpx.AsyncClient(timeout=DELIVERY_TIMEOUT_SECONDS) as client:
            resp = await client.post(endpoint.url, content=raw_body, headers=headers)
            status_code = resp.status_code
            response_body = resp.text[:2048]
    except httpx.HTTPError as exc:
        response_body = f"request_error: {exc!s}"[:2048]
    latency_ms = int((time.monotonic() - start) * 1000)
    delivered = status_code is not None and 200 <= status_code < 300

    # Timing-safe sanity check — ensures we did indeed compute the signature
    # the way verify_signature() would reproduce it.
    assert verify_signature(endpoint.signing_secret, raw_body, signature)

    return {
        "status_code": status_code,
        "response_body": response_body,
        "latency_ms": latency_ms,
        "delivered": delivered,
    }


# ---------------------------------------------------------------------------
# Sync wrapper (used by Celery task)
# ---------------------------------------------------------------------------


def deliver_sync(endpoint_id: UUID, envelope: dict[str, Any], log_id: UUID | None = None) -> dict[str, Any]:
    """Synchronous driver used by Celery tasks.

    Opens its own DB session, loads the endpoint, delivers once, writes the
    log row, and returns a small dict describing the outcome. Raises if the
    endpoint could not be reached or responded with a non-2xx so that the
    Celery retry machinery can trigger backoff.
    """

    async def _run() -> dict[str, Any]:
        async with async_session() as session:
            endpoint = await session.get(WebhookEndpoint, endpoint_id)
            if endpoint is None or not endpoint.active:
                return {"skipped": True, "reason": "endpoint_missing_or_inactive"}
            existing_log = None
            if log_id is not None:
                existing_log = await session.get(WebhookLog, log_id)
            log = await deliver(session, endpoint, envelope, existing_log=existing_log)
            await session.commit()
            return {
                "log_id": str(log.id),
                "delivered": log.delivered,
                "status_code": log.status_code,
                "retries": log.retries,
            }

    return asyncio.run(_run())
