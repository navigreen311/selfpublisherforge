"""Chrome Extension API service layer.

Handles saving extracted Amazon data, serving quick research data,
and saving clips to the Knowledge Vault.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cover_design.models import ExtractedProduct, KnowledgeClip
from app.modules.chrome_extension.schemas import (
    ClipSaveRequest,
    ClipSaveResponse,
    ExtractDataRequest,
    ExtractedDataResponse,
    QuickResearchQuery,
    QuickResearchResponse,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Save extracted Amazon data
# ---------------------------------------------------------------------------


async def save_extracted_data(
    db: AsyncSession,
    org_id: UUID,
    request: ExtractDataRequest,
) -> ExtractedDataResponse:
    """Persist Amazon product data extracted by the Chrome Extension."""
    data = request.data

    product = ExtractedProduct(
        org_id=org_id,
        asin=data.asin,
        title=data.title,
        subtitle=data.subtitle,
        author=data.author,
        price=data.price,
        currency=data.currency,
        bsr=data.bsr,
        bsr_categories=data.bsr_categories,
        categories=data.categories,
        keywords=data.keywords,
        reviews_json=data.reviews.model_dump() if data.reviews else None,
        page_url=data.page_url,
        image_url=data.image_url,
        marketplace=data.marketplace.value,
        publication_date=data.publication_date,
        page_count=data.page_count,
        language=data.language,
        dimensions=data.dimensions,
        isbn=data.isbn,
        notes=request.notes,
        tags=request.tags or [],
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)

    return ExtractedDataResponse(
        id=product.id,
        org_id=product.org_id,
        asin=product.asin,
        title=product.title,
        bsr=product.bsr,
        saved_at=product.created_at,
    )


# ---------------------------------------------------------------------------
# Quick research
# ---------------------------------------------------------------------------


async def get_quick_research(
    db: AsyncSession,
    org_id: UUID,
    query: QuickResearchQuery,
) -> QuickResearchResponse:
    """Return quick niche research data for the extension sidebar.

    In production this would aggregate data from:
    - Historical BSR tracking
    - Market intelligence module
    - Competitor analysis

    For now, returns data from our stored extractions plus some
    computed estimates.
    """
    response = QuickResearchResponse(asin=query.asin)

    if query.asin:
        # Look up stored data for this ASIN
        stmt = (
            select(ExtractedProduct)
            .where(
                ExtractedProduct.org_id == org_id,
                ExtractedProduct.asin == query.asin,
                ExtractedProduct.deleted_at.is_(None),
            )
            .order_by(ExtractedProduct.created_at.desc())
        )
        result = await db.execute(stmt)
        products = result.scalars().all()

        if products:
            latest = products[0]
            response.title = latest.title
            response.current_bsr = latest.bsr

            # Build BSR history from stored snapshots
            response.bsr_history = [
                {
                    "date": p.created_at.isoformat() if p.created_at else None,
                    "bsr": p.bsr,
                }
                for p in products
                if p.bsr is not None
            ]

            # Rough sales estimate from BSR (simplified formula)
            if latest.bsr:
                response.estimated_daily_sales = _estimate_daily_sales(latest.bsr)

    # Keyword-based niche stats
    if query.keywords:
        niche_stats = await _compute_niche_stats(db, org_id, query.keywords)
        response.competitor_count = niche_stats.get("competitor_count")
        response.avg_price = niche_stats.get("avg_price")
        response.avg_reviews = niche_stats.get("avg_reviews")
        response.niche_score = niche_stats.get("niche_score")
        response.related_keywords = niche_stats.get("related_keywords", [])

    return response


def _estimate_daily_sales(bsr: int) -> int:
    """Rough daily sales estimate from Amazon BSR (Kindle store).

    This uses a simplified power-law model.  Real implementations
    would use calibrated curves per marketplace/category.
    """
    if bsr <= 0:
        return 0
    if bsr <= 100:
        return max(1, int(500 / (bsr ** 0.5)))
    if bsr <= 1_000:
        return max(1, int(200 / (bsr ** 0.4)))
    if bsr <= 10_000:
        return max(1, int(100 / (bsr ** 0.35)))
    if bsr <= 100_000:
        return max(1, int(50 / (bsr ** 0.3)))
    return 1


async def _compute_niche_stats(
    db: AsyncSession,
    org_id: UUID,
    keywords: list[str],
) -> dict[str, Any]:
    """Compute aggregate niche statistics from stored product data.

    In production this queries the market intelligence module.
    """
    # For now, count products matching any keyword in title/keywords
    stmt = select(func.count(ExtractedProduct.id)).where(
        ExtractedProduct.org_id == org_id,
        ExtractedProduct.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    competitor_count = result.scalar() or 0

    # Average price
    price_stmt = select(func.avg(ExtractedProduct.price)).where(
        ExtractedProduct.org_id == org_id,
        ExtractedProduct.price.isnot(None),
        ExtractedProduct.deleted_at.is_(None),
    )
    price_result = await db.execute(price_stmt)
    avg_price_raw = price_result.scalar()
    avg_price = round(float(avg_price_raw), 2) if avg_price_raw else None

    return {
        "competitor_count": competitor_count,
        "avg_price": avg_price,
        "avg_reviews": None,  # Would come from reviews_json aggregation
        "niche_score": None,  # Would be computed by market intelligence
        "related_keywords": keywords,  # Placeholder
    }


# ---------------------------------------------------------------------------
# Knowledge Vault clip saving
# ---------------------------------------------------------------------------


async def save_clip(
    db: AsyncSession,
    org_id: UUID,
    request: ClipSaveRequest,
) -> ClipSaveResponse:
    """Save a clip from the browser to the Knowledge Vault."""
    clip = KnowledgeClip(
        org_id=org_id,
        clip_type=request.clip_type.value,
        content=request.content,
        source_url=request.source_url,
        title=request.title,
        tags=request.tags or [],
        notes=request.notes,
    )
    db.add(clip)
    await db.flush()
    await db.refresh(clip)

    return ClipSaveResponse(
        id=clip.id,
        org_id=clip.org_id,
        clip_type=request.clip_type,
        title=clip.title,
        saved_at=clip.created_at,
    )
