"""Service layer for the Product Page Conversion Lab.

Orchestrates listing analysis, blurb generation, A/B test management,
Look Inside analysis, and mobile checks.
"""

from __future__ import annotations

import logging
import math
import re
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.project import Book
from app.models.publishing import Listing
from app.modules.product_page_lab.analyzer import analyze_listing
from app.modules.product_page_lab.blurb_generator import (
    generate_blurb_variants_ai,
    generate_blurb_variants_local,
)
from app.modules.product_page_lab.mobile_checker import check_mobile_display
from app.modules.product_page_lab.models import ABTest
from app.modules.product_page_lab.schemas import (
    ABTestCreateRequest,
    ABTestResponse,
    ABTestResultsResponse,
    ABTestStatus,
    ABTestUpdateRequest,
    ABTestVariantResult,
    BlurbGenerateRequest,
    BlurbGenerateResponse,
    ConversionScores,
    Genre,
    ListingAnalysis,
    ListingAnalyzeRequest,
    LookInsideAnalysis,
    LookInsideAnalyzeRequest,
    LookInsideSection,
    MobileCheckRequest,
    MobileCheckResult,
    Recommendation,
)

logger = logging.getLogger(__name__)

# Minimum total impressions across both variants before statistical
# significance can be meaningfully assessed.
_MIN_SAMPLE_SIZE = 100


# ---------------------------------------------------------------------------
# Listing analysis
# ---------------------------------------------------------------------------


async def analyze_amazon_listing(
    request: ListingAnalyzeRequest,
    db: AsyncSession,
) -> ListingAnalysis:
    """Analyze an Amazon listing by ASIN, URL, or book ID.

    Resolves listing data from the database using the book's title,
    subtitle, and any associated ``Listing.listing_data`` JSONB fields
    (description/blurb, keywords, categories, price, genre).  When no
    stored data can be found, raises ``ValidationError``.
    """
    asin = request.asin
    if not asin and request.url:
        asin = _extract_asin_from_url(request.url)

    # Attempt to resolve a Book record from the database.
    book: Book | None = None

    if request.book_id is not None:
        result = await db.execute(
            select(Book).where(
                Book.id == request.book_id,
                Book.deleted_at.is_(None),
            )
        )
        book = result.scalar_one_or_none()
        if book is None:
            raise NotFoundError(
                resource="Book",
                detail=f"Book {request.book_id} not found.",
            )

    if book is None and asin:
        result = await db.execute(
            select(Book).where(
                Book.asin == asin,
                Book.deleted_at.is_(None),
            )
        )
        book = result.scalar_one_or_none()

    if book is None:
        raise ValidationError(
            message=(
                "No book data found for the given ASIN or URL. "
                "Please provide a valid book_id, or ensure the ASIN "
                "is associated with a book in the system."
            ),
        )

    # Gather listing data from the first associated Listing record.
    listing_result = await db.execute(
        select(Listing)
        .where(
            Listing.book_id == book.id,
            Listing.deleted_at.is_(None),
        )
        .order_by(Listing.updated_at.desc())
    )
    listing: Listing | None = listing_result.scalars().first()

    listing_data: dict = {}
    if listing is not None and listing.listing_data:
        listing_data = listing.listing_data

    # Build the full title from the book record, including subtitle
    # and any override stored in listing_data.
    title = listing_data.get("title") or book.title or ""
    if book.subtitle and book.subtitle not in title:
        title = f"{title}: {book.subtitle}"

    blurb = listing_data.get("description") or listing_data.get("blurb") or ""
    keywords = listing_data.get("keywords") or []
    categories = listing_data.get("categories") or []
    price = listing_data.get("current_price") or listing_data.get("price")
    genre = listing_data.get("genre")
    resolved_asin = asin or book.asin

    # Extract book metadata if available (metadata_ column is JSONB).
    book_meta: dict = {}
    if hasattr(book, "metadata_") and book.metadata_:
        book_meta = book.metadata_

    # Fall back to book metadata for fields not present in listing_data.
    if not blurb:
        blurb = book_meta.get("description") or book_meta.get("blurb") or ""
    if not keywords:
        keywords = book_meta.get("keywords") or []
    if not categories:
        categories = book_meta.get("categories") or []
    if price is None:
        price = book_meta.get("price")
    if not genre:
        genre = book_meta.get("genre")

    logger.info(
        "Analyzing listing for book %s (ASIN=%s): title_len=%d, blurb_len=%d, keywords=%d",
        book.id,
        resolved_asin,
        len(title),
        len(blurb),
        len(keywords),
    )

    return analyze_listing(
        title=title,
        blurb=blurb,
        keywords=keywords,
        categories=categories,
        price=price,
        genre=genre,
        asin=resolved_asin,
    )


