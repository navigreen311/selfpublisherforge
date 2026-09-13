"""Pydantic schemas for the billing module."""

from __future__ import annotations

import os
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import PlanTier

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")


# ---------------------------------------------------------------------------
# Plan schemas
# ---------------------------------------------------------------------------


class PlanFeature(BaseModel):
    """A single feature included in a plan."""

    name: str


class PlanInfo(BaseModel):
    """Public-facing plan information."""

    tier: PlanTier
    name: str
    price_monthly: int = Field(description="Price in cents")
    description: str
    max_projects: int | None = Field(description="None means unlimited")
    ai_generations_per_day: int
    features: list[str]
    highlight: bool = False

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Subscription schemas
# ---------------------------------------------------------------------------


class SubscriptionResponse(BaseModel):
    """Current subscription state for the requesting organization."""

    org_id: UUID
    plan_tier: PlanTier
    subscription_status: str = Field(description="active | trialing | past_due | canceled | incomplete | none")
    stripe_subscription_id: str | None = None
    stripe_customer_id: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False


# ---------------------------------------------------------------------------
# Usage schemas
# ---------------------------------------------------------------------------


class UsageStats(BaseModel):
    """Current usage statistics for the requesting organization."""

    org_id: UUID
    plan_tier: PlanTier

    # Project usage
    projects_used: int
    projects_limit: int | None = Field(description="None means unlimited")

    # AI generation usage (daily)
    ai_generations_used_today: int
    ai_generations_daily_limit: int

    # Billing period
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None


# ---------------------------------------------------------------------------
# Checkout / Portal request schemas
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    """Request body to create a Stripe Checkout session."""

    plan_tier: PlanTier = Field(description="Target plan tier")
    success_url: str = Field(
        default=f"{FRONTEND_URL}/settings/billing?success=true",
        description="URL to redirect after successful checkout",
    )
    cancel_url: str = Field(
        default=f"{FRONTEND_URL}/settings/billing?canceled=true",
        description="URL to redirect if user cancels checkout",
    )


class CheckoutResponse(BaseModel):
    """Response containing the Stripe Checkout session URL."""

    checkout_url: str
    session_id: str


class PortalRequest(BaseModel):
    """Request body to create a Stripe billing portal session."""

    return_url: str = Field(
        default=f"{FRONTEND_URL}/settings/billing",
        description="URL to redirect when user returns from portal",
    )


class PortalResponse(BaseModel):
    """Response containing the Stripe billing portal URL."""

    portal_url: str


# ---------------------------------------------------------------------------
# Invoice schemas
# ---------------------------------------------------------------------------


class InvoiceItem(BaseModel):
    """A single Stripe invoice."""

    id: str
    number: str | None = None
    status: str
    amount_due: int = Field(description="Amount in cents")
    amount_paid: int = Field(description="Amount in cents")
    currency: str = "usd"
    created: datetime
    period_start: datetime
    period_end: datetime
    hosted_invoice_url: str | None = None
    invoice_pdf: str | None = None


class InvoiceListResponse(BaseModel):
    """List of invoices for the organization."""

    invoices: list[InvoiceItem]
    has_more: bool = False
