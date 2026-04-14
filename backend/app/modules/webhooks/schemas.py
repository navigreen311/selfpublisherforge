"""Pydantic schemas for webhook CRUD + delivery log."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class WebhookCreate(BaseModel):
    url: HttpUrl
    description: str | None = None
    events: list[str] = Field(default_factory=list, min_length=1)
    active: bool = True

    @field_validator("events")
    @classmethod
    def _strip_events(cls, v: list[str]) -> list[str]:
        cleaned = [e.strip() for e in v if e and e.strip()]
        if not cleaned:
            raise ValueError("At least one event must be provided")
        return cleaned


class WebhookUpdate(BaseModel):
    url: HttpUrl | None = None
    description: str | None = None
    events: list[str] | None = None
    active: bool | None = None


class WebhookOut(BaseModel):
    id: UUID
    url: str
    description: str | None
    events: list[str]
    active: bool
    secret_preview: str
    last_triggered_at: datetime | None
    last_status_code: int | None
    last_error: str | None
    failure_count: int
    created_at: datetime
    updated_at: datetime


class WebhookWithSecretOut(WebhookOut):
    """Returned on create and rotate-secret -- contains full secret (once)."""

    secret: str


class WebhookTestResult(BaseModel):
    status_code: int | None
    response_body: str | None
    latency_ms: int | None
    delivered: bool
    error: str | None = None


class WebhookDeliveryOut(BaseModel):
    id: UUID
    webhook_id: UUID
    event_type: str
    event_id: str | None
    payload: dict[str, Any]
    status_code: int | None
    response_body: str | None
    latency_ms: int | None
    attempt: int
    delivered: bool
    error: str | None
    created_at: datetime
