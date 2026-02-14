"""Cover Design Studio service layer.

Orchestrates cover generation, template management, and competitor analysis.
"""
from __future__ import annotations

import logging
from datetime import UTC
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
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

    except (KeyError, ValueError, TypeError, RuntimeError, OSError) as exc:
        logger.exception("Cover generation failed for cover %s: %s", cover.id, exc)
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
        raise AppException(
            status_code=404,
            code="COVER_NOT_FOUND",
            message=f"Cover {cover_id} not found",
        )

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
) -> CoverResponse:
    """Return a single cover by ID."""
    stmt = select(Cover).where(
        Cover.id == cover_id,
        Cover.org_id == org_id,
        Cover.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    cover = result.scalar_one_or_none()
    if cover is None:
        raise AppException(
            status_code=404,
            code="COVER_NOT_FOUND",
            message=f"Cover {cover_id} not found",
        )
    return _cover_to_response(cover)


async def delete_cover(
    db: AsyncSession,
    org_id: UUID,
    cover_id: UUID,
) -> bool:
    """Soft-delete a cover. Returns True if found and deleted."""
    from datetime import datetime

    stmt = select(Cover).where(
        Cover.id == cover_id,
        Cover.org_id == org_id,
        Cover.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    cover = result.scalar_one_or_none()
    if cover is None:
        raise AppException(
            status_code=404,
            code="COVER_NOT_FOUND",
            message=f"Cover {cover_id} not found",
        )

    cover.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


# Additional service methods for router endpoints
async def list_covers(db, org_id, project_id=None, format_filter=None, sort_by="created_at", sort_dir="desc", limit=50, offset=0):
    from sqlalchemy import desc as sql_desc, asc as sql_asc
    stmt = select(Cover).where(Cover.org_id == org_id, Cover.deleted_at.is_(None))
    if project_id:
        stmt = stmt.where(Cover.book_id == project_id)
    order_col = getattr(Cover, sort_by, Cover.created_at)
    stmt = stmt.order_by(sql_desc(order_col) if sort_dir == "desc" else sql_asc(order_col))
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return [_cover_to_response(c) for c in result.scalars().all()]

async def update_cover(db, org_id, cover_id, **updates):
    cover = await get_cover_by_id(db, org_id, cover_id)
    stmt = select(Cover).where(Cover.id == cover_id, Cover.org_id == org_id, Cover.deleted_at.is_(None))
    result = await db.execute(stmt)
    cover_orm = result.scalar_one_or_none()
    if cover_orm:
        for key, value in updates.items():
            if hasattr(cover_orm, key):
                setattr(cover_orm, key, value)
        await db.flush()
        await db.refresh(cover_orm)
    return _cover_to_response(cover_orm)


async def update_editor_state(db, org_id, cover_id, editor_state):
    stmt = select(Cover).where(Cover.id == cover_id, Cover.org_id == org_id, Cover.deleted_at.is_(None))
    result = await db.execute(stmt)
    cover = result.scalar_one_or_none()
    if not cover:
        raise AppException(status_code=404, code="COVER_NOT_FOUND", message=f"Cover {cover_id} not found")
    if cover.metadata_json is None:
        cover.metadata_json = {}
    cover.metadata_json["editor_state"] = editor_state
    await db.flush()
    await db.refresh(cover)
    return _cover_to_response(cover)


async def export_cover(db, org_id, cover_id, export_format, dpi, include_bleed, color_profile):
    stmt = select(Cover).where(Cover.id == cover_id, Cover.org_id == org_id, Cover.deleted_at.is_(None))
    result = await db.execute(stmt)
    cover = result.scalar_one_or_none()
    if not cover:
        raise AppException(status_code=404, code="COVER_NOT_FOUND", message=f"Cover {cover_id} not found")
    export_url = f"{cover.image_url}?format={export_format}&dpi={dpi}"
    return {
        "export_url": export_url,
        "format": export_format,
        "file_size_bytes": 1024000,
        "dimensions": CoverDimensions(width_px=cover.width_px or 2560, height_px=cover.height_px or 1600, dpi=dpi, bleed_px=cover.bleed_px if include_bleed else 0),
        "created_at": datetime.now(UTC),
    }


async def create_ab_test(db, org_id, name, description, cover_a_id, cover_b_id, target_audience, duration_days, public_url_enabled):
    import secrets
    from app.modules.cover_design.models import CoverABTest
    stmt = select(Cover).where(Cover.id.in_([cover_a_id, cover_b_id]), Cover.org_id == org_id, Cover.deleted_at.is_(None))
    result = await db.execute(stmt)
    if len(result.scalars().all()) != 2:
        raise AppException(status_code=404, code="COVER_NOT_FOUND", message="One or both covers not found")
    public_url = f"ab-test-{secrets.token_urlsafe(16)}" if public_url_enabled else None
    ab_test = CoverABTest(org_id=org_id, name=name, description=description, cover_a_id=cover_a_id, cover_b_id=cover_b_id, status="active", public_url=public_url, target_audience=target_audience, duration_days=duration_days, started_at=datetime.now(UTC))
    db.add(ab_test)
    await db.flush()
    await db.refresh(ab_test)
    return {"id": ab_test.id, "org_id": ab_test.org_id, "name": ab_test.name, "description": ab_test.description, "cover_a_id": ab_test.cover_a_id, "cover_b_id": ab_test.cover_b_id, "status": ab_test.status, "votes_a": ab_test.votes_a, "votes_b": ab_test.votes_b, "public_url": ab_test.public_url, "target_audience": ab_test.target_audience, "duration_days": ab_test.duration_days, "started_at": ab_test.started_at, "ended_at": ab_test.ended_at, "created_at": ab_test.created_at, "updated_at": ab_test.updated_at}


async def list_ab_tests(db, org_id):
    from app.modules.cover_design.models import CoverABTest
    stmt = select(CoverABTest).where(CoverABTest.org_id == org_id, CoverABTest.deleted_at.is_(None)).order_by(CoverABTest.created_at.desc())
    result = await db.execute(stmt)
    tests = result.scalars().all()
    return [{"id": t.id, "org_id": t.org_id, "name": t.name, "description": t.description, "cover_a_id": t.cover_a_id, "cover_b_id": t.cover_b_id, "status": t.status, "votes_a": t.votes_a, "votes_b": t.votes_b, "public_url": t.public_url, "target_audience": t.target_audience, "duration_days": t.duration_days, "started_at": t.started_at, "ended_at": t.ended_at, "created_at": t.created_at, "updated_at": t.updated_at} for t in tests]


async def get_ab_test(db, test_id, org_id=None):
    from app.modules.cover_design.models import CoverABTest
    stmt = select(CoverABTest).where(CoverABTest.id == test_id, CoverABTest.deleted_at.is_(None))
    if org_id:
        stmt = stmt.where(CoverABTest.org_id == org_id)
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if not test:
        raise AppException(status_code=404, code="AB_TEST_NOT_FOUND", message=f"A/B test {test_id} not found")
    return {"id": test.id, "org_id": test.org_id, "name": test.name, "description": test.description, "cover_a_id": test.cover_a_id, "cover_b_id": test.cover_b_id, "status": test.status, "votes_a": test.votes_a, "votes_b": test.votes_b, "public_url": test.public_url, "target_audience": test.target_audience, "duration_days": test.duration_days, "started_at": test.started_at, "ended_at": test.ended_at, "created_at": test.created_at, "updated_at": test.updated_at}


async def vote_on_ab_test(db, test_id, choice, voter_fingerprint=None):
    from app.modules.cover_design.models import CoverABTest
    stmt = select(CoverABTest).where(CoverABTest.id == test_id, CoverABTest.deleted_at.is_(None))
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if not test:
        raise AppException(status_code=404, code="AB_TEST_NOT_FOUND", message=f"A/B test {test_id} not found")
    if test.status != "active":
        raise AppException(status_code=400, code="AB_TEST_NOT_ACTIVE", message="This A/B test is not active")
    if choice == "a":
        test.votes_a += 1
    elif choice == "b":
        test.votes_b += 1
    else:
        raise AppException(status_code=400, code="INVALID_CHOICE", message="Choice must be a or b")
    await db.flush()
    await db.refresh(test)
    return {"success": True, "message": "Vote recorded successfully", "current_votes_a": test.votes_a, "current_votes_b": test.votes_b}


async def end_ab_test(db, org_id, test_id, winner, notes):
    from app.modules.cover_design.models import CoverABTest
    stmt = select(CoverABTest).where(CoverABTest.id == test_id, CoverABTest.org_id == org_id, CoverABTest.deleted_at.is_(None))
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if not test:
        raise AppException(status_code=404, code="AB_TEST_NOT_FOUND", message=f"A/B test {test_id} not found")
    test.status = "ended"
    test.ended_at = datetime.now(UTC)
    if test.metadata_json is None:
        test.metadata_json = {}
    test.metadata_json["winner"] = winner
    test.metadata_json["notes"] = notes
    await db.flush()
    await db.refresh(test)
    return {"id": test.id, "org_id": test.org_id, "name": test.name, "description": test.description, "cover_a_id": test.cover_a_id, "cover_b_id": test.cover_b_id, "status": test.status, "votes_a": test.votes_a, "votes_b": test.votes_b, "public_url": test.public_url, "target_audience": test.target_audience, "duration_days": test.duration_days, "started_at": test.started_at, "ended_at": test.ended_at, "created_at": test.created_at, "updated_at": test.updated_at}


_generation_jobs = {}


async def start_generation_job(db, org_id, request):
    import secrets
    job_id = f"job-{secrets.token_urlsafe(16)}"
    _generation_jobs[job_id] = {"job_id": job_id, "status": "pending", "progress": 0, "cover_id": None, "error_message": None, "created_at": datetime.now(UTC), "completed_at": None}
    return job_id


async def get_generation_job_status(job_id):
    if job_id not in _generation_jobs:
        raise AppException(status_code=404, code="JOB_NOT_FOUND", message=f"Job {job_id} not found")
    return _generation_jobs[job_id]
