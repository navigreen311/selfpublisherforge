"""Bundle / Box Set Creator.

Combines multiple volumes from a series into a single "Complete Collection"
book with section dividers, a combined table of contents, and merged answer
keys (for puzzle books).

Blueprint refs: 12.3
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty.models.shared import BookBundle, BookSeries

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BundleInfo:
    """Lightweight representation of a book bundle."""

    id: uuid.UUID
    org_id: uuid.UUID
    title: str
    book_type: str
    volume_ids: list[str]
    series_id: uuid.UUID | None
    config: dict[str, Any] | None
    total_pages: int | None


@dataclass
class BundleContent:
    """Generated content for a bundle."""

    bundle_id: uuid.UUID
    toc: list[dict[str, Any]]
    sections: list[dict[str, Any]]
    answer_keys: list[dict[str, Any]]
    total_pages: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_bundle(row: BookBundle) -> BundleInfo:
    return BundleInfo(
        id=row.id,
        org_id=row.org_id,
        title=row.title,
        book_type=row.book_type,
        volume_ids=row.volume_ids or [],
        series_id=row.series_id,
        config=row.config,
        total_pages=row.total_pages,
    )


# Default configuration for a new bundle.
DEFAULT_BUNDLE_CONFIG: dict[str, Any] = {
    "section_dividers": True,
    "combined_toc": True,
    "combined_answer_keys": True,
    "divider_style": "full_page",
    "page_numbering": "continuous",
    "include_volume_titles": True,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def create_bundle(
    db: AsyncSession,
    org_id: uuid.UUID,
    title: str,
    volume_ids: list[uuid.UUID],
    series_id: uuid.UUID | None = None,
) -> BundleInfo:
    """Create a new bundle (box set) from a list of volume book IDs.

    Parameters
    ----------
    db:
        Async database session.
    org_id:
        Tenant identifier.
    title:
        Bundle title, e.g. "Animal Coloring Adventures: Complete Collection".
    volume_ids:
        Ordered list of book UUIDs to include.
    series_id:
        Optional link to a ``BookSeries`` record.
    """
    # Resolve book_type from the series if available.
    book_type = "coloring"  # default fallback
    if series_id:
        stmt = select(BookSeries).where(BookSeries.id == series_id)
        result = await db.execute(stmt)
        series = result.scalar_one_or_none()
        if series:
            book_type = series.book_type

    row = BookBundle(
        org_id=org_id,
        title=title,
        book_type=book_type,
        volume_ids=[str(vid) for vid in volume_ids],
        series_id=series_id,
        config=dict(DEFAULT_BUNDLE_CONFIG),
        total_pages=None,
    )
    db.add(row)
    await db.flush()

    return _row_to_bundle(row)


async def generate_bundle_content(
    db: AsyncSession,
    bundle_id: uuid.UUID,
) -> BundleContent:
    """Generate combined content for a bundle.

    This produces:
    * **Combined TOC** -- a master table of contents spanning all volumes.
    * **Section dividers** -- full-page dividers between each volume.
    * **Combined answer keys** -- merged answer key section (puzzle books).

    In production, actual page content is fetched from the per-book-type
    tables.  The current implementation generates the structural skeleton.
    """
    stmt = select(BookBundle).where(BookBundle.id == bundle_id)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise ValueError(f"Bundle {bundle_id} not found")

    config = row.config or DEFAULT_BUNDLE_CONFIG
    volume_ids = row.volume_ids or []

    # --- Build TOC entries ---
    toc: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    answer_keys: list[dict[str, Any]] = []
    running_page = 1

    # Title page + TOC pages (estimate 2 pages)
    running_page += 2

    for idx, vol_id in enumerate(volume_ids, start=1):
        vol_label = f"Volume {idx}"

        # Section divider (1 page)
        if config.get("section_dividers"):
            sections.append(
                {
                    "type": "divider",
                    "volume_index": idx,
                    "volume_id": vol_id,
                    "title": vol_label,
                    "page_number": running_page,
                }
            )
            running_page += 1

        # Estimate volume content at 30 pages (placeholder -- real
        # implementation queries actual book page counts).
        estimated_volume_pages = 30

        toc.append(
            {
                "volume_index": idx,
                "volume_id": vol_id,
                "title": vol_label,
                "start_page": running_page,
                "end_page": running_page + estimated_volume_pages - 1,
            }
        )

        sections.append(
            {
                "type": "content",
                "volume_index": idx,
                "volume_id": vol_id,
                "start_page": running_page,
                "page_count": estimated_volume_pages,
            }
        )
        running_page += estimated_volume_pages

    # Combined answer keys section (for puzzle books).
    if config.get("combined_answer_keys") and row.book_type == "puzzle":
        for idx, vol_id in enumerate(volume_ids, start=1):
            answer_keys.append(
                {
                    "volume_index": idx,
                    "volume_id": vol_id,
                    "start_page": running_page,
                    "page_count": 5,  # placeholder estimate
                }
            )
            running_page += 5

    total_pages = running_page - 1

    # Persist computed total page count.
    row.total_pages = total_pages
    await db.flush()

    return BundleContent(
        bundle_id=row.id,
        toc=toc,
        sections=sections,
        answer_keys=answer_keys,
        total_pages=total_pages,
    )


async def calculate_bundle_pages(
    db: AsyncSession,
    bundle_id: uuid.UUID,
) -> int:
    """Calculate and return the total page count for a bundle.

    If content has not yet been generated, a quick estimate is returned
    based on the number of volumes.
    """
    stmt = select(BookBundle).where(BookBundle.id == bundle_id)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise ValueError(f"Bundle {bundle_id} not found")

    if row.total_pages is not None:
        return row.total_pages

    # Quick estimate: title/TOC (2) + per-volume (30 content + 1 divider)
    volume_count = len(row.volume_ids or [])
    estimated = 2 + volume_count * 31
    if row.book_type == "puzzle":
        estimated += volume_count * 5  # answer keys

    return estimated
