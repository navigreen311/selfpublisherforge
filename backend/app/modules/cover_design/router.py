"""FastAPI router for the Cover Design Studio.

Endpoints:
    POST /api/v1/covers/generate            — Generate cover concept via AI
    GET  /api/v1/covers/templates            — List cover templates by genre
    POST /api/v1/covers/analyze-competitors  — Analyse competitor covers
    POST /api/v1/covers/{id}/variations      — Generate variations of a cover
    GET  /api/v1/covers/book/{book_id}       — List covers for a book
    DELETE /api/v1/covers/{id}               — Delete a cover
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.cover_design import service
from app.modules.cover_design.schemas import (
    CompetitorAnalysisResponse,
    CompetitorCoverAnalysisRequest,
    CoverGenerateRequest,
    CoverGenre,
    CoverResponse,
    CoverTemplateResponse,
    CoverVariationRequest,
)
from shared.contracts.api import SuccessResponse

router = APIRouter(prefix="/covers", tags=["covers"])

# ---------------------------------------------------------------------------
# Placeholder dependency — will be replaced by real auth in production
# ---------------------------------------------------------------------------

_PLACEHOLDER_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


async def _get_org_id() -> UUID:
    """Return the current organisation ID.

    In production this is extracted from the JWT token via the auth middleware.
    """
    return _PLACEHOLDER_ORG_ID


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/generate",
    response_model=SuccessResponse[CoverResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate a cover concept via AI",
)
async def generate_cover(
    request: CoverGenerateRequest,
    db: AsyncSession = Depends(get_db),
    org_id: UUID = Depends(_get_org_id),
):
    cover = await service.generate_cover(db, org_id, request)
    return SuccessResponse(data=cover)


@router.get(
    "/templates",
    response_model=SuccessResponse[list[CoverTemplateResponse]],
    summary="List cover templates, optionally filtered by genre",
)
async def list_templates(
    genre: CoverGenre | None = Query(None, description="Filter templates by genre"),
):
    templates = await service.list_templates(genre)
    return SuccessResponse(data=templates)


@router.post(
    "/analyze-competitors",
    response_model=SuccessResponse[CompetitorAnalysisResponse],
    summary="Analyse competitor covers in a niche",
)
async def analyze_competitors(
    request: CompetitorCoverAnalysisRequest,
):
    analysis = await service.analyze_competitors(request)
    return SuccessResponse(data=analysis)


@router.post(
    "/{cover_id}/variations",
    response_model=SuccessResponse[list[CoverResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Generate variations of an existing cover",
)
async def create_variations(
    cover_id: UUID,
    request: CoverVariationRequest,
    db: AsyncSession = Depends(get_db),
    org_id: UUID = Depends(_get_org_id),
):
    try:
        variations = await service.create_variations(db, org_id, cover_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return SuccessResponse(data=variations)


@router.get(
    "/book/{book_id}",
    response_model=SuccessResponse[list[CoverResponse]],
    summary="List covers for a specific book",
)
async def list_covers_for_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    org_id: UUID = Depends(_get_org_id),
):
    covers = await service.list_covers_for_book(db, org_id, book_id)
    return SuccessResponse(data=covers)


@router.delete(
    "/{cover_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cover (soft-delete)",
)
async def delete_cover(
    cover_id: UUID,
    db: AsyncSession = Depends(get_db),
    org_id: UUID = Depends(_get_org_id),
):
    deleted = await service.delete_cover(db, org_id, cover_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cover {cover_id} not found",
        )
    return None
