"""Pydantic schemas for the Proof Orders module."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


CHECKLIST_KEYS = (
    "print_quality",
    "colors",
    "text",
    "pages",
    "cover",
    "spine",
    "barcode",
    "overall",
)


class ShippingMethod(str, Enum):
    STANDARD = "standard"
    EXPEDITED = "expedited"
    PRIORITY = "priority"


class ProofStatus(str, Enum):
    ORDERED = "ordered"
    PRINTING = "printing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class IssuesLevel(str, Enum):
    NONE = "none"
    MINOR = "minor"
    MAJOR = "major"


class ShippingAddress(BaseModel):
    name: str = Field(..., max_length=255)
    address: str
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=10)
    zip: str = Field(..., max_length=20)


class ProofOrderCreate(BaseModel):
    interior_file_url: str
    cover_file_url: str
    trim_size: str | None = None
    page_count: int | None = Field(None, ge=24, le=828)
    interior_type: str | None = None  # black_white | standard_color | premium_color
    shipping_address: ShippingAddress
    shipping_method: ShippingMethod = ShippingMethod.STANDARD


class ProofOrderSkip(BaseModel):
    reason: str | None = None


class Checklist(BaseModel):
    print_quality: bool = False
    colors: bool = False
    text: bool = False
    pages: bool = False
    cover: bool = False
    spine: bool = False
    barcode: bool = False
    overall: bool = False

    def all_checked(self) -> bool:
        return all(
            getattr(self, k) for k in CHECKLIST_KEYS
        )


class ProofReviewUpdate(BaseModel):
    checklist: Checklist
    issues: IssuesLevel = IssuesLevel.NONE
    notes: str | None = None
    approved: bool = False


class ProofOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    publishing_id: UUID
    book_id: UUID | None
    interior_file_url: str
    cover_file_url: str
    trim_size: str | None
    page_count: int | None
    interior_type: str | None
    shipping_name: str | None
    shipping_address: str | None
    shipping_city: str | None
    shipping_state: str | None
    shipping_zip: str | None
    shipping_method: str | None
    print_cost: Decimal | None
    shipping_cost: Decimal | None
    cost: Decimal | None
    tracking_number: str | None
    estimated_delivery: date | None
    status: str
    checklist: dict | None
    issues: str | None
    notes: str | None
    approved: bool
    approved_at: datetime | None
    skipped: bool
    ordered_at: datetime


class ProofCostEstimate(BaseModel):
    print_cost: Decimal
    shipping_cost: Decimal
    total: Decimal
    currency: str = "USD"
