"""HTTP endpoints for webhook endpoint management and delivery logs."""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.webhooks.events import EVENT_CATALOG
from app.modules.webhooks.models import WebhookEndpoint, WebhookLog
from app.modules.webhooks.schemas import (
    EventCatalogEntry,
    WebhookEndpointCreate,
    WebhookEndpointCreated,
    WebhookEndpointRead,
    WebhookEndpointUpdate,
    WebhookLogRead,
    WebhookTestResponse,
)
from app.modules.webhooks.service import (
    deliver_test_payload,
    generate_signing_secret,
    mask_secret,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _to_read(ep: WebhookEndpoint) -> WebhookEndpointRead:
    return WebhookEndpointRead(
        id=ep.id,
        url=ep.url,
        description=ep.description,
        events=list(ep.events or []),
        active=ep.active,
        last_triggered_at=ep.last_triggered_at,
        last_status_code=ep.last_status_code,
        created_at=ep.created_at,
        signing_secret_masked=mask_secret(ep.signing_secret),
    )


@router.get("/events", response_model=list[EventCatalogEntry])
async def list_event_catalog(
    _user: dict = Depends(get_current_user),
) -> list[EventCatalogEntry]:
    """Return the full catalog of webhook event types for the picker UI."""
    return [
        EventCatalogEntry(
            type=e["type"], category=e["category"], description=e["description"]
        )
        for e in EVENT_CATALOG
    ]


@router.get("", response_model=list[WebhookEndpointRead])
async def list_endpoints(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WebhookEndpointRead]:
    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.org_id == current_user["org_id"]
    )
    result = await db.execute(stmt)
    return [_to_read(ep) for ep in result.scalars().all()]


@router.post(
    "",
    response_model=WebhookEndpointCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_endpoint(
    body: WebhookEndpointCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookEndpointCreated:
    secret = generate_signing_secret()
    ep = WebhookEndpoint(
        org_id=current_user["org_id"],
        url=str(body.url),
        description=body.description,
        events=body.events,
        active=body.active,
        signing_secret=secret,
    )
    db.add(ep)
    await db.flush()
    await db.refresh(ep)
    return WebhookEndpointCreated(
        **_to_read(ep).model_dump(),
        signing_secret=secret,
    )


@router.patch("/{endpoint_id}", response_model=WebhookEndpointRead)
async def update_endpoint(
    endpoint_id: UUID,
    body: WebhookEndpointUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookEndpointRead:
    ep = await _get_endpoint_or_404(db, endpoint_id, current_user["org_id"])
    data = body.model_dump(exclude_unset=True)
    if "url" in data and data["url"] is not None:
        ep.url = str(data["url"])
    if "description" in data:
        ep.description = data["description"]
    if "events" in data and data["events"] is not None:
        ep.events = data["events"]
    if "active" in data and data["active"] is not None:
        ep.active = data["active"]
    await db.flush()
    await db.refresh(ep)
    return _to_read(ep)


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(
    endpoint_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    ep = await _get_endpoint_or_404(db, endpoint_id, current_user["org_id"])
    await db.delete(ep)


@router.post("/{endpoint_id}/test", response_model=WebhookTestResponse)
async def test_endpoint(
    endpoint_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookTestResponse:
    ep = await _get_endpoint_or_404(db, endpoint_id, current_user["org_id"])
    result = await deliver_test_payload(ep)
    return WebhookTestResponse(**result)


@router.get("/{endpoint_id}/logs", response_model=list[WebhookLogRead])
async def list_logs(
    endpoint_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WebhookLogRead]:
    await _get_endpoint_or_404(db, endpoint_id, current_user["org_id"])
    stmt = (
        select(WebhookLog)
        .where(WebhookLog.endpoint_id == endpoint_id)
        .order_by(WebhookLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [WebhookLogRead.model_validate(log) for log in result.scalars().all()]


@router.post(
    "/logs/{log_id}/retry",
    response_model=WebhookLogRead,
)
async def retry_log(
    log_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookLogRead:
    log = await db.get(WebhookLog, log_id)
    if log is None or log.org_id != current_user["org_id"]:
        raise HTTPException(status_code=404, detail="Webhook log not found")
    ep = await db.get(WebhookEndpoint, log.endpoint_id)
    if ep is None or ep.org_id != current_user["org_id"]:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")

    from app.modules.webhooks.service import deliver

    updated = await deliver(db, ep, log.payload, existing_log=log)
    await db.flush()
    await db.refresh(updated)
    return WebhookLogRead.model_validate(updated)


async def _get_endpoint_or_404(
    db: AsyncSession, endpoint_id: UUID, org_id: UUID
) -> WebhookEndpoint:
    ep = await db.get(WebhookEndpoint, endpoint_id)
    if ep is None or ep.org_id != org_id:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")
    return ep
