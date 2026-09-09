"""Series Branding Manager.

Manages multi-volume book series with consistent branding, naming
conventions, and theme coherence across volumes.

Blueprint refs: 12.1, 4.7
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty.models.shared import BookBundle, BookSeries

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SeriesInfo:
    """Lightweight representation of a book series."""

    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    book_type: str
    naming_format: str | None
    branding_config: dict[str, Any] | None
    branding_locked: bool
    volume_count: int
    volumes: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CoherenceResult:
    """Result of a series coherence check."""

    score: float
    issues: list[dict[str, str]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _row_to_series(row: BookSeries, volumes: list[dict[str, Any]] | None = None) -> SeriesInfo:
    return SeriesInfo(
        id=row.id,
        org_id=row.org_id,
        name=row.name,
        book_type=row.book_type,
        naming_format=row.naming_format,
        branding_config=row.branding_config,
        branding_locked=row.branding_locked,
        volume_count=row.volume_count,
        volumes=volumes or [],
    )


# Default branding configuration applied when creating a new series.
DEFAULT_BRANDING_CONFIG: dict[str, Any] = {
    "title_font": None,
    "title_position": "top_center",
    "author_position": "bottom_center",
    "volume_badge": {
        "enabled": True,
        "position": "top_right",
        "style": "circle",
    },
    "spine_layout": {
        "title_orientation": "horizontal",
        "author_orientation": "horizontal",
        "volume_number": True,
    },
    "color_scheme": None,
    "cover_template_id": None,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def create_series(
    db: AsyncSession,
    org_id: uuid.UUID,
    name: str,
    book_type: str,
    naming_format: str | None = None,
    branding_config: dict[str, Any] | None = None,
) -> SeriesInfo:
    """Create a new book series.

    Parameters
    ----------
    db:
        Async database session.
    org_id:
        Tenant / organisation identifier.
    name:
        Human-readable series name (e.g. "Animal Coloring Adventures").
    book_type:
        One of ``childrens``, ``coloring``, ``puzzle``.
    naming_format:
        Title template with placeholders, e.g.
        ``"{series_name} Vol. {volume} - {theme}"``.
    branding_config:
        Cover & spine branding settings.  Falls back to
        ``DEFAULT_BRANDING_CONFIG`` when ``None``.
    """
    config = branding_config or dict(DEFAULT_BRANDING_CONFIG)

    row = BookSeries(
        org_id=org_id,
        name=name,
        book_type=book_type,
        naming_format=naming_format,
        branding_config=config,
        branding_locked=False,
        volume_count=0,
    )
    db.add(row)
    await db.flush()

    return _row_to_series(row)


async def get_series(
    db: AsyncSession,
    series_id: uuid.UUID,
) -> SeriesInfo:
    """Return a series with its associated volumes (from bundles).

    Raises ``ValueError`` if the series does not exist.
    """
    stmt = select(BookSeries).where(BookSeries.id == series_id)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise ValueError(f"Series {series_id} not found")

    # Gather volumes from bundles linked to this series.
    bundle_stmt = select(BookBundle).where(BookBundle.series_id == series_id).order_by(BookBundle.created_at.asc())
    bundle_result = await db.execute(bundle_stmt)
    volumes: list[dict[str, Any]] = []
    for bundle in bundle_result.scalars().all():
        volumes.append(
            {
                "bundle_id": str(bundle.id),
                "title": bundle.title,
                "volume_ids": bundle.volume_ids,
                "total_pages": bundle.total_pages,
            }
        )

    return _row_to_series(row, volumes=volumes)


async def lock_branding(
    db: AsyncSession,
    series_id: uuid.UUID,
) -> SeriesInfo:
    """Lock branding configuration so new volumes inherit the template.

    Once locked the following are fixed across all subsequent volumes:
    * Title font and position
    * Author name position
    * Volume badge style and position
    * Spine layout
    """
    stmt = update(BookSeries).where(BookSeries.id == series_id).values(branding_locked=True).returning(BookSeries)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise ValueError(f"Series {series_id} not found")
    await db.flush()
    return _row_to_series(row)


async def check_coherence(
    db: AsyncSession,
    series_id: uuid.UUID,
) -> CoherenceResult:
    """Evaluate theme and style consistency across all volumes in a series.

    Returns a score (0-100) and a list of identified issues such as:
    * Inconsistent illustration style between volumes
    * Mismatched color palettes
    * Naming format deviations
    * Branding drift (unlocked elements changed across volumes)

    NOTE: In a production implementation this would analyse actual cover
    images and metadata.  The current version performs structural checks
    against the branding_config and naming_format fields.
    """
    series = await get_series(db, series_id)
    issues: list[dict[str, str]] = []
    score = 100.0

    # --- Check: series must have at least 2 volumes for meaningful coherence ---
    if series.volume_count < 2:
        return CoherenceResult(score=score, issues=[])

    # --- Check: branding should be locked ---
    if not series.branding_locked:
        issues.append(
            {
                "field": "branding_locked",
                "severity": "warning",
                "message": "Series branding is not locked. Cover elements may drift between volumes.",
            }
        )
        score -= 10

    # --- Check: naming format is defined ---
    if not series.naming_format:
        issues.append(
            {
                "field": "naming_format",
                "severity": "warning",
                "message": "No naming format defined. Volume titles may be inconsistent.",
            }
        )
        score -= 10

    # --- Check: branding config completeness ---
    config = series.branding_config or {}
    required_keys = ["title_font", "title_position", "author_position", "volume_badge", "spine_layout"]
    for key in required_keys:
        if key not in config or config[key] is None:
            issues.append(
                {
                    "field": f"branding_config.{key}",
                    "severity": "info",
                    "message": f"Branding element '{key}' is not configured.",
                }
            )
            score -= 5

    # --- Check: spine layout completeness ---
    spine = config.get("spine_layout") or {}
    if not spine.get("volume_number"):
        issues.append(
            {
                "field": "branding_config.spine_layout.volume_number",
                "severity": "warning",
                "message": "Volume number not shown on spine. Readers cannot identify volumes on shelf.",
            }
        )
        score -= 5

    # --- Check: volume badge enabled ---
    badge = config.get("volume_badge") or {}
    if not badge.get("enabled"):
        issues.append(
            {
                "field": "branding_config.volume_badge",
                "severity": "info",
                "message": "Volume badge is disabled. Consider enabling for series recognition.",
            }
        )
        score -= 5

    score = max(0.0, min(100.0, score))
    return CoherenceResult(score=score, issues=issues)


async def add_volume(
    db: AsyncSession,
    series_id: uuid.UUID,
    book_id: uuid.UUID,
) -> SeriesInfo:
    """Add a book to a series as the next volume.

    Increments ``volume_count`` on the series record and, if branding is
    locked, the caller should apply the locked template to the new book's
    cover.
    """
    stmt = select(BookSeries).where(BookSeries.id == series_id)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise ValueError(f"Series {series_id} not found")

    row.volume_count = (row.volume_count or 0) + 1
    await db.flush()
    return _row_to_series(row)
