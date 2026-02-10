"""Chrome Extension API service layer.

Handles saving extracted Amazon data, serving quick research data,
and saving clips to the Knowledge Vault.
"""
from __future__ import annotations

import json
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cover_design.models import ExtractedProduct, KnowledgeClip
from app.models.market import CompetitorBook, MarketKeyword
from app.modules.chrome_extension.schemas import (
    ClipSaveRequest,
    ClipSaveResponse,
    ExtractDataRequest,
    ExtractedDataResponse,
    QuickResearchQuery,
    QuickResearchResponse,
    RelatedKeyword,
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

    Aggregates data from stored extractions, competitor tracking
    (CompetitorBook), and market intelligence scoring.  Each data
    source is wrapped in its own try/except so a single failing
    module never breaks the whole response.
    """
    response = QuickResearchResponse(asin=query.asin)

    if query.asin:
        # --- Stored extraction data (ExtractedProduct) -----------------
        try:
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

                # BSR history from extraction snapshots
                response.bsr_history = [
                    {
                        "date": p.created_at.isoformat() if p.created_at else None,
                        "bsr": p.bsr,
                    }
                    for p in products
                    if p.bsr is not None
                ]

                if latest.bsr:
                    response.estimated_daily_sales = _estimate_daily_sales(latest.bsr)
        except Exception:
            logger.warning(
                "Failed to fetch ExtractedProduct data for ASIN %s",
                query.asin,
                exc_info=True,
            )

        # --- Competitor tracking data (CompetitorBook) -----------------
        try:
            comp_stmt = (
                select(CompetitorBook)
                .where(
                    CompetitorBook.asin == query.asin,
                    CompetitorBook.deleted_at.is_(None),
                )
            )
            comp_result = await db.execute(comp_stmt)
            competitor = comp_result.scalar_one_or_none()

            if competitor:
                # Fill in title/BSR from competitor if not already set
                if not response.title:
                    response.title = competitor.title
                if response.current_bsr is None and competitor.bsr_current is not None:
                    response.current_bsr = competitor.bsr_current
                    response.estimated_daily_sales = _estimate_daily_sales(
                        competitor.bsr_current
                    )

                # Merge richer BSR history from competitor tracking
                if isinstance(competitor.bsr_history, list) and competitor.bsr_history:
                    tracked_history = [
                        {"date": pt.get("date"), "bsr": pt.get("bsr")}
                        for pt in competitor.bsr_history
                        if pt.get("bsr") is not None
                    ]
                    # Combine with extraction history, de-duplicate by date
                    existing_dates = {
                        entry.get("date") for entry in response.bsr_history
                    }
                    for entry in tracked_history:
                        if entry.get("date") not in existing_dates:
                            response.bsr_history.append(entry)
                    # Sort chronologically
                    response.bsr_history.sort(
                        key=lambda e: e.get("date") or ""
                    )
        except Exception:
            logger.warning(
                "Failed to fetch CompetitorBook data for ASIN %s",
                query.asin,
                exc_info=True,
            )

    # --- Keyword-based niche stats ------------------------------------
    if query.keywords:
        try:
            niche_stats = await _compute_niche_stats(db, org_id, query.keywords)
            response.competitor_count = niche_stats.get("competitor_count")
            response.avg_price = niche_stats.get("avg_price")
            response.avg_reviews = niche_stats.get("avg_reviews")
            response.niche_score = niche_stats.get("niche_score")
            response.related_keywords = niche_stats.get("related_keywords", [])
        except Exception:
            logger.warning(
                "Failed to compute niche stats for keywords %s",
                query.keywords,
                exc_info=True,
            )

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

    Queries ExtractedProduct and CompetitorBook tables for competition
    metrics, computes a niche opportunity score via the market
    intelligence scoring module, and generates related keyword
    suggestions via the LLM orchestration service with a local
    frequency-analysis fallback.
    """
    competitor_count = 0
    avg_price: float | None = None
    avg_reviews: float | None = None
    niche_score: float | None = None

    # --- Competitor count from ExtractedProduct -----------------------
    try:
        stmt = select(func.count(ExtractedProduct.id)).where(
            ExtractedProduct.org_id == org_id,
            ExtractedProduct.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        competitor_count = result.scalar() or 0
    except Exception:
        logger.warning("Failed to count ExtractedProduct entries", exc_info=True)

    # --- Average price from ExtractedProduct --------------------------
    try:
        price_stmt = select(func.avg(ExtractedProduct.price)).where(
            ExtractedProduct.org_id == org_id,
            ExtractedProduct.price.isnot(None),
            ExtractedProduct.deleted_at.is_(None),
        )
        price_result = await db.execute(price_stmt)
        avg_price_raw = price_result.scalar()
        avg_price = round(float(avg_price_raw), 2) if avg_price_raw else None
    except Exception:
        logger.warning("Failed to compute avg price from ExtractedProduct", exc_info=True)

    # --- Average reviews from CompetitorBook --------------------------
    try:
        reviews_stmt = select(func.avg(CompetitorBook.reviews_count)).where(
            CompetitorBook.deleted_at.is_(None),
            CompetitorBook.reviews_count > 0,
        )
        # Scope to org if the book has an org_id
        reviews_stmt = reviews_stmt.where(CompetitorBook.org_id == org_id)
        reviews_result = await db.execute(reviews_stmt)
        avg_reviews_raw = reviews_result.scalar()
        if avg_reviews_raw is not None:
            avg_reviews = round(float(avg_reviews_raw), 1)
    except Exception:
        logger.warning("Failed to compute avg reviews from CompetitorBook", exc_info=True)

    # Also augment competitor_count with CompetitorBook rows
    try:
        comp_count_stmt = select(func.count(CompetitorBook.id)).where(
            CompetitorBook.org_id == org_id,
            CompetitorBook.deleted_at.is_(None),
        )
        comp_count_result = await db.execute(comp_count_stmt)
        comp_count = comp_count_result.scalar() or 0
        competitor_count = max(competitor_count, comp_count)
    except Exception:
        logger.warning("Failed to count CompetitorBook entries", exc_info=True)

    # --- Niche score via market intelligence scoring ------------------
    try:
        from app.modules.market_intelligence.scoring import (
            NicheMetrics,
            calculate_niche_scores,
        )

        # Gather BSR values from CompetitorBook for the org
        bsr_stmt = select(CompetitorBook.bsr_current).where(
            CompetitorBook.org_id == org_id,
            CompetitorBook.bsr_current.isnot(None),
            CompetitorBook.deleted_at.is_(None),
        )
        bsr_result = await db.execute(bsr_stmt)
        bsr_values = [row[0] for row in bsr_result.all() if row[0] is not None]

        # Gather top-10 review counts for supply score
        top_reviews_stmt = (
            select(CompetitorBook.reviews_count)
            .where(
                CompetitorBook.org_id == org_id,
                CompetitorBook.deleted_at.is_(None),
            )
            .order_by(CompetitorBook.reviews_count.desc())
            .limit(10)
        )
        top_reviews_result = await db.execute(top_reviews_stmt)
        top_10_reviews = [row[0] for row in top_reviews_result.all()]

        # Gather avg rating from CompetitorBook
        rating_stmt = select(func.avg(CompetitorBook.rating)).where(
            CompetitorBook.org_id == org_id,
            CompetitorBook.rating.isnot(None),
            CompetitorBook.deleted_at.is_(None),
        )
        rating_result = await db.execute(rating_stmt)
        avg_rating_raw = rating_result.scalar()
        avg_rating = float(avg_rating_raw) if avg_rating_raw is not None else 0.0

        # Look up keyword search volume from MarketKeyword if available
        search_volume = 0
        try:
            for kw in keywords:
                kw_stmt = (
                    select(MarketKeyword.search_volume)
                    .where(
                        MarketKeyword.keyword == kw,
                        MarketKeyword.deleted_at.is_(None),
                    )
                    .limit(1)
                )
                kw_result = await db.execute(kw_stmt)
                kw_row = kw_result.scalar_one_or_none()
                if kw_row is not None:
                    search_volume = max(search_volume, kw_row)
        except Exception:
            logger.debug("MarketKeyword lookup failed, defaulting search_volume=0", exc_info=True)

        import statistics as _stats

        metrics = NicheMetrics(
            avg_monthly_search_volume=search_volume,
            bsr_values=bsr_values,
            trend_slope=0.0,
            total_competing_titles=competitor_count,
            avg_review_count=float(avg_reviews) if avg_reviews else 0.0,
            avg_rating=avg_rating,
            top_10_avg_reviews=(
                _stats.mean(top_10_reviews) if top_10_reviews else 0.0
            ),
            avg_price=float(avg_price) if avg_price else 0.0,
        )

        scores = calculate_niche_scores(metrics)
        niche_score = round(scores.opportunity_score, 1)
    except Exception:
        logger.warning("Failed to compute niche score via market intelligence", exc_info=True)

    # --- Related keywords ---------------------------------------------
    related_keywords: list[RelatedKeyword] = []
    try:
        related_keywords = await _generate_related_keywords(
            db, org_id, keywords
        )
        # Augment with MarketKeyword data for volume accuracy
        related_keywords = await _enrich_keywords_from_market_data(
            db, related_keywords
        )
    except Exception:
        logger.warning("Failed to generate related keywords", exc_info=True)

    return {
        "competitor_count": competitor_count,
        "avg_price": avg_price,
        "avg_reviews": avg_reviews,
        "niche_score": niche_score,
        "related_keywords": related_keywords,
    }


async def _enrich_keywords_from_market_data(
    db: AsyncSession,
    keywords: list[RelatedKeyword],
) -> list[RelatedKeyword]:
    """Enrich related keywords with real volume data from MarketKeyword table.

    If a keyword exists in the MarketKeyword table, replace the estimated
    volume indicator with one derived from actual search volume data.
    """
    if not keywords:
        return keywords

    enriched: list[RelatedKeyword] = []
    for kw in keywords:
        try:
            stmt = (
                select(MarketKeyword.search_volume, MarketKeyword.competition_score)
                .where(
                    MarketKeyword.keyword == kw.keyword,
                    MarketKeyword.deleted_at.is_(None),
                )
                .limit(1)
            )
            result = await db.execute(stmt)
            row = result.one_or_none()

            if row and row[0] is not None:
                sv = row[0]
                if sv >= 5000:
                    volume = "high"
                elif sv >= 1000:
                    volume = "medium"
                else:
                    volume = "low"
                enriched.append(
                    RelatedKeyword(
                        keyword=kw.keyword,
                        volume=volume,
                        relevance=kw.relevance,
                        source=kw.source,
                    )
                )
            else:
                enriched.append(kw)
        except Exception as exc:
            logger.warning(
                "Failed to enrich keyword %r from MarketKeyword data: %s",
                kw.keyword,
                exc,
            )
            enriched.append(kw)

    return enriched


# ---------------------------------------------------------------------------
# Related keyword generation
# ---------------------------------------------------------------------------

# Common English stop-words to exclude from frequency analysis
_STOP_WORDS: frozenset[str] = frozenset(
    "a an the and or but in on at to for of is it by as with from this that "
    "be are was were been have has had do does did not no nor so if its my "
    "your his her our their which what when where who whom how all each every "
    "both few more most other some such than too very can will just should "
    "now into also about up out after before between through during without".split()
)


def _extract_candidate_words(text: str) -> list[str]:
    """Tokenize text and return meaningful lowercase words."""
    tokens = re.findall(r"[a-zA-Z]{2,}", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS]


def _volume_indicator(frequency: int, max_freq: int) -> str:
    """Map a word frequency to a volume indicator bucket."""
    if max_freq == 0:
        return "low"
    ratio = frequency / max_freq
    if ratio >= 0.6:
        return "high"
    if ratio >= 0.25:
        return "medium"
    return "low"


async def _generate_related_keywords_via_llm(
    keywords: list[str],
) -> list[RelatedKeyword]:
    """Use the LLM orchestration service to generate related keywords.

    Returns an empty list if the service is unavailable or errors out,
    allowing the caller to fall back to local analysis.
    """
    try:
        from app.modules.llm_orchestration.service import LLMOrchestrationService
        from app.modules.llm_orchestration.schemas import (
            CompletionRequest,
            ModelConfig,
            TaskTypeEnum,
        )

        service = LLMOrchestrationService()

        keyword_list = ", ".join(keywords)
        prompt = (
            f"Given these Amazon book niche keywords: [{keyword_list}], "
            "generate 15 closely related keyword phrases that a self-published "
            "author could target. For each keyword, estimate the relative "
            "search volume as 'high', 'medium', or 'low' and rate its "
            "relevance from 0.0 to 1.0.\n\n"
            "Return ONLY a JSON array with objects like:\n"
            '[{"keyword": "phrase", "volume": "high", "relevance": 0.9}]\n'
            "No explanation, just valid JSON."
        )

        request = CompletionRequest(
            task_type=TaskTypeEnum.MARKET_ANALYSIS,
            prompt=prompt,
            system_prompt=(
                "You are a keyword research assistant for Amazon KDP "
                "(Kindle Direct Publishing). You understand book niches, "
                "reader search behaviour, and Amazon search algorithms. "
                "Respond ONLY with the requested JSON."
            ),
            config=ModelConfig(
                temperature=0.4,
                max_tokens=1024,
                skip_cache=False,
                skip_quality_check=True,
            ),
        )

        response = await service.complete(request)

        if not response.succeeded or not response.content:
            return []

        # Parse the JSON from the LLM response
        raw = response.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        items = json.loads(raw)
        results: list[RelatedKeyword] = []
        for item in items:
            if isinstance(item, dict) and "keyword" in item:
                volume = item.get("volume", "medium")
                if volume not in ("high", "medium", "low"):
                    volume = "medium"
                relevance = float(item.get("relevance", 0.5))
                relevance = max(0.0, min(1.0, relevance))
                results.append(
                    RelatedKeyword(
                        keyword=str(item["keyword"]),
                        volume=volume,
                        relevance=relevance,
                        source="llm",
                    )
                )
        return results

    except (ImportError, json.JSONDecodeError, KeyError, ValueError, OSError, RuntimeError) as exc:
        logger.debug(
            "LLM-based keyword generation unavailable (%s: %s), falling back to "
            "local analysis",
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        return []


async def _generate_related_keywords_from_corpus(
    db: AsyncSession,
    org_id: UUID,
    keywords: list[str],
) -> list[RelatedKeyword]:
    """Generate related keywords using word frequency analysis on stored products.

    Scans titles and stored keywords of all products for the org,
    builds a frequency map, and surfaces terms that co-occur with the
    input keywords but are not already in the input set.
    """
    stmt = select(
        ExtractedProduct.title,
        ExtractedProduct.keywords,
    ).where(
        ExtractedProduct.org_id == org_id,
        ExtractedProduct.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        # No stored data — return the input keywords as low-confidence suggestions
        return [
            RelatedKeyword(
                keyword=kw,
                volume="low",
                relevance=0.5,
                source="frequency",
            )
            for kw in keywords
        ]

    input_set = {kw.lower() for kw in keywords}
    word_counter: Counter[str] = Counter()

    for title, stored_kws in rows:
        if title:
            word_counter.update(_extract_candidate_words(title))
        if stored_kws:
            for kw in stored_kws:
                word_counter.update(_extract_candidate_words(kw))

    # Remove words that are already in the input keywords
    for kw in input_set:
        word_counter.pop(kw, None)
    # Remove very short or overly generic single words that leaked through
    for w in list(word_counter):
        if len(w) < 3:
            del word_counter[w]

    if not word_counter:
        return []

    max_freq = word_counter.most_common(1)[0][1] if word_counter else 1
    results: list[RelatedKeyword] = []

    for word, freq in word_counter.most_common(20):
        volume = _volume_indicator(freq, max_freq)
        relevance = round(min(1.0, freq / max_freq), 2)
        results.append(
            RelatedKeyword(
                keyword=word,
                volume=volume,
                relevance=relevance,
                source="frequency",
            )
        )

    return results


async def _generate_related_keywords(
    db: AsyncSession,
    org_id: UUID,
    keywords: list[str],
) -> list[RelatedKeyword]:
    """Produce related keyword suggestions.

    Strategy:
      1. Attempt LLM-based generation (richer, more creative).
      2. If that fails or returns nothing, fall back to corpus
         frequency analysis from stored product data.
      3. Merge results, de-duplicate, and cap at 20 entries.
    """
    if not keywords:
        return []

    # Try LLM first
    llm_keywords = await _generate_related_keywords_via_llm(keywords)

    # Always run local analysis for data-backed suggestions
    corpus_keywords = await _generate_related_keywords_from_corpus(
        db, org_id, keywords
    )

    # Merge: LLM results first, then corpus results (de-duplicated)
    seen: set[str] = set()
    merged: list[RelatedKeyword] = []

    for kw in llm_keywords + corpus_keywords:
        normalised = kw.keyword.lower().strip()
        if normalised not in seen:
            seen.add(normalised)
            merged.append(kw)

    # Cap at 20 keyword suggestions
    return merged[:20]


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
