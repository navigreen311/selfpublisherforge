"""FastAPI router for Series, Bundles, ISBN, Back Matter, and Multi-Distributor.

Endpoints map to blueprint sections 12.1-12.6.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.specialty_books import service_series

router = APIRouter(
    prefix="/api/v1/specialty",
    tags=["specialty-series"],
)


# ── Inline Pydantic Schemas ─────────────────────────────────────────────────


class BookType(str, Enum):
    CHILDRENS = "childrens"
    COLORING = "coloring"
    PUZZLE = "puzzle"


class DistributorTarget(str, Enum):
    KDP = "kdp"
    INGRAM_SPARK = "ingram_spark"
    BN_PRESS = "bn_press"


# -- Series --


class SeriesCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    book_type: BookType
    naming_format: str | None = Field(
        None, max_length=255,
        description="Template for volume titles, e.g. '{Series Name} Vol. {N}: {Subtitle}'",
    )
    branding_config: dict[str, Any] | None = None
    branding_locked: bool = False


class SeriesResponse(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    book_type: str
    naming_format: str | None = None
    branding_config: dict[str, Any] | None = None
    branding_locked: bool = False
    volume_count: int = 0
    created_at: Any = None

    model_config = ConfigDict(from_attributes=True)


class CoherenceCheckResponse(BaseModel):
    series_id: UUID
    score: int
    issues: list[dict[str, Any]] = Field(default_factory=list)
    volume_count: int = 0


# -- Back Matter --


class BackMatterTemplateInput(BaseModel):
    template_type: str
    cta_url: str | None = None
    author_name: str | None = None
    author_bio: str | None = None
    series_name: str | None = None
    series_description: str | None = None
    volumes: list[dict[str, Any]] | None = None


class GenerateBackMatterRequest(BaseModel):
    templates: list[BackMatterTemplateInput] = Field(..., min_length=1)


class GeneratedPage(BaseModel):
    id: UUID
    template_type: str
    content: str
    qr_code_url: str | None = None


class GenerateBackMatterResponse(BaseModel):
    pages: list[GeneratedPage] = Field(default_factory=list)


# -- QR Code --


class QRCodeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    size_px: int = Field(300, ge=100, le=1000)
    error_correction: str = Field("M", pattern="^[LMQH]$")


class QRCodeResponse(BaseModel):
    qr_code_url: str
    url_encoded: str
    size_px: int


# -- Bundle --


class BundleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    book_type: BookType
    volume_ids: list[UUID] = Field(..., min_length=1)
    series_id: UUID | None = None
    config: dict[str, Any] | None = None
    volume_page_counts: list[dict[str, Any]] | None = None


class BundleResponse(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    book_type: str
    volume_ids: list[str]
    series_id: UUID | None = None
    config: dict[str, Any] | None = None
    total_pages: int = 0
    created_at: Any = None

    model_config = ConfigDict(from_attributes=True)


# -- ISBN --


class ISBNPoolAddRequest(BaseModel):
    isbns: list[str] = Field(..., min_length=1)
    publisher_name: str = Field(..., min_length=1, max_length=255)


class ISBNPoolAddResponse(BaseModel):
    added: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class ISBNAssignRequest(BaseModel):
    book_type: BookType
    book_id: UUID
    publisher_name: str = Field(..., min_length=1, max_length=255)
    isbn: str | None = Field(None, pattern=r"^\d{13}$")


class ISBNAssignResponse(BaseModel):
    id: UUID
    isbn: str
    publisher_name: str | None = None
    assigned_to_book_type: str | None = None
    assigned_to_book_id: UUID | None = None
    barcode_url: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# -- Distributor Preflight --


class PreflightRequest(BaseModel):
    distributor: DistributorTarget
    page_count: int = Field(0, ge=0)


class PreflightCheckResult(BaseModel):
    name: str
    passed: bool
    details: str | None = None
    severity: str = "info"


class DistributorPreflightResponse(BaseModel):
    id: UUID
    book_type: str
    book_id: UUID
    distributor: str
    status: str
    checks: list[PreflightCheckResult] = Field(default_factory=list)
    issues: list[dict[str, Any]] = Field(default_factory=list)
    exported_url: str | None = None
    all_passed: bool = False


# -- Review Feedback --


class ReviewFeedbackRequest(BaseModel):
    complaints: list[str] = Field(..., min_length=1)


class ReviewFeedbackMapping(BaseModel):
    complaint: str
    suggested_fix: str
    automated_action: str | None = None
    automated_action_available: bool = False


class ReviewFeedbackResponse(BaseModel):
    mappings: list[ReviewFeedbackMapping] = Field(default_factory=list)


# ── Series Endpoints ─────────────────────────────────────────────────────────


@router.post(
    "/series",
    response_model=SeriesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a book series",
)
async def create_series(
    body: SeriesCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await service_series.create_series(db, user["org_id"], body.model_dump())
    return result


@router.get(
    "/series/{series_id}",
    response_model=SeriesResponse,
    summary="Get series details",
)
async def get_series(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await service_series.get_series(db, series_id, user["org_id"])
    if result is None:
        raise HTTPException(status_code=404, detail="Series not found")
    return result


@router.post(
    "/series/{series_id}/coherence-check",
    response_model=CoherenceCheckResponse,
    summary="Run theme coherence check on a series",
)
async def check_coherence(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        result = await service_series.check_series_coherence(db, series_id, user["org_id"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "series_id": series_id,
        "score": result["score"],
        "issues": result["issues"],
        "volume_count": result["volume_count"],
    }


# ── Back Matter Endpoints ────────────────────────────────────────────────────


@router.post(
    "/{book_type}/{book_id}/generate-back-matter",
    response_model=GenerateBackMatterResponse,
    summary="Generate back-matter pages for a book",
)
async def generate_back_matter(
    book_type: str,
    book_id: UUID,
    body: GenerateBackMatterRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    templates = [t.model_dump() for t in body.templates]
    pages = await service_series.generate_back_matter(
        db, book_type, book_id, user["org_id"], templates,
    )
    return {"pages": pages}


@router.post(
    "/{book_type}/{book_id}/generate-qr-code",
    response_model=QRCodeResponse,
    summary="Generate a QR code from a URL",
)
async def generate_qr_code(
    book_type: str,
    book_id: UUID,
    body: QRCodeRequest,
    user: dict = Depends(get_current_user),
):
    result = service_series.generate_qr_code(
        body.url, body.size_px, body.error_correction,
    )
    return {
        "qr_code_url": result["qr_code_data_uri"],
        "url_encoded": result["url_encoded"],
        "size_px": result["size_px"],
    }


# ── Bundle Endpoints ─────────────────────────────────────────────────────────


@router.post(
    "/bundles",
    response_model=BundleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bundle / box set",
)
async def create_bundle(
    body: BundleCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await service_series.create_bundle(db, user["org_id"], body.model_dump())
    return result


@router.get(
    "/bundles/{bundle_id}",
    response_model=BundleResponse,
    summary="Get bundle details",
)
async def get_bundle(
    bundle_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await service_series.get_bundle(db, bundle_id, user["org_id"])
    if result is None:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return result


# ── ISBN Endpoints ───────────────────────────────────────────────────────────


@router.post(
    "/isbn",
    response_model=ISBNPoolAddResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add ISBNs to pool",
)
async def add_isbns(
    body: ISBNPoolAddRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await service_series.manage_isbn(
        db, user["org_id"], "add_to_pool",
        {"isbns": body.isbns, "publisher_name": body.publisher_name},
    )
    return result


@router.get(
    "/isbn",
    summary="Get ISBN pool status",
)
async def get_isbn_pool(
    isbn: str = Query(..., description="ISBN-13 to look up"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        return await service_series.manage_isbn(
            db, user["org_id"], "get_status", {"isbn": isbn},
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post(
    "/isbn/{isbn_id}/assign",
    response_model=ISBNAssignResponse,
    summary="Assign ISBN to a book",
)
async def assign_isbn(
    isbn_id: UUID,
    body: ISBNAssignRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        result = await service_series.manage_isbn(
            db, user["org_id"], "assign",
            {
                "isbn": body.isbn,
                "book_type": body.book_type.value,
                "book_id": body.book_id,
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


# ── Distributor Preflight Endpoint ───────────────────────────────────────────


@router.post(
    "/{book_type}/{book_id}/distributor-preflight",
    response_model=DistributorPreflightResponse,
    summary="Run multi-distributor preflight checks",
)
async def distributor_preflight(
    book_type: str,
    book_id: UUID,
    body: PreflightRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await service_series.run_distributor_preflight(
        db, book_type, book_id, user["org_id"],
        body.distributor.value,
        page_count=body.page_count,
    )
    return {
        "id": result["id"],
        "book_type": book_type,
        "book_id": book_id,
        "distributor": body.distributor.value,
        "status": result["status"],
        "checks": result["checks"],
        "issues": [c for c in result["checks"] if not c["passed"]],
        "exported_url": result.get("export_url"),
        "all_passed": result["all_passed"],
    }


# ── Review Feedback Endpoint ────────────────────────────────────────────────


@router.post(
    "/{book_type}/{book_id}/review-feedback",
    response_model=ReviewFeedbackResponse,
    summary="Map review complaints to actionable fixes",
)
async def review_feedback(
    book_type: str,
    book_id: UUID,
    body: ReviewFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await service_series.process_review_feedback(
        db, book_type, book_id, user["org_id"], body.complaints,
    )
    return result
