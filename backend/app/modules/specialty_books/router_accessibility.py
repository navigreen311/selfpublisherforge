"""API endpoints for accessibility variants and layout protection.

Provides:
- POST /api/v1/specialty/{type}/{id}/generate-accessible-variant
- POST /api/v1/specialty/{type}/{id}/safe-zone-heatmap
- POST /api/v1/specialty/{type}/{id}/gutter-check
- POST /api/v1/specialty/{type}/{id}/reflow
- POST /api/v1/specialty/{type}/{id}/accessibility-compliance
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.specialty_books import service_accessibility as acc_svc
from app.modules.specialty_books import service_layout_protection as layout_svc
from app.modules.specialty_books.service_accessibility import (
    VARIANT_DYSLEXIA,
    VARIANT_HIGH_CONTRAST,
    VARIANT_LARGE_PRINT,
)

router = APIRouter(prefix="/api/v1/specialty", tags=["accessibility-layout"])

_DEFAULT_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _org_id() -> uuid.UUID:
    return _DEFAULT_ORG_ID


class AccessibleVariantRequest(BaseModel):
    variant_type: str = Field(..., description="dyslexia_friendly, large_print, or high_contrast")
    settings: dict[str, Any] | None = Field(None, description="Optional overrides")


class SafeZoneHeatmapRequest(BaseModel):
    page_id: uuid.UUID


class ReflowRequest(BaseModel):
    target_trim_size: str = Field(..., description="e.g. '6x9', '8.5x11'")


class ComplianceCheckRequest(BaseModel):
    standard: str = Field("WCAG_AA", description="WCAG_AA or WCAG_AAA")


@router.post(
    "/{book_type}/{book_id}/generate-accessible-variant",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Generate an accessible variant of a book",
)
async def generate_accessible_variant(
    book_type: str,
    book_id: uuid.UUID,
    body: AccessibleVariantRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(_org_id),
) -> dict[str, Any]:
    try:
        if body.variant_type == VARIANT_DYSLEXIA:
            return await acc_svc.generate_dyslexia_friendly(db, book_type, book_id, org_id)
        if body.variant_type == VARIANT_LARGE_PRINT:
            return await acc_svc.generate_large_print(db, book_type, book_id, org_id, settings=body.settings)
        if body.variant_type == VARIANT_HIGH_CONTRAST:
            return await acc_svc.generate_high_contrast(db, book_type, book_id, org_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown variant type: {body.variant_type}"
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{book_type}/{book_id}/safe-zone-heatmap",
    response_model=dict[str, Any],
    summary="Generate safe-zone heatmap overlay for a page",
)
async def safe_zone_heatmap(
    book_type: str,
    book_id: uuid.UUID,
    body: SafeZoneHeatmapRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(_org_id),
) -> dict[str, Any]:
    try:
        return await layout_svc.generate_safe_zone_heatmap(db, book_type, book_id, body.page_id, org_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{book_type}/{book_id}/gutter-check", response_model=dict[str, Any], summary="Detect content near the fold/spine"
)
async def gutter_check(
    book_type: str,
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(_org_id),
) -> dict[str, Any]:
    try:
        return await layout_svc.check_gutter_collisions(db, book_type, book_id, org_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{book_type}/{book_id}/reflow",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Reflow layout for an alternate trim size",
)
async def reflow(
    book_type: str,
    book_id: uuid.UUID,
    body: ReflowRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(_org_id),
) -> dict[str, Any]:
    try:
        return await layout_svc.generate_reflow(db, book_type, book_id, org_id, body.target_trim_size)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post(
    "/{book_type}/{book_id}/accessibility-compliance",
    response_model=dict[str, Any],
    summary="Check book against accessibility standards",
)
async def accessibility_compliance(
    book_type: str,
    book_id: uuid.UUID,
    body: ComplianceCheckRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(_org_id),
) -> dict[str, Any]:
    try:
        return await acc_svc.check_accessibility_compliance(db, book_type, book_id, org_id, standard=body.standard)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
