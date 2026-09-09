"""API router for Children's Books AI Story Generation & Text Analysis.

Endpoints:
  POST /specialty-books/childrens/{id}/generate-story    -- AI story generation
  POST /specialty-books/childrens/{id}/analyze-text      -- Text readability analysis
  POST /specialty-books/childrens/{id}/continuity-check  -- Character continuity check
  POST /specialty-books/childrens/{id}/auto-fix-prompts  -- Batch fix illustration prompts
  POST /specialty-books/childrens/{id}/translate         -- Bilingual translation
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import AppException
from app.database import get_db
from app.modules.specialty_books.service_childrens_ai import (
    AgeBand,
    AutoFixResponse,
    BilingualLayout,
    CharacterSheet,
    ContinuityCheckResponse,
    StoryGenerateRequest,
    StoryGenerateResponse,
    TextAnalysisResponse,
    TranslateRequest,
    TranslateResponse,
    analyze_text,
    auto_fix_prompts,
    check_continuity,
    generate_story,
    translate_book,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/specialty-books/childrens",
    tags=["Children's Books AI"],
)


# ---------------------------------------------------------------------------
# Request schemas for router-level wrappers
# ---------------------------------------------------------------------------


class AnalyzeTextRequest(BaseModel):
    """Request body for text analysis endpoint."""
    pages_text: list[str] = Field(
        default_factory=list, description="List of page texts"
    )
    age_band: AgeBand = AgeBand.PICTURE


class ContinuityCheckRequest(BaseModel):
    """Request body for continuity check endpoint."""
    character_sheets: list[CharacterSheet] = Field(default_factory=list)
    illustration_prompts: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of {page_number, prompt} dicts",
    )


class AutoFixRequest(BaseModel):
    """Request body for auto-fix prompts endpoint."""
    character_sheets: list[CharacterSheet] = Field(default_factory=list)
    illustration_prompts: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of {page_number, prompt} dicts",
    )


class TranslateBookRequest(BaseModel):
    """Request body for translation endpoint."""
    target_language: str = Field(..., min_length=2, max_length=50)
    layout_mode: BilingualLayout = BilingualLayout.SIDE_BY_SIDE
    pages_text: list[str] = Field(default_factory=list)
    age_band: AgeBand = AgeBand.PICTURE
    source_language: str = "English"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{book_id}/generate-story",
    response_model=StoryGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate an AI children's story",
)
async def generate_story_endpoint(
    book_id: UUID,
    request: StoryGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> StoryGenerateResponse:
    """Generate a full AI children's story with illustration prompts.

    Respects age-band word-count constraints and generates per-page
    illustration prompts plus character description sheets.
    """
    try:
        org_id = current_user.get("org_id")
        return await generate_story(db, book_id, org_id, request)
    except AppException:
        raise
    except Exception as e:
        logger.exception("Story generation failed for book %s", book_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Story generation failed: {e}",
        )


@router.post(
    "/{book_id}/analyze-text",
    response_model=TextAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze text readability and pacing",
)
async def analyze_text_endpoint(
    book_id: UUID,
    request: AnalyzeTextRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TextAnalysisResponse:
    """Analyze text for reading level, pacing, rhythm, and hook strength."""
    try:
        org_id = current_user.get("org_id")
        return await analyze_text(
            db,
            book_id,
            org_id,
            pages_text=request.pages_text,
            age_band=request.age_band,
        )
    except AppException:
        raise
    except Exception as e:
        logger.exception("Text analysis failed for book %s", book_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text analysis failed: {e}",
        )


@router.post(
    "/{book_id}/continuity-check",
    response_model=ContinuityCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check character continuity across pages",
)
async def continuity_check_endpoint(
    book_id: UUID,
    request: ContinuityCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ContinuityCheckResponse:
    """Analyze illustration prompts for character consistency issues."""
    try:
        org_id = current_user.get("org_id")
        return await check_continuity(
            db,
            book_id,
            org_id,
            character_sheets=request.character_sheets,
            illustration_prompts=request.illustration_prompts,
        )
    except AppException:
        raise
    except Exception as e:
        logger.exception("Continuity check failed for book %s", book_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Continuity check failed: {e}",
        )


@router.post(
    "/{book_id}/auto-fix-prompts",
    response_model=AutoFixResponse,
    status_code=status.HTTP_200_OK,
    summary="Auto-fix illustration prompts for consistency",
)
async def auto_fix_prompts_endpoint(
    book_id: UUID,
    request: AutoFixRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> AutoFixResponse:
    """Batch-update all illustration prompts to match character rules."""
    try:
        org_id = current_user.get("org_id")
        return await auto_fix_prompts(
            db,
            book_id,
            org_id,
            character_sheets=request.character_sheets,
            illustration_prompts=request.illustration_prompts,
        )
    except AppException:
        raise
    except Exception as e:
        logger.exception("Auto-fix prompts failed for book %s", book_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-fix prompts failed: {e}",
        )


@router.post(
    "/{book_id}/translate",
    response_model=TranslateResponse,
    status_code=status.HTTP_200_OK,
    summary="Translate book to another language",
)
async def translate_book_endpoint(
    book_id: UUID,
    request: TranslateBookRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TranslateResponse:
    """AI translation with cultural adaptation and reading-level validation."""
    try:
        org_id = current_user.get("org_id")
        translate_req = TranslateRequest(
            target_language=request.target_language,
            layout_mode=request.layout_mode,
        )
        return await translate_book(
            db,
            book_id,
            org_id,
            request=translate_req,
            pages_text=request.pages_text,
            age_band=request.age_band,
            source_language=request.source_language,
        )
    except AppException:
        raise
    except Exception as e:
        logger.exception("Translation failed for book %s", book_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {e}",
        )