async def analyze_listing_with_data(
    title: str,
    blurb: str,
    keywords: list[str] | None = None,
    categories: list[str] | None = None,
    price: float | None = None,
    genre: str | None = None,
    asin: str | None = None,
) -> ListingAnalysis:
    """Analyze a listing using directly provided data.

    This bypass function accepts all listing fields inline, runs the
    full algorithmic analysis pipeline, and returns scored results with
    actionable recommendations.  No database or external API access is
    required.
    """
    return analyze_listing(
        title=title,
        blurb=blurb,
        keywords=keywords,
        categories=categories,
        price=price,
        genre=genre,
        asin=asin,
    )


# ---------------------------------------------------------------------------
# Blurb generation
# ---------------------------------------------------------------------------


async def generate_blurb_variants(
    request: BlurbGenerateRequest,
) -> BlurbGenerateResponse:
    """Generate optimized blurb variations.

    Attempts AI generation first, falls back to template-based approach.
    """
    try:
        return await generate_blurb_variants_ai(
            current_blurb=request.current_blurb,
            genre=request.genre,
            target_audience=request.target_audience,
            keywords=request.keywords,
            tone=request.tone,
            num_variants=request.num_variants,
            llm_client=None,  # Will be injected when LLM orchestration is ready
        )
    except (RuntimeError, ConnectionError, ValueError, TimeoutError):
        return generate_blurb_variants_local(
            current_blurb=request.current_blurb,
            genre=request.genre,
            target_audience=request.target_audience,
            keywords=request.keywords,
            tone=request.tone,
            num_variants=request.num_variants,
        )


# ---------------------------------------------------------------------------
# A/B testing
# ---------------------------------------------------------------------------


async def create_ab_test(
    request: ABTestCreateRequest,
    org_id: UUID,
    db: AsyncSession,
) -> ABTestResponse:
    """Create a new A/B test for blurb variants."""
    ab_test = ABTest(
        id=uuid.uuid4(),
        org_id=org_id,
        book_id=request.book_id,
        name=request.name,
        status=ABTestStatus.DRAFT,
        variant_a_content=request.variant_a,
        variant_b_content=request.variant_b,
        variant_a_impressions=0,
        variant_a_clicks=0,
        variant_b_impressions=0,
        variant_b_clicks=0,
        duration_days=request.duration_days,
        started_at=None,
        completed_at=None,
    )

    db.add(ab_test)
    await db.flush()
    await db.refresh(ab_test)

    return _ab_test_to_response(ab_test)


async def list_ab_tests(
    org_id: UUID,
    db: AsyncSession,
    book_id: UUID | None = None,
    status: ABTestStatus | None = None,
) -> list[ABTestResponse]:
    """List A/B tests for an organisation, with optional filtering."""
    stmt = select(ABTest).where(
        ABTest.org_id == org_id,
        ABTest.deleted_at.is_(None),
    )

    if book_id is not None:
        stmt = stmt.where(ABTest.book_id == book_id)

    if status is not None:
        stmt = stmt.where(ABTest.status == status.value)

    stmt = stmt.order_by(ABTest.created_at.desc())

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [_ab_test_to_response(row) for row in rows]


async def get_ab_test(
    test_id: UUID,
    db: AsyncSession,
) -> ABTestResponse:
    """Get A/B test by ID with results.

    Raises ``NotFoundError`` when the test does not exist.
    """
    ab_test = await _fetch_ab_test(test_id, db)
    return _ab_test_to_response(ab_test)


