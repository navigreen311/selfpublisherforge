"""Pydantic schemas for the webhook module."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

from app.modules.webhooks.events import EVENT_TYPES


class WebhookEndpointCreate(BaseModel):
    url: AnyHttpUrl
    description: str | None = None
    events: list[str] = Field(..., min_length=1)
    active: bool = True

    @field_validator("events")
    @classmethod
    def _validate_events(cls, v: list[str]) -> list[str]:
        unknown = [e for e in v if e not in EVENT_TYPES]
        if unknown:
            raise ValueError(f"Unknown event types: {', '.join(unknown)}")
        return v


class WebhookEndpointUpdate(BaseModel):
    url: AnyHttpUrl | None = None
    description: str | None = None
    events: list[str] | None = None
    active: bool | None = None

    @field_validator("events")
    @classmethod
    def _validate_events(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        unknown = [e for e in v if e not in EVENT_TYPES]
        if unknown:
            raise ValueError(f"Unknown event types: {', '.join(unknown)}")
        return v


class WebhookEndpointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    description: str | None
    events: list[str]
    active: bool
    last_triggered_at: datetime | None
    last_status_code: int | None
    created_at: datetime
    # Masked secret — full secret returned only on create / regenerate.
    signing_secret_masked: str = ""


class WebhookEndpointCreated(WebhookEndpointRead):
    """Returned on create; includes the full signing secret (once)."""

    signing_secret: str


class WebhookTestResponse(BaseModel):
    status_code: int | None
    response_body: str | None
    latency_ms: int | None
    delivered: bool


class WebhookLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    endpoint_id: UUID
    event_type: str
    payload: dict[str, Any]
    status_code: int | None
    response_body: str | None
    latency_ms: int | None
    retries: int
    delivered: bool
    created_at: datetime


class EventCatalogEntry(BaseModel):
    type: str
    category: str
    description: str
