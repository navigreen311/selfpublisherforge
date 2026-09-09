"""Pydantic schemas for proof order endpoints."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


Platform = Literal["kdp", "ingramspark"]


class ShippingAddress(BaseModel):
    name: str
    address: str
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = "US"


class Billing(BaseModel):
    method: str | None = None  # e.g. "card_on_file", "invoice"
    reference: str | None = None
    amount: Decimal | None = None


class ProofOrderCreate(BaseModel):
    publishing_id: UUID | None = None
    book_id: UUID | None = None
    quantity: int = Field(default=1, ge=1, le=50)
    platform: Platform
    shipping_address: ShippingAddress
    billing: Billing | None = None
    shipping_method: str | None = "standard"
    interior_file_url: str | None = None
    cover_file_url: str | None = None
    notes: str | None = None


ProofStatus = Literal[
    "ordered",
    "processing",
    "printed",
    "shipped",
    "delivered",
    "reviewed",
    "approved",
    "rejected",
    "cancelled",
]


class ProofOrderStatusUpdate(BaseModel):
    status: ProofStatus
    tracking_number: str | None = None
    estimated_delivery: date | None = None
    notes: str | None = None


class ProofOrderOut(BaseModel):
    id: UUID
    org_id: UUID
    publishing_id: UUID | None
    book_id: UUID | None
    quantity: int
    platform: str | None
    interior_file_url: str | None
    cover_file_url: str | None
    shipping_name: str | None
    shipping_address: str | None
    shipping_method: str | None
    billing: dict | None
    cost: Decimal | None
    tracking_number: str | None
    estimated_delivery: date | None
    status: str
    checklist: dict | None
    issues: str | None
    notes: str | None
    approved: bool
    approved_at: datetime | None
    ordered_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProofOrderListResponse(BaseModel):
    items: list[ProofOrderOut]
    limit: int
    offset: int
    total: int
