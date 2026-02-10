"""Cover Design Studio service layer.

Orchestrates cover generation, template management, and competitor analysis.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cover_design.analyzer import analyze_competitor_covers
from app.modules.cover_design.generator import (
    build_cover_prompt,
    generate_cover_image,
    generate_variations,
)
from app.modules.cover_design.models import Cover
from app.modules.cover_design.schemas import (
    CompetitorAnalysisResponse,
    CompetitorCoverAnalysisRequest,
    CoverDimensions,
    CoverGenerateRequest,
    CoverGenre,
    CoverPlatform,
    CoverResponse,
    CoverStatus,
    CoverTemplateResponse,
    CoverVariationRequest,
)
from app.modules.cover_design.templates import (
    get_all_templates,
    get_dimensions_for_platform,
    get_templates_by_genre,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cover_to_response(cover: Cover) -> CoverResponse:
    """Map a Cover ORM object to the CoverResponse schema."""
    dims = None
    if cover.width_px and cover.height_px:
        dims = CoverDimensions(
            width_px=cover.width_px,
            height_px=cover.height_px,
            dpi=cover.dpi,
            bleed_px=cover.bleed_px,
        )

    return CoverResponse(
        id=cover.id,
        org_id=cover.org_id,
        book_id=cover.book_id,
        title=cover.title,
        subtitle=cover.subtitle,
        author_name=cover.author_name,
        genre=CoverGenre(cover.genre),
        status=CoverStatus(cover.status),
        image_url=cover.image_url,
        thumbnail_url=cover.thumbnail_url,
        prompt_used=cover.prompt_used,
        dimensions=dims,
        platform=CoverPlatform(cover.platform),
        metadata=cover.metadata_json or {},
        created_at=cover.created_at,
        updated_at=cover.updated_at,
    )


# ---------------------------------------------------------------------------
# Cover generation
# ---------------------------------------------------------------------------


async def generate_cover(
    db: AsyncSession,
    org_id: UUID,
    request: CoverGenerateRequest,
) -> CoverResponse:
    """Generate a new AI cover and persist it."""

    # 1. Create a pending cover record
    cover = Cover(
        org_id=org_id,
        book_id=request.book_id,
        title=request.title,
        subtitle=request.subtitle,
        author_name=request.author_name,
        genre=request.genre.value,
        status=CoverStatus.GENERATING.value,
        platform=request.platform.value,
        metadata_json={
            "mood": request.mood,
            "style_keywords": request.style_keywords,
            "color_palette": request.color_palette,
            "additional_instructions": request.additional_instructions,
        },
    )
    db.add(cover)
    await db.flush()
    await db.refresh(cover)

    # 2. Build prompt
    prompt = build_cover_prompt(
        title=request.title,
        subtitle=request.subtitle,
        author_name=request.author_name,
        genre=request.genre,
        mood=request.mood,
        style_keywords=request.style_keywords,
        color_palette=request.color_palette,
        additional_instructions=request.additional_instructions,
    )

    # 3. Generate image
    try:
        dimensions = get_dimensions_for_platform(request.platform)
        result = await generate_cover_image(prompt, dimensions, request.platform)

        cover.image_url = result["image_url"]
        cover.thumbnail_url = result.get("thumbnail_url")
        cover.prompt_used = result.get("prompt_used", prompt)
        cover.width_px = result.get("width_px", dimensions.width_px)
        cover.height_px = result.get("height_px", dimensions.height_px)
        cover.dpi = result.get("dpi", dimensions.dpi)
        cover.status = CoverStatus.COMPLETED.value

    except Exception:
        logger.exception("Cover generation failed for cover %s", cover.id)
        cover.status = CoverStatus.FAILED.value

    await db.flush()
    await db.refresh(cover)

    return _cover_to_response(cover)


# ---------------------------------------------------------------------------
# Variations
# ---------------------------------------------------------------------------


async def create_variations(
    db: AsyncSession,
    org_id: UUID,
    cover_id: UUID,
    request: CoverVariationRequest,
) -> list[CoverResponse]:
    """Generate variations of an existing cover."""

    # Fetch the original cover
    stmt = select(Cover).where(Cover.id == cover_id, Cover.org_id == org_id, Cover.deleted_at.is_(None))
    result = await db.execute(stmt)
    original = result.scalar_one_or_none()
    if original is None:
        raise ValueError(f"Cover {cover_id} not found")

    prompt = original.prompt_used or build_cover_prompt(
        title=original.title,
        subtitle=original.subtitle,
        author_name=original.author_name,
        genre=CoverGenre(original.genre),
    )

    variation_results = await generate_variations(
        original_prompt=prompt,
        variation_type=request.variation_type,
        count=request.variation_count,
        instructions=request.instructions,
    )

    covers: list[CoverResponse] = []
    for vr in variation_results:
        variation = Cover(
            org_id=org_id,
            book_id=original.book_id,
            title=original.title,
            subtitle=original.subtitle,
            author_name=original.author_name,
            genre=original.genre,
            status=CoverStatus.COMPLETED.value,
            platform=original.platform,
            image_url=vr["image_url"],
            thumbnail_url=vr.get("thumbnail_url"),
            prompt_used=vr.get("prompt_used"),
            width_px=vr.get("width_px"),
            height_px=vr.get("height_px"),
            dpi=vr.get("dpi", 300),
            parent_cover_id=original.id,
            metadata_json={
                "variation_type": vr.get("variation_type"),
                "variation_index": vr.get("variation_index"),
            },
        )
        db.add(variation)
        await db.flush()
        await db.refresh(variation)
        covers.append(_cover_to_response(variation))

    return covers


# ---------------------------------------------------------------------------
# Template listing
# ---------------------------------------------------------------------------


async def list_templates(
    genre: CoverGenre | None = None,
) -> list[CoverTemplateResponse]:
    """Return available cover templates, optionally filtered by genre."""
    if genre:
        templates = get_templates_by_genre(genre)
    else:
        templates = get_all_templates()

    return [
        CoverTemplateResponse(
            id=t.id,
            name=t.name,
            genre=t.genre,
            description=t.description,
            thumbnail_url=t.thumbnail_url,
            dimensions=t.dimensions,
            font_recommendations=t.font_recommendations,
            layout_guidance=t.layout_guidance,
            tags=t.tags,
        )
        for t in templates
    ]


# ---------------------------------------------------------------------------
# Competitor analysis
# ---------------------------------------------------------------------------


async def analyze_competitors(
    request: CompetitorCoverAnalysisRequest,
) -> CompetitorAnalysisResponse:
    """Analyse competitor covers in a niche."""
    return await analyze_competitor_covers(
        genre=request.genre,
        niche_keywords=request.niche_keywords,
        image_urls=request.competitor_image_urls or None,
        max_results=request.max_results,
    )


# ---------------------------------------------------------------------------
# Cover queries
# ---------------------------------------------------------------------------


async def list_covers_for_book(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
) -> list[CoverResponse]:
    """Return all covers associated with a specific book."""
    stmt = (
        select(Cover)
        .where(
            Cover.org_id == org_id,
            Cover.book_id == book_id,
            Cover.deleted_at.is_(None),
        )
        .order_by(Cover.created_at.desc())
    )
    result = await db.execute(stmt)
    covers = result.scalars().all()
    return [_cover_to_response(c) for c in covers]


async def get_cover_by_id(
    db: AsyncSession,
    org_id: UUID,
    cover_id: UUID,
) -> CoverResponse | None:
    """Return a single cover by ID."""
    stmt = select(Cover).where(
        Cover.id == cover_id,
        Cover.org_id == org_id,
        Cover.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    cover = result.scalar_one_or_none()
    if cover is None:
        return None
    return _cover_to_response(cover)


async def delete_cover(
    db: AsyncSession,
    org_id: UUID,
    cover_id: UUID,
) -> bool:
    """Soft-delete a cover. Returns True if found and deleted."""
    from datetime import datetime, timezone

    stmt = select(Cover).where(
        Cover.id == cover_id,
        Cover.org_id == org_id,
        Cover.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    cover = result.scalar_one_or_none()
    if cover is None:
        return False

    cover.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return True
