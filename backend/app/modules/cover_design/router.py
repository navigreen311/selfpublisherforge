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

from app.core.dependencies import get_current_user
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
from app.core.contracts import SuccessResponse

router = APIRouter(prefix="/covers", tags=["covers"])


@router.post(
    "/generate",
    response_model=SuccessResponse[CoverResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate a cover concept via AI",
    description="Generate an AI cover concept based on genre, title, and style preferences.",
)
async def generate_cover(
    request: CoverGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cover = await service.generate_cover(db, current_user["org_id"], request)
    return SuccessResponse(data=cover)


@router.get(
    "/templates",
    response_model=SuccessResponse[list[CoverTemplateResponse]],
    summary="List cover templates, optionally filtered by genre",
    description="List available cover design templates with optional genre filter.",
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
    description="Analyse competitor covers to identify trends, color palettes, and design patterns.",
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
    description="Generate style or color variations of an existing cover design.",
)
async def create_variations(
    cover_id: UUID,
    request: CoverVariationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        variations = await service.create_variations(db, current_user["org_id"], cover_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return SuccessResponse(data=variations)


@router.get(
    "/book/{book_id}",
    response_model=SuccessResponse[list[CoverResponse]],
    summary="List covers for a specific book",
    description="List all cover designs associated with a specific book.",
)
async def list_covers_for_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    covers = await service.list_covers_for_book(db, current_user["org_id"], book_id)
    return SuccessResponse(data=covers)


@router.delete(
    "/{cover_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cover (soft-delete)",
    description="Soft-delete a cover design. The record is retained but hidden from listings.",
)
async def delete_cover(
    cover_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_cover(db, current_user["org_id"], cover_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cover {cover_id} not found",
        )
    return None