async def update_ab_test(
    test_id: UUID,
    request: ABTestUpdateRequest,
    db: AsyncSession,
) -> ABTestResponse:
    """Update an existing A/B test.

    Only tests in DRAFT or PAUSED status may have their content changed.
    Status transitions are validated (e.g. cannot move a COMPLETED test
    back to DRAFT).
    """
    ab_test = await _fetch_ab_test(test_id, db)

    # Validate content changes only allowed when not running/completed
    content_fields_changing = request.variant_a is not None or request.variant_b is not None
    if content_fields_changing and ab_test.status in (
        ABTestStatus.RUNNING.value,
        ABTestStatus.COMPLETED.value,
    ):
        raise ValidationError(
            message="Cannot modify variant content while the test is running or completed.",
        )

    # Validate status transition
    if request.status is not None:
        _validate_status_transition(ab_test.status, request.status.value)

    # Apply updates
    if request.name is not None:
        ab_test.name = request.name
    if request.variant_a is not None:
        ab_test.variant_a_content = request.variant_a
    if request.variant_b is not None:
        ab_test.variant_b_content = request.variant_b
    if request.duration_days is not None:
        ab_test.duration_days = request.duration_days
    if request.status is not None:
        ab_test.status = request.status.value
        if request.status == ABTestStatus.RUNNING and ab_test.started_at is None:
            ab_test.started_at = datetime.now(UTC)
        elif request.status == ABTestStatus.COMPLETED and ab_test.completed_at is None:
            ab_test.completed_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(ab_test)

    return _ab_test_to_response(ab_test)


async def start_ab_test(
    test_id: UUID,
    db: AsyncSession,
) -> ABTestResponse:
    """Start an A/B test.

    Raises ``NotFoundError`` when the test does not exist.
    Raises ``ValidationError`` if the test is not in DRAFT or PAUSED status.
    """
    ab_test = await _fetch_ab_test(test_id, db)

    if ab_test.status not in (ABTestStatus.DRAFT.value, ABTestStatus.PAUSED.value):
        raise ValidationError(
            message=f"Cannot start a test with status '{ab_test.status}'. "
            f"Only DRAFT or PAUSED tests can be started.",
        )

    ab_test.status = ABTestStatus.RUNNING.value
    ab_test.started_at = ab_test.started_at or datetime.now(UTC)
    await db.flush()
    await db.refresh(ab_test)

    return _ab_test_to_response(ab_test)


async def get_test_results(
    test_id: UUID,
    db: AsyncSession,
) -> ABTestResultsResponse:
    """Return detailed test metrics with statistical significance analysis.

    Computes click-through rates, a two-proportion z-test for statistical
    significance, and remaining time estimates.
    """
    ab_test = await _fetch_ab_test(test_id, db)

    # Auto-complete tests that have exceeded their duration
    if ab_test.status == ABTestStatus.RUNNING.value and ab_test.started_at is not None:
        end_date = ab_test.started_at + timedelta(days=ab_test.duration_days)
        if datetime.now(UTC) >= end_date:
            ab_test.status = ABTestStatus.COMPLETED.value
            ab_test.completed_at = datetime.now(UTC)
            await db.flush()
            await db.refresh(ab_test)

    # Compute rates
    a_ctr = ab_test.variant_a_clicks / ab_test.variant_a_impressions * 100 if ab_test.variant_a_impressions > 0 else 0.0
    b_ctr = ab_test.variant_b_clicks / ab_test.variant_b_impressions * 100 if ab_test.variant_b_impressions > 0 else 0.0
    a_conv = ab_test.variant_a_clicks / ab_test.variant_a_impressions if ab_test.variant_a_impressions > 0 else 0.0
    b_conv = ab_test.variant_b_clicks / ab_test.variant_b_impressions if ab_test.variant_b_impressions > 0 else 0.0

    total_impressions = ab_test.variant_a_impressions + ab_test.variant_b_impressions
    sample_sufficient = total_impressions >= _MIN_SAMPLE_SIZE

    # Statistical significance via two-proportion z-test
    confidence = _compute_z_test_confidence(
        ab_test.variant_a_impressions,
        ab_test.variant_a_clicks,
        ab_test.variant_b_impressions,
        ab_test.variant_b_clicks,
    )
    is_significant = confidence >= 95.0 and sample_sufficient

    # Determine winner
    winner = None
    if ab_test.status == ABTestStatus.COMPLETED.value or is_significant:
        if a_ctr > b_ctr:
            winner = "A"
        elif b_ctr > a_ctr:
            winner = "B"
        else:
            winner = "tie"

    # Time calculations
    days_running: int | None = None
    days_remaining: int | None = None
    if ab_test.started_at is not None:
        delta = datetime.now(UTC) - ab_test.started_at
        days_running = max(0, delta.days)
        if ab_test.status == ABTestStatus.RUNNING.value:
            days_remaining = max(0, ab_test.duration_days - delta.days)

    return ABTestResultsResponse(
        test_id=ab_test.id,
        name=ab_test.name,
        status=ABTestStatus(ab_test.status),
        variant_a=ABTestVariantResult(
            variant_label="A",
            content=ab_test.variant_a_content,
            impressions=ab_test.variant_a_impressions,
            clicks=ab_test.variant_a_clicks,
            click_through_rate=round(a_ctr, 2),
            conversion_rate=round(a_conv * 100, 2),
            estimated_score=round(min(100.0, a_ctr * 10), 1),
        ),
        variant_b=ABTestVariantResult(
            variant_label="B",
            content=ab_test.variant_b_content,
            impressions=ab_test.variant_b_impressions,
            clicks=ab_test.variant_b_clicks,
            click_through_rate=round(b_ctr, 2),
            conversion_rate=round(b_conv * 100, 2),
            estimated_score=round(min(100.0, b_ctr * 10), 1),
        ),
        winner=winner,
        confidence=round(confidence, 2) if confidence else None,
        is_statistically_significant=is_significant,
        sample_size_sufficient=sample_sufficient,
        minimum_sample_needed=_MIN_SAMPLE_SIZE,
        days_running=days_running,
        days_remaining=days_remaining,
    )


