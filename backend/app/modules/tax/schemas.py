"""Pydantic schemas for the Tax module."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


TAX_DISCLAIMER = (
    "This is an estimate only. Consult a tax professional for accurate tax "
    "advice. SelfPublisherForge is not a tax advisor."
)


class FilingStatus(str, Enum):
    SINGLE = "single"
    MARRIED_JOINT = "married_joint"
    MARRIED_SEPARATE = "married_separate"
    HEAD_OF_HOUSEHOLD = "head_of_household"


class TaxExpenseBase(BaseModel):
    category: str = Field(..., max_length=100)
    amount: Decimal
    description: str | None = None
    expense_date: date | None = None
    tax_year: int = Field(..., ge=2000, le=2100)
    receipt_url: str | None = None


class TaxExpenseCreate(TaxExpenseBase):
    pass


class TaxExpenseUpdate(BaseModel):
    category: str | None = None
    amount: Decimal | None = None
    description: str | None = None
    expense_date: date | None = None
    receipt_url: str | None = None


class TaxExpenseOut(TaxExpenseBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    org_id: UUID
    created_at: datetime


class IncomeSourceRow(BaseModel):
    source: str
    amount: Decimal
    expects_1099: bool


class QuarterlyEstimate(BaseModel):
    quarter: int
    tax_year: int
    label: str
    due_date: date
    estimated_amount: Decimal
    actual_amount: Decimal | None = None
    paid: bool = False
    paid_date: date | None = None


class TaxDashboard(BaseModel):
    tax_year: int
    filing_status: FilingStatus
    tax_rate: Decimal
    gross_income: Decimal
    estimated_expenses: Decimal
    net_income: Decimal
    estimated_tax_owed: Decimal
    income_by_source: list[IncomeSourceRow]
    quarterly_estimates: list[QuarterlyEstimate]
    next_quarterly_due: date | None = None
    disclaimer: str = TAX_DISCLAIMER


class QuarterlyPaymentUpdate(BaseModel):
    paid: bool
    paid_date: date | None = None
    actual_amount: Decimal | None = None
