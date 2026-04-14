"""Celery tasks for webhook delivery with exponential backoff."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.modules.webhooks.service import (
    deliver_sync,
    resolve_subscribers,
)
from app.tasks import celery_app

logger = logging.getLogger(__name__)

# Spec: 5 retries -> 1min, 5min, 15min, 1hr, 6hr
RETRY_BACKOFF_SECONDS: list[int] = [60, 300, 900, 3600, 21600]
MAX_RETRIES = len(RETRY_BACKOFF_SECONDS)


def _backoff_for(attempt: int) -> int:
    if attempt < 0:
        return RETRY_BACKOFF_SECONDS[0]
    if attempt >= len(RETRY_BACKOFF_SECONDS):
        return RETRY_BACKOFF_SECONDS[-1]
    return RETRY_BACKOFF_SECONDS[attempt]


@celery_app.task(
    name="webhooks.dispatch_event",
    bind=True,
    acks_late=True,
    soft_time_limit=60,
    time_limit=120,
)
def dispatch_event_task(
    self,
    event_type: str,
    envelope: dict[str, Any],
    org_id: str | None = None,
) -> dict[str, Any]:
    """Fan out an event to all subscribers and schedule deliveries.

    The task does not make the HTTP calls directly; it enqueues a separate
    ``webhooks.deliver_single`` task per endpoint so each delivery has its
    own retry budget.
    """
    from uuid import UUID

    from app.database import async_session

    async def _run() -> list[str]:
        async with async_session() as session:
            subs = await resolve_subscribers(
                session,
                event_type,
                UUID(org_id) if org_id else None,
            )
            return [str(s.id) for s in subs]

    endpoint_ids = asyncio.run(_run())
    for ep_id in endpoint_ids:
        deliver_single.delay(
            endpoint_id=ep_id,
            envelope=envelope,
            log_id=None,
            attempt=0,
        )
    return {"event_type": event_type, "fanned_out": len(endpoint_ids)}


@celery_app.task(
    name="webhooks.deliver_single",
    bind=True,
    acks_late=True,
    soft_time_limit=30,
    time_limit=60,
)
def deliver_single(
    self,
    endpoint_id: str,
    envelope: dict[str, Any],
    log_id: str | None = None,
    attempt: int = 0,
) -> dict[str, Any]:
    """Deliver a single webhook and retry with exponential backoff on failure.

    Celery retry countdowns: 1m, 5m, 15m, 1h, 6h (5 total retries).
    Marks as delivered only on 2xx HTTP responses.
    """
    from uuid import UUID

    result: dict[str, Any] = {}
    try:
        result = deliver_sync(
            endpoint_id=UUID(endpoint_id),
            envelope=envelope,
            log_id=UUID(log_id) if log_id else None,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Webhook delivery threw (attempt=%s endpoint=%s): %s",
            attempt,
            endpoint_id,
            exc,
        )
        result = {"delivered": False, "error": str(exc)}

    if result.get("skipped"):
        return result

    if result.get("delivered"):
        return result

    if attempt >= MAX_RETRIES - 1:
        logger.error(
            "Webhook permanently failed after %s attempts: endpoint=%s",
            attempt + 1,
            endpoint_id,
        )
        return {**result, "exhausted": True}

    countdown = _backoff_for(attempt)
    # Reuse the log row that was just written so retry count increments
    # monotonically and operators see every attempt in the UI.
    next_log_id = result.get("log_id") or log_id
    raise self.retry(
        exc=RuntimeError(f"non-2xx: {result.get('status_code')}"),
        countdown=countdown,
        max_retries=MAX_RETRIES,
        kwargs={
            "endpoint_id": endpoint_id,
            "envelope": envelope,
            "log_id": next_log_id,
            "attempt": attempt + 1,
        },
    )
