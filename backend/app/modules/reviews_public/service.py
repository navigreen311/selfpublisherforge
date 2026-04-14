"""Service layer for the public reviews endpoint.

Aggregates non-sensitive review data for a book into a response shape that
is safe to expose to unauthenticated callers. Adds Redis-backed caching
keyed by book id + max reviews count.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.review_intelligence.models import BookReview
from app.modules.reviews_public.schemas import PublicReviewItem, PublicReviewsResponse

logger = logging.getLogger(__name__)

PUBLIC_CACHE_TTL = 300  # 5 minutes
_CACHE_PREFIX = "public_reviews:"
EXCERPT_LEN = 280


def _excerpt(text: str | None) -> str | None:
    if not text:
        return None
    text = text.strip()
    if len(text) <= EXCERPT_LEN:
        return text
    return text[: EXCERPT_LEN - 1].rstrip() + "…"


def _serialise(resp: PublicReviewsResponse) -> str:
    return resp.model_dump_json()


def _deserialise(raw: str) -> PublicReviewsResponse:
    return PublicReviewsResponse.model_validate_json(raw)


async def _try_redis_get(key: str) -> str | None:
    try:
        import redis.asyncio as redis

        from app.config import get_settings

        client = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
        try:
            return await client.get(key)
        finally:
            await client.close()
    except Exception:  # noqa: BLE001 - cache is best-effort
        return None


async def _try_redis_set(key: str, value: str, ttl: int) -> None:
    try:
        import redis.asyncio as redis

        from app.config import get_settings

        client = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
        try:
            await client.set(key, value, ex=ttl)
        finally:
            await client.close()
    except Exception:  # noqa: BLE001
        return


async def build_public_reviews(
    db: AsyncSession,
    book_id: UUID,
    max_reviews: int = 3,
) -> PublicReviewsResponse:
    """Aggregate published review stats + top reviews for a book.

    Only non-competitor reviews are exposed (those are the book owner's own
    reviews). Reviewer names are surfaced but free-text content is truncated
    to a short excerpt to avoid accidental leakage of very long reviews.
    """
    cache_key = f"{_CACHE_PREFIX}{book_id}:{max_reviews}"
    cached = await _try_redis_get(cache_key)
    if cached:
        try:
            return _deserialise(cached)
        except Exception:  # noqa: BLE001
            pass

    # Aggregate rating + count
    agg_stmt = select(
        func.count(BookReview.id),
        func.coalesce(func.avg(BookReview.star_rating), 0.0),
    ).where(
        BookReview.book_id == book_id,
        BookReview.is_competitor.is_(False),
    )
    agg_row = (await db.execute(agg_stmt)).one()
    total = int(agg_row[0] or 0)
    avg_rating = round(float(agg_row[1] or 0.0), 2)

    # Top reviews — 5-star first, then most recent
    rev_stmt = (
        select(BookReview)
        .where(
            BookReview.book_id == book_id,
            BookReview.is_competitor.is_(False),
        )
        .order_by(
            BookReview.star_rating.desc(),
            BookReview.review_date.desc().nullslast(),
        )
        .limit(max(0, min(max_reviews, 10)))
    )
    review_rows = (await db.execute(rev_stmt)).scalars().all()
    reviews = [
        PublicReviewItem(
            rating=float(r.star_rating),
            title=r.title,
            body_excerpt=_excerpt(r.body),
            reviewer_name=r.reviewer_name,
            date=r.review_date,
        )
        for r in review_rows
    ]

    response = PublicReviewsResponse(
        book_id=str(book_id),
        book_title=None,  # book title is loaded from project module elsewhere
        rating=avg_rating,
        review_count=total,
        reviews=reviews,
    )

    await _try_redis_set(cache_key, _serialise(response), PUBLIC_CACHE_TTL)
    return response
