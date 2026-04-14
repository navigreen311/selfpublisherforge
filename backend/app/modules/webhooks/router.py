"""REST API for webhook management (Feature 8C)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.webhooks.emitter import (
    build_event,
    deliver_to_webhook,
    generate_secret,
    mask_secret,
)
from app.modules.webhooks.models import KNOWN_EVENTS, Webhook, WebhookDelivery
from app.modules.webhooks.schemas import (
    WebhookCreate,
    WebhookDeliveryOut,
    WebhookOut,
    WebhookTestResult,
    WebhookUpdate,
    WebhookWithSecretOut,
)

router = APIRouter()


def _serialize(w: Webhook, *, include_secret: bool = False) -> dict[str, Any]:
    base = {
        "id": w.id,
        "url": w.url,
        "description": w.description,
        "events": list(w.events or []),
        "active": w.active,
        "secret_preview": mask_secret(w.secret),
        "last_triggered_at": w.last_triggered_at,
        "last_status_code": w.last_status_code,
        "last_error": w.last_error,
        "failure_count": w.failure_count or 0,
        "created_at": w.created_at,
        "updated_at": w.updated_at,
    }
    if include_secret:
        base["secret"] = w.secret
    return base


async def _get_webhook_or_404(
    db: AsyncSession, webhook_id: UUID, org_id: UUID
) -> Webhook:
    stmt = select(Webhook).where(Webhook.id == webhook_id, Webhook.org_id == org_id)
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()
    if webhook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    return webhook


@router.get("/events", summary="List known webhook event types")
async def list_events(_user: dict = Depends(get_current_user)) -> dict[str, list[str]]:
    """Return the catalog of event types publishers can subscribe to."""
    return {"events": KNOWN_EVENTS}


@router.get("", response_model=list[WebhookOut], summary="List webhooks")
async def list_webhooks(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = (
        select(Webhook)
        .where(Webhook.org_id == current_user["org_id"])
        .order_by(Webhook.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_serialize(w) for w in rows]


@router.post(
    "",
    response_model=WebhookWithSecretOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create webhook",
)
async def create_webhook(
    body: WebhookCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    webhook = Webhook(
        org_id=current_user["org_id"],
        url=str(body.url),
        description=body.description,
        events=body.events,
        secret=generate_secret(),
        active=body.active,
    )
    db.add(webhook)
    await db.flush()
    await db.commit()
    await db.refresh(webhook)
    return _serialize(webhook, include_secret=True)


@router.patch("/{webhook_id}", response_model=WebhookOut, summary="Update webhook")
async def update_webhook(
    webhook_id: UUID,
    body: WebhookUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    webhook = await _get_webhook_or_404(db, webhook_id, current_user["org_id"])
    if body.url is not None:
        webhook.url = str(body.url)
    if body.description is not None:
        webhook.description = body.description
    if body.events is not None:
        if not body.events:
            raise HTTPException(status_code=400, detail="At least one event required")
        webhook.events = body.events
    if body.active is not None:
        webhook.active = body.active
    webhook.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(webhook)
    return _serialize(webhook)


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete webhook",
)
async def delete_webhook(
    webhook_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    webhook = await _get_webhook_or_404(db, webhook_id, current_user["org_id"])
    await db.delete(webhook)
    await db.commit()


@router.post(
    "/{webhook_id}/test",
    response_model=WebhookTestResult,
    summary="Send a test event to a webhook",
)
async def test_webhook(
    webhook_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    webhook = await _get_webhook_or_404(db, webhook_id, current_user["org_id"])
    event = build_event(
        "webhook.test",
        {
            "message": "This is a test event from SelfPublisherForge.",
            "webhook_id": str(webhook.id),
        },
    )
    delivery = await deliver_to_webhook(db, webhook, event, retries=False)
    await db.commit()
    return {
        "status_code": delivery.status_code,
        "response_body": delivery.response_body,
        "latency_ms": delivery.latency_ms,
        "delivered": delivery.delivered,
        "error": delivery.error,
    }


@router.get(
    "/{webhook_id}/deliveries",
    response_model=list[WebhookDeliveryOut],
    summary="List recent delivery attempts for a webhook",
)
async def list_deliveries(
    webhook_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    await _get_webhook_or_404(db, webhook_id, current_user["org_id"])
    stmt = (
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": d.id,
            "webhook_id": d.webhook_id,
            "event_type": d.event_type,
            "event_id": d.event_id,
            "payload": d.payload or {},
            "status_code": d.status_code,
            "response_body": d.response_body,
            "latency_ms": d.latency_ms,
            "attempt": d.attempt,
            "delivered": d.delivered,
            "error": d.error,
            "created_at": d.created_at,
        }
        for d in rows
    ]


@router.post(
    "/{webhook_id}/rotate-secret",
    response_model=WebhookWithSecretOut,
    summary="Rotate the signing secret",
)
async def rotate_secret(
    webhook_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    webhook = await _get_webhook_or_404(db, webhook_id, current_user["org_id"])
    webhook.secret = generate_secret()
    webhook.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(webhook)
    return _serialize(webhook, include_secret=True)
