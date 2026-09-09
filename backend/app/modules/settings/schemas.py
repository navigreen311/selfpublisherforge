"""Pydantic schemas for settings module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OrgSettingsResponse(BaseModel):
    """Organization settings response schema."""

    name: str
    website: str | None = None
    industry: str | None = None
    imprint_name: str | None = None
    publisher_id: str | None = None
    default_genre: str | None = None
    default_marketplace: str | None = None
    default_currency: str = "USD"
    team_members: list[dict] = Field(default_factory=list)


class OrgSettingsUpdateRequest(BaseModel):
    """Organization settings update request schema."""

    name: str | None = None
    website: str | None = None
    industry: str | None = None
    imprint_name: str | None = None
    default_genre: str | None = None
    default_marketplace: str | None = None
    default_currency: str | None = None


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    current_password: str
    new_password: str = Field(min_length=8)


class Enable2FAResponse(BaseModel):
    """Enable 2FA response schema."""

    secret: str
    qr_code_url: str


class SessionInfo(BaseModel):
    """User session information schema."""

    id: UUID
    device: str
    browser: str
    os: str
    ip_address: str
    location: str
    is_current: bool
    last_active_at: datetime


class LoginHistoryEntry(BaseModel):
    """Login history entry schema."""

    id: UUID
    device: str
    browser: str
    ip_address: str
    location: str
    success: bool
    created_at: datetime


class ApiKeyCreateRequest(BaseModel):
    """API key creation request schema."""

    name: str
    permissions: list[str] = Field(default_factory=lambda: ["read"])


class ApiKeyResponse(BaseModel):
    """API key response schema (without full key)."""

    id: UUID
    name: str
    key_prefix: str
    permissions: list[str]
    last_used_at: datetime | None = None
    created_at: datetime


class ApiKeyCreatedResponse(BaseModel):
    """API key created response schema (includes full key)."""

    id: UUID
    name: str
    key: str
    permissions: list[str]


class WebhookCreateRequest(BaseModel):
    """Webhook creation request schema."""

    url: str
    events: list[str]


class WebhookResponse(BaseModel):
    """Webhook response schema."""

    id: UUID
    url: str
    events: list[str]
    status: str
    last_delivery_at: datetime | None = None
    last_response_code: int | None = None
    created_at: datetime


class WebhookUpdateRequest(BaseModel):
    """Webhook update request schema."""

    url: str | None = None
    events: list[str] | None = None
    status: str | None = None


class NotificationPrefsResponse(BaseModel):
    """Notification preferences response schema."""

    preferences: dict
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None


class NotificationPrefsUpdateRequest(BaseModel):
    """Notification preferences update request schema."""

    preferences: dict | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