# ---------------------------------------------------------------------------
# Look Inside analysis
# ---------------------------------------------------------------------------


async def analyze_look_inside(
    request: LookInsideAnalyzeRequest,
) -> LookInsideAnalysis:
    """Analyze the Look Inside preview effectiveness."""
    sections: list[LookInsideSection] = []
    recommendations: list[Recommendation] = []

    preview_text = request.preview_text
    genre = request.genre
    chapter_titles = request.chapter_titles

    # --- First page analysis ---
    first_page = preview_text[:500]
    first_page_score = _score_first_page(first_page, genre)
    sections.append(
        LookInsideSection(
            section="first_page",
            score=first_page_score,
            feedback=_first_page_feedback(first_page_score),
            suggestions=_first_page_suggestions(first_page, first_page_score),
        )
    )

    # --- Hook strength ---
    first_paragraph = _extract_first_paragraph(preview_text)
    hook_score = _score_hook(first_paragraph, genre)
    sections.append(
        LookInsideSection(
            section="opening_hook",
            score=hook_score,
            feedback=_hook_feedback(hook_score),
            suggestions=_hook_suggestions(hook_score),
        )
    )

    # --- Pacing ---
    pacing_score = _score_pacing(preview_text)
    sections.append(
        LookInsideSection(
            section="pacing",
            score=pacing_score,
            feedback=f"Pacing score: {pacing_score}/100.",
            suggestions=_pacing_suggestions(pacing_score),
        )
    )

    # --- Table of contents ---
    toc_score = _score_toc(chapter_titles)
    sections.append(
        LookInsideSection(
            section="table_of_contents",
            score=toc_score,
            feedback=_toc_feedback(toc_score, chapter_titles),
            suggestions=_toc_suggestions(toc_score, chapter_titles),
        )
    )

    # Overall score (weighted)
    overall = first_page_score * 0.30 + hook_score * 0.30 + pacing_score * 0.20 + toc_score * 0.20

    # Build recommendations from sections with low scores
    for section in sections:
        if section.score < 60:
            for suggestion in section.suggestions:
                recommendations.append(
                    Recommendation(
                        area=f"look_inside_{section.section}",
                        severity="critical" if section.score < 40 else "warning",
                        message=section.feedback,
                        suggestion=suggestion,
                    )
                )

    return LookInsideAnalysis(
        overall_score=round(overall, 1),
        hook_strength=round(hook_score, 1),
        first_page_impact=round(first_page_score, 1),
        pacing_score=round(pacing_score, 1),
        toc_effectiveness=round(toc_score, 1),
        sections=sections,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# Mobile check
# ---------------------------------------------------------------------------


async def check_mobile_listing(
    request: MobileCheckRequest,
) -> MobileCheckResult:
    """Check listing appearance on mobile devices."""
    return check_mobile_display(
        title=request.title,
        blurb=request.blurb,
        author_name=request.author_name,
        subtitle=request.subtitle,
        cover_image_url=request.cover_image_url,
        price=request.price,
    )


# ---------------------------------------------------------------------------
# Conversion scores
# ---------------------------------------------------------------------------


async def get_conversion_scores(
    book_id: UUID,
    db: AsyncSession,
) -> ConversionScores:
    """Get aggregate conversion optimization scores for a book.

    Derives a blurb score from the best-performing completed A/B test
    for the given book.  Other score dimensions (listing, mobile,
    look-inside) are not persisted yet and remain ``None``.
    """
    # Pull the most recent completed A/B test for this book to derive
    # a blurb conversion score.
    result = await db.execute(
        select(ABTest)
        .where(
            ABTest.book_id == book_id,
            ABTest.status == ABTestStatus.COMPLETED.value,
            ABTest.deleted_at.is_(None),
        )
        .order_by(ABTest.completed_at.desc())
    )
    completed_tests = result.scalars().all()

    blurb_score: float | None = None
    last_analyzed: datetime | None = None
    recommendations_count = 0

    if completed_tests:
        # Use the best CTR across all completed tests for this book.
        best_ctr = 0.0
        for test in completed_tests:
            a_ctr = test.variant_a_clicks / test.variant_a_impressions * 100 if test.variant_a_impressions > 0 else 0.0
            b_ctr = test.variant_b_clicks / test.variant_b_impressions * 100 if test.variant_b_impressions > 0 else 0.0
            best_ctr = max(best_ctr, a_ctr, b_ctr)

        # Normalise CTR to a 0-100 score (10% CTR -> 100 score).
        blurb_score = round(min(100.0, best_ctr * 10), 1)
        last_analyzed = completed_tests[0].completed_at

        # Count tests where neither variant exceeds 5% CTR as needing attention.
        for test in completed_tests:
            a_ctr = test.variant_a_clicks / test.variant_a_impressions * 100 if test.variant_a_impressions > 0 else 0.0
            b_ctr = test.variant_b_clicks / test.variant_b_impressions * 100 if test.variant_b_impressions > 0 else 0.0
            if max(a_ctr, b_ctr) < 5.0:
                recommendations_count += 1

    # Count active (running) tests that have not been analysed yet.
    running_result = await db.execute(
        select(func.count())
        .select_from(ABTest)
        .where(
            ABTest.book_id == book_id,
            ABTest.status == ABTestStatus.RUNNING.value,
            ABTest.deleted_at.is_(None),
        )
    )
    running_count = running_result.scalar() or 0
    if running_count > 0 and blurb_score is None:
        recommendations_count += 1  # Suggest waiting for results

    # Overall score is the average of available dimensions.
    available_scores = [s for s in [blurb_score] if s is not None]
    overall_score = round(sum(available_scores) / len(available_scores), 1) if available_scores else 0.0

    return ConversionScores(
        book_id=book_id,
        listing_score=None,
        blurb_score=blurb_score,
        mobile_score=None,
        look_inside_score=None,
        overall_score=overall_score,
        last_analyzed_at=last_analyzed,
        recommendations_count=recommendations_count,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_asin_from_url(url: str) -> str | None:
    """Extract ASIN from an Amazon product URL."""
    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/ASIN/([A-Z0-9]{10})",
        r"asin=([A-Z0-9]{10})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


async def _fetch_ab_test(test_id: UUID, db: AsyncSession) -> ABTest:
    """Fetch a single non-deleted ABTest or raise ``NotFoundError``."""
    result = await db.execute(
        select(ABTest).where(
            ABTest.id == test_id,
            ABTest.deleted_at.is_(None),
        )
    )
    ab_test = result.scalar_one_or_none()
    if ab_test is None:
        raise NotFoundError(resource="ABTest", detail=f"A/B test {test_id} not found.")
    return ab_test


def _validate_status_transition(current: str, target: str) -> None:
    """Validate that the status transition is allowed.

    Allowed transitions:
        draft   -> running, paused
        running -> paused, completed
        paused  -> running, completed
        completed -> (none)
    """
    allowed: dict[str, set[str]] = {
        ABTestStatus.DRAFT.value: {ABTestStatus.RUNNING.value, ABTestStatus.PAUSED.value},
        ABTestStatus.RUNNING.value: {ABTestStatus.PAUSED.value, ABTestStatus.COMPLETED.value},
        ABTestStatus.PAUSED.value: {ABTestStatus.RUNNING.value, ABTestStatus.COMPLETED.value},
        ABTestStatus.COMPLETED.value: set(),
    }
    if target not in allowed.get(current, set()):
        raise ValidationError(
            message=f"Cannot transition from '{current}' to '{target}'.",
        )


def _compute_z_test_confidence(
    n_a: int,
    x_a: int,
    n_b: int,
    x_b: int,
) -> float:
    """Compute confidence level using a two-proportion z-test.

    Returns a confidence percentage (0-100).  Returns 0.0 when there are
    insufficient observations.
    """
    if n_a <= 0 or n_b <= 0:
        return 0.0

    p_a = x_a / n_a
    p_b = x_b / n_b
    p_pool = (x_a + x_b) / (n_a + n_b)

    # Avoid division-by-zero when pooled proportion is 0 or 1.
    if p_pool <= 0 or p_pool >= 1:
        return 0.0

    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
    if se == 0:
        return 0.0

    z = abs(p_a - p_b) / se

    # Approximate two-tailed p-value -> confidence using the standard
    # normal CDF.  We use an approximation good enough for A/B testing
    # dashboards.  For |z| > 3.5 we cap at 99.95%.
    if z > 3.5:
        return 99.95
    # Abramowitz-Stegun rational approximation of the normal CDF.
    p_value = 2.0 * _normal_sf(z)
    confidence = (1.0 - p_value) * 100
    return max(0.0, min(100.0, confidence))


def _normal_sf(z: float) -> float:
    """Survival function (1 - CDF) of the standard normal distribution.

    Uses the Abramowitz-Stegun approximation (formula 26.2.17) which is
    accurate to about 1e-5.
    """
    if z < 0:
        return 1.0 - _normal_sf(-z)
    b0 = 0.2316419
    b1 = 0.319381530
    b2 = -0.356563782
    b3 = 1.781477937
    b4 = -1.821255978
    b5 = 1.330274429
    t = 1.0 / (1.0 + b0 * z)
    phi = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    return phi * t * (b1 + t * (b2 + t * (b3 + t * (b4 + t * b5))))


def _ab_test_to_response(ab_test: ABTest) -> ABTestResponse:
    """Convert an ABTest model to response schema."""
    # Calculate CTR
    a_ctr = ab_test.variant_a_clicks / ab_test.variant_a_impressions * 100 if ab_test.variant_a_impressions > 0 else 0.0
    b_ctr = ab_test.variant_b_clicks / ab_test.variant_b_impressions * 100 if ab_test.variant_b_impressions > 0 else 0.0

    # Conversion rate (proportion as percentage)
    a_conv = (
        ab_test.variant_a_clicks / ab_test.variant_a_impressions * 100 if ab_test.variant_a_impressions > 0 else 0.0
    )
    b_conv = (
        ab_test.variant_b_clicks / ab_test.variant_b_impressions * 100 if ab_test.variant_b_impressions > 0 else 0.0
    )

    # Estimated score normalised to 0-100 (10% CTR -> score 100)
    a_score = round(min(100.0, a_ctr * 10), 1)
    b_score = round(min(100.0, b_ctr * 10), 1)

    # Determine winner and confidence if test is completed
    winner = None
    confidence = None
    if ab_test.status in (ABTestStatus.COMPLETED.value, ABTestStatus.COMPLETED):
        confidence = _compute_z_test_confidence(
            ab_test.variant_a_impressions,
            ab_test.variant_a_clicks,
            ab_test.variant_b_impressions,
            ab_test.variant_b_clicks,
        )
        if a_ctr > b_ctr:
            winner = "A"
        elif b_ctr > a_ctr:
            winner = "B"
        else:
            winner = "tie"
        confidence = round(confidence, 2)

    return ABTestResponse(
        id=ab_test.id,
        book_id=ab_test.book_id,
        name=ab_test.name,
        status=ABTestStatus(ab_test.status) if isinstance(ab_test.status, str) else ab_test.status,
        variant_a=ABTestVariantResult(
            variant_label="A",
            content=ab_test.variant_a_content,
            impressions=ab_test.variant_a_impressions,
            clicks=ab_test.variant_a_clicks,
            click_through_rate=round(a_ctr, 2),
            conversion_rate=round(a_conv, 2),
            estimated_score=a_score,
        ),
        variant_b=ABTestVariantResult(
            variant_label="B",
            content=ab_test.variant_b_content,
            impressions=ab_test.variant_b_impressions,
            clicks=ab_test.variant_b_clicks,
            click_through_rate=round(b_ctr, 2),
            conversion_rate=round(b_conv, 2),
            estimated_score=b_score,
        ),
        winner=winner,
        confidence=confidence,
        started_at=ab_test.started_at,
        completed_at=ab_test.completed_at,
        created_at=ab_test.created_at,
        updated_at=ab_test.updated_at,
    )


# ---------------------------------------------------------------------------
# Look Inside scoring helpers
# ---------------------------------------------------------------------------


def _extract_first_paragraph(text: str) -> str:
    """Extract the first paragraph from preview text."""
    paragraphs = text.split("\n\n")
    for p in paragraphs:
        p = p.strip()
        if len(p) > 20:
            return p
    return text[:300]


def _score_first_page(text: str, genre: Genre) -> float:
    """Score the first page of the Look Inside preview."""
    score = 50.0

    # Word count of first page
    words = text.split()
    word_count = len(words)

    if word_count < 50:
        score -= 10  # Too sparse
    elif word_count > 400:
        score -= 5  # Dense opening can be overwhelming

    # Check for dialogue (engagement signal)
    if '"' in text or "\u201c" in text:
        score += 10

    # Check for action/movement verbs
    action_words = ["ran", "grabbed", "pushed", "pulled", "jumped", "screamed", "whispered", "rushed"]
    if any(w in text.lower() for w in action_words):
        score += 10

    # Check for setting establishment
    sensory_words = ["smelled", "tasted", "felt", "heard", "saw", "looked", "bright", "dark", "cold", "warm"]
    if any(w in text.lower() for w in sensory_words):
        score += 10

    # Short first sentence is usually more impactful
    first_sentence = text.split(".")[0] if "." in text else text[:100]
    if len(first_sentence.split()) <= 15:
        score += 10
    elif len(first_sentence.split()) > 30:
        score -= 5

    return max(0, min(100, score))


def _score_hook(paragraph: str, genre: Genre) -> float:
    """Score the opening hook."""
    score = 50.0

    paragraph_lower = paragraph.lower()

    # Question opening
    if "?" in paragraph[:200]:
        score += 15

    # Emotional tension
    tension_words = ["never", "always", "impossible", "only", "last", "first", "everything", "nothing"]
    tension_count = sum(1 for w in tension_words if w in paragraph_lower)
    score += min(20, tension_count * 5)

    # In media res (starting in the middle of action)
    action_indicators = ["was running", "had to", "couldn't", "didn't", "wasn't", "grabbed", "slammed"]
    if any(ind in paragraph_lower for ind in action_indicators):
        score += 15

    # Short, punchy opening
    first_sentence = paragraph.split(".")[0] if "." in paragraph else paragraph[:80]
    if len(first_sentence.split()) <= 10:
        score += 10

    return max(0, min(100, score))


def _score_pacing(text: str) -> float:
    """Score the pacing of the preview text."""
    score = 60.0

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return 30.0

    # Variety in paragraph length (good pacing)
    lengths = [len(p.split()) for p in paragraphs]
    if len(lengths) > 1:
        avg_length = sum(lengths) / len(lengths)
        variance = sum((length - avg_length) ** 2 for length in lengths) / len(lengths)
        # Some variance is good (varied pacing)
        if variance > 100:
            score += 15
        elif variance < 10:
            score -= 10  # Too uniform

    # Dialogue mixed with narrative
    dialogue_paras = sum(1 for p in paragraphs if '"' in p or "\u201c" in p)
    narrative_paras = len(paragraphs) - dialogue_paras
    if dialogue_paras > 0 and narrative_paras > 0:
        score += 10

    # Short paragraphs for tension
    short_paras = sum(1 for length in lengths if length <= 15)
    if short_paras > 0:
        score += 5

    return max(0, min(100, score))


def _score_toc(chapter_titles: list[str]) -> float:
    """Score the table of contents."""
    if not chapter_titles:
        return 40.0  # No TOC provided

    score = 60.0

    # Having a TOC is good
    if len(chapter_titles) >= 5:
        score += 10

    # Descriptive titles (not just "Chapter 1")
    generic_count = sum(1 for t in chapter_titles if re.match(r"^chapter\s+\d+$", t.lower().strip()))
    descriptive_ratio = 1 - (generic_count / max(len(chapter_titles), 1))
    score += descriptive_ratio * 20

    # Intriguing titles (contain interesting words)
    intriguing_words = ["secret", "dark", "last", "first", "blood", "fire", "night", "truth"]
    intriguing_count = sum(1 for t in chapter_titles if any(w in t.lower() for w in intriguing_words))
    score += min(10, intriguing_count * 3)

    return max(0, min(100, score))


def _first_page_feedback(score: float) -> str:
    if score >= 80:
        return "Excellent first page impact. Strong opening that hooks readers."
    if score >= 60:
        return "Good first page. Consider adding more sensory detail or action."
    if score >= 40:
        return "Average first page. Needs stronger opening elements."
    return "Weak first page impact. Major revision recommended."


def _first_page_suggestions(text: str, score: float) -> list[str]:
    suggestions = []
    if score < 60:
        suggestions.append("Start with action or dialogue rather than exposition.")
    if score < 70:
        suggestions.append("Add sensory details to immerse the reader immediately.")
    if score < 80:
        suggestions.append("Consider shortening your opening sentence for more impact.")
    return suggestions


def _hook_feedback(score: float) -> str:
    if score >= 80:
        return "Powerful opening hook that grabs attention immediately."
    if score >= 60:
        return "Decent hook. Could be more compelling."
    if score >= 40:
        return "Weak hook. Readers may not continue past the first paragraph."
    return "No effective hook detected. High risk of readers abandoning."


def _hook_suggestions(score: float) -> list[str]:
    suggestions = []
    if score < 50:
        suggestions.append("Open with a question, conflict, or bold statement.")
    if score < 60:
        suggestions.append("Try starting in media res (in the middle of the action).")
    if score < 70:
        suggestions.append("Add emotional tension to your opening paragraph.")
    if score < 80:
        suggestions.append("Make the opening line shorter and more punchy.")
    return suggestions


def _pacing_suggestions(score: float) -> list[str]:
    suggestions = []
    if score < 50:
        suggestions.append("Vary paragraph lengths to create rhythm.")
    if score < 60:
        suggestions.append("Mix dialogue with narrative for better engagement.")
    if score < 70:
        suggestions.append("Use shorter paragraphs to build tension.")
    return suggestions


def _toc_feedback(score: float, titles: list[str]) -> str:
    if not titles:
        return "No chapter titles provided for TOC analysis."
    if score >= 80:
        return "Excellent chapter titles that build curiosity."
    if score >= 60:
        return "Good chapter structure. Consider more descriptive titles."
    return "Chapter titles need improvement to attract browsers."


def _toc_suggestions(score: float, titles: list[str]) -> list[str]:
    suggestions = []
    if not titles:
        suggestions.append("Provide chapter titles for a complete Look Inside analysis.")
        return suggestions
    if score < 60:
        suggestions.append("Replace generic 'Chapter N' titles with descriptive, intriguing names.")
    if score < 70:
        suggestions.append("Add curiosity-inducing words to chapter titles.")
    if score < 80:
        suggestions.append("Ensure chapter titles hint at content without spoiling.")
    return suggestions
