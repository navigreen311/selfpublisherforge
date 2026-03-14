"""Art Style Cloning service layer."""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundError
from app.database import TenantModel
from app.modules.specialty.models.style_clone import StyleCloneProfile

logger = logging.getLogger(__name__)


def _profile_to_dict(profile: StyleCloneProfile) -> dict[str, Any]:
    return {
        "id": str(profile.id),
        "org_id": str(profile.org_id),
        "name": profile.name,
        "description": profile.description,
        "reference_image_urls": profile.reference_image_urls or [],
        "reference_count": profile.reference_count,
        "style_attributes": profile.style_attributes or {},
        "style_prompt": profile.style_prompt,
        "style_embedding": profile.style_embedding,
        "test_image_urls": profile.test_image_urls or [],
        "drift_score": profile.drift_score,
        "last_drift_check": profile.last_drift_check,
        "book_type": profile.book_type,
        "is_active": profile.is_active,
        "is_default": profile.is_default,
        "times_used": profile.times_used,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


async def _get_profile_or_404(
    db: AsyncSession, org_id: UUID, profile_id: UUID
) -> StyleCloneProfile:
    stmt = select(StyleCloneProfile).where(
        StyleCloneProfile.id == profile_id,
        StyleCloneProfile.org_id == org_id,
        StyleCloneProfile.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError("StyleCloneProfile", f"Style clone profile {profile_id} not found")
    return profile


async def list_profiles(
    db: AsyncSession,
    org_id: UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    book_type: str | None = None,
    search: str | None = None,
    active_only: bool = True,
) -> dict[str, Any]:
    """List style clone profiles with pagination."""
    stmt = select(StyleCloneProfile).where(
        StyleCloneProfile.org_id == org_id,
        StyleCloneProfile.deleted_at.is_(None),
    )
    count_stmt = select(func.count()).select_from(StyleCloneProfile).where(
        StyleCloneProfile.org_id == org_id,
        StyleCloneProfile.deleted_at.is_(None),
    )

    if active_only:
        stmt = stmt.where(StyleCloneProfile.is_active.is_(True))
        count_stmt = count_stmt.where(StyleCloneProfile.is_active.is_(True))
    if book_type:
        stmt = stmt.where(StyleCloneProfile.book_type == book_type)
        count_stmt = count_stmt.where(StyleCloneProfile.book_type == book_type)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(StyleCloneProfile.name.ilike(pattern))
        count_stmt = count_stmt.where(StyleCloneProfile.name.ilike(pattern))

    total_result = await db.execute(count_stmt)
    total_count = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(StyleCloneProfile.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    profiles = result.scalars().all()

    return {
        "items": [_profile_to_dict(p) for p in profiles],
        "total_count": total_count,
        "has_more": (offset + page_size) < total_count,
        "next_cursor": str(page + 1) if (offset + page_size) < total_count else None,
    }


async def create_profile(
    db: AsyncSession,
    org_id: UUID,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Create a new style clone profile."""
    ref_urls = payload.get("reference_image_urls", [])
    profile = StyleCloneProfile(
        org_id=org_id,
        name=payload["name"],
        description=payload.get("description"),
        reference_image_urls=ref_urls,
        reference_count=len(ref_urls) if ref_urls else 0,
        book_type=payload.get("book_type"),
        style_attributes=payload.get("style_attributes"),
        style_prompt=payload.get("style_prompt"),
    )
    db.add(profile)
    await db.flush()
    return _profile_to_dict(profile)


async def get_profile(db: AsyncSession, org_id: UUID, profile_id: UUID) -> dict[str, Any]:
    """Get style clone profile detail."""
    profile = await _get_profile_or_404(db, org_id, profile_id)
    return _profile_to_dict(profile)


async def update_profile(
    db: AsyncSession, org_id: UUID, profile_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """Update a style clone profile."""
    profile = await _get_profile_or_404(db, org_id, profile_id)

    updatable_fields = [
        "name", "description", "reference_image_urls", "book_type",
        "style_attributes", "style_prompt", "is_active",
    ]
    for field in updatable_fields:
        if field in payload:
            setattr(profile, field, payload[field])

    if "reference_image_urls" in payload:
        urls = payload["reference_image_urls"]
        profile.reference_count = len(urls) if urls else 0

    await db.flush()
    return _profile_to_dict(profile)


async def delete_profile(db: AsyncSession, org_id: UUID, profile_id: UUID) -> bool:
    """Soft-delete a style clone profile."""
    try:
        profile = await _get_profile_or_404(db, org_id, profile_id)
    except NotFoundError:
        return False
    profile.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def analyze_style(
    db: AsyncSession,
    org_id: UUID,
    profile_id: UUID,
) -> dict[str, Any]:
    """Analyze reference images and extract style attributes (stub).

    In production this would use a vision model to analyze line weight,
    color palette, shading technique, perspective, texture, and composition
    patterns, then update the profile.
    """
    profile = await _get_profile_or_404(db, org_id, profile_id)

    style_attributes = {
        "line_weight": "medium",
        "color_saturation": "high",
        "shading_technique": "cross-hatching",
        "perspective": "three-quarter",
        "palette_dominant": ["#2C3E50", "#E74C3C", "#ECF0F1"],
        "texture": "slightly rough",
        "composition_style": "dynamic",
    }
    style_prompt = (
        "In a dynamic art style with medium line weight, high color saturation, "
        "cross-hatching shading, three-quarter perspective, slightly rough texture, "
        "using a palette of deep blue-grey, vibrant red, and light grey."
    )

    profile.style_attributes = style_attributes
    profile.style_prompt = style_prompt
    await db.flush()

    return {
        "profile_id": str(profile_id),
        "style_attributes": style_attributes,
        "style_prompt": style_prompt,
        "confidence": 0.87,
    }


async def test_generate(
    db: AsyncSession,
    org_id: UUID,
    profile_id: UUID,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Generate test images using cloned style (stub).

    In production this would call the image generation service with the
    profile's style_prompt prepended to the user's prompt.
    """
    profile = await _get_profile_or_404(db, org_id, profile_id)
    count = payload.get("count", 4)

    test_urls = [
        f"https://placeholder.com/style-test-{i}.png"
        for i in range(count)
    ]
    profile.test_image_urls = test_urls
    await db.flush()

    return {
        "profile_id": str(profile_id),
        "test_images": test_urls,
    }


async def check_drift(
    db: AsyncSession,
    org_id: UUID,
    profile_id: UUID,
) -> dict[str, Any]:
    """Check for style drift (stub).

    Score: 0 = perfect match, 1 = completely different.
    In production this would compare recent generations against reference
    images using a vision model.
    """
    profile = await _get_profile_or_404(db, org_id, profile_id)

    drift_score = 0.12
    profile.drift_score = drift_score
    profile.last_drift_check = datetime.now(UTC).isoformat()
    await db.flush()

    return {
        "profile_id": str(profile_id),
        "drift_score": drift_score,
        "drift_level": "low",
        "details": {
            "color_drift": 0.08,
            "line_weight_drift": 0.15,
            "composition_drift": 0.13,
        },
        "recommendation": "Style is consistent. No action needed.",
    }


async def set_default(db: AsyncSession, org_id: UUID, profile_id: UUID) -> dict[str, Any]:
    """Set a profile as the default for its book type.

    Unsets any other default profile for the same book_type within the org.
    """
    profile = await _get_profile_or_404(db, org_id, profile_id)

    if profile.book_type:
        stmt = (
            update(StyleCloneProfile)
            .where(
                StyleCloneProfile.org_id == org_id,
                StyleCloneProfile.book_type == profile.book_type,
                StyleCloneProfile.is_default.is_(True),
                StyleCloneProfile.id != profile_id,
                StyleCloneProfile.deleted_at.is_(None),
            )
            .values(is_default=False)
        )
        await db.execute(stmt)
    else:
        stmt = (
            update(StyleCloneProfile)
            .where(
                StyleCloneProfile.org_id == org_id,
                StyleCloneProfile.book_type.is_(None),
                StyleCloneProfile.is_default.is_(True),
                StyleCloneProfile.id != profile_id,
                StyleCloneProfile.deleted_at.is_(None),
            )
            .values(is_default=False)
        )
        await db.execute(stmt)

    profile.is_default = True
    await db.flush()

    return _profile_to_dict(profile)
