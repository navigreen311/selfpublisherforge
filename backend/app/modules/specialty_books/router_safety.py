"""FastAPI router for Safety & Compliance endpoints.

Provides originality fingerprinting, spam checking, trademark safety,
content sensitivity, and full compliance reporting.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty_books import service_safety as svc

router = APIRouter()


# ── Request / Response Schemas ──────────────────────────────────────────


class FingerprintRequest(BaseModel):
    """Request to generate originality fingerprints for a book."""

    book_type: str = Field(..., description="One of: childrens, coloring, puzzle")
    book_id: UUID
    org_id: UUID | None = Field(None, description="Defaults to the authenticated user's org.")


class CompareRequest(BaseModel):
    """Request to compare originality of two books."""

    book_type: str = Field("childrens", description="One of: childrens, coloring, puzzle")
    book_id_1: UUID
    book_id_2: UUID
    org_id: UUID | None = Field(None, description="Defaults to the authenticated user's org.")


class SpamCheckRequest(BaseModel):
    """Request to run KDP spam risk detection on a book."""

    book_type: str = Field(..., description="One of: childrens, coloring, puzzle")
    book_id: UUID
    org_id: UUID | None = Field(None, description="Defaults to the authenticated user's org.")


class SafetyCheckRequest(BaseModel):
    """Request for combined trademark + content sensitivity check."""

    text: str = Field(..., min_length=1, max_length=50000)
    context: str = Field("general", description="Where the text comes from.")
    age_range: str | None = Field(None, description="Target age range, e.g. '3-5'.")


class SafetyCheckResponse(BaseModel):
    """Combined trademark and sensitivity check result."""

    trademark_violations: list[dict[str, Any]] = Field(default_factory=list)
    sensitivity_issues: list[dict[str, Any]] = Field(default_factory=list)
    passed: bool
    total_issues: int


# ── Endpoints ───────────────────────────────────────────────────────────


@router.post(
    "/originality/fingerprint",
    summary="Generate originality fingerprint",
    description="Generate multi-method originality fingerprints for a book.",
)
async def generate_fingerprint(
    body: FingerprintRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = body.org_id or current_user["org_id"]
    result = await svc.generate_originality_fingerprint(
        db, body.book_type, body.book_id, org_id,
    )
    return result


@router.post(
    "/originality/compare",
    summary="Compare originality of two books",
    description="Compare fingerprints between two books and return similarity report.",
)
async def compare_originality(
    body: CompareRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = body.org_id or current_user["org_id"]
    result = await svc.compare_originality(
        db, body.book_id_1, body.book_id_2, org_id, body.book_type,
    )
    return result


@router.post(
    "/originality/spam-check",
    summary="Run KDP spam risk detection",
    description="Analyze a book for KDP spam risk factors and return a risk score.",
)
async def spam_check(
    body: SpamCheckRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = body.org_id or current_user["org_id"]
    result = await svc.run_spam_check(db, body.book_type, body.book_id, org_id)
    return result


@router.post(
    "/{book_type}/{book_id}/safety-check",
    response_model=SafetyCheckResponse,
    summary="Combined trademark + sensitivity check",
    description="Run trademark blocklist and content sensitivity checks on provided text.",
)
async def safety_check(
    book_type: str,
    book_id: UUID,
    body: SafetyCheckRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    trademark_violations = svc.check_trademark_safety(body.text, body.context)
    sensitivity_issues = svc.check_content_sensitivity(body.text, body.age_range)

    error_violations = [v for v in trademark_violations if v["severity"] == "error"]
    block_issues = [i for i in sensitivity_issues if i["severity"] == "block"]
    passed = len(error_violations) == 0 and len(block_issues) == 0

    return SafetyCheckResponse(
        trademark_violations=trademark_violations,
        sensitivity_issues=sensitivity_issues,
        passed=passed,
        total_issues=len(trademark_violations) + len(sensitivity_issues),
    )


@router.get(
    "/{book_type}/{book_id}/compliance-report",
    summary="Get full compliance report",
    description="Generate a comprehensive compliance report aggregating all safety checks.",
)
async def get_compliance_report(
    book_type: str,
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user["org_id"]
    result = await svc.generate_compliance_report(db, book_type, book_id, org_id)
    return result
