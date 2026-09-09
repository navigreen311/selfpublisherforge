"""Pydantic request/response schemas for the admin module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import PlanTier

# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class UserListRequest(BaseModel):
    """Request parameters for listing users."""

    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    search: str | None = None
    tier: PlanTier | None = None


class FeatureFlagUpdateRequest(BaseModel):
    """Request to update a feature flag."""

    enabled: bool
    description: str | None = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class UserListItem(BaseModel):
    """User summary for admin list view."""

    id: UUID
    email: str
    name: str
    created_at: datetime
    tier: PlanTier
    is_active: bool


class UserListResponse(BaseModel):
    """Response containing list of users."""

    users: list[UserListItem]
    total: int


class FeatureFlag(BaseModel):
    """Feature flag details."""

    key: str
    enabled: bool
    description: str | None = None


class FeatureFlagsResponse(BaseModel):
    """Response containing all feature flags."""

    flags: list[FeatureFlag]


# ---------------------------------------------------------------------------
# Platform Statistics
# ---------------------------------------------------------------------------


class PlatformStatsResponse(BaseModel):
    """Platform-wide statistics for admin dashboard."""

    users_total: int
    users_active_week: int
    organizations: int
    books: int
    ai_tasks_month: int
    tokens_month: int
    storage_used_bytes: int
    monthly_revenue: float


# ---------------------------------------------------------------------------
# Activity Log
# ---------------------------------------------------------------------------


class ActivityLogEntry(BaseModel):
    """Individual activity log entry."""

    id: UUID
    user_name: str
    user_email: str
    action: str
    resource_type: str | None
    resource_id: UUID | None
    details: dict | None
    created_at: datetime


class ActivityLogResponse(BaseModel):
    """Response containing activity log entries."""

    activities: list[ActivityLogEntry]
    total: int


class ActivityLogFilters(BaseModel):
    """Filters for activity log queries."""

    action: str | None = None
    resource_type: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    limit: int = 50


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------


class AdminUserDetail(BaseModel):
    """Detailed user information for admin view."""

    id: UUID
    email: str
    name: str
    role: str
    status: str
    org_id: UUID
    org_name: str
    last_active: datetime | None
    books_count: int
    manuscripts_count: int
    ai_tasks_count: int
    permissions: list[str]


class InviteUserRequest(BaseModel):
    """Request to invite a new user."""

    email: str
    role: str = "author"
    message: str | None = None


class UpdateUserRequest(BaseModel):
    """Request to update user settings."""

    role: str | None = None
    status: str | None = None
    permissions: list[str] | None = None


# ---------------------------------------------------------------------------
# Organization Management
# ---------------------------------------------------------------------------


class AdminOrgDetail(BaseModel):
    """Detailed organization information for admin view."""

    id: UUID
    name: str
    slug: str
    plan_tier: str
    owner_name: str
    member_count: int
    books_count: int
    storage_used_bytes: int
    storage_limit_bytes: int
    feature_toggles: dict
    created_at: datetime


class UpdateOrgRequest(BaseModel):
    """Request to update organization settings."""

    name: str | None = None
    feature_toggles: dict | None = None


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------


class BillingOverview(BaseModel):
    """Billing overview for an organization."""

    plan_name: str
    plan_price: float
    next_billing: datetime | None
    usage: dict
    invoices: list[dict]
