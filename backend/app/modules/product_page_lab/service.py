"""Service layer for the Product Page Conversion Lab.

Orchestrates listing analysis, blurb generation, A/B test management,
Look Inside analysis, and mobile checks.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    ABTestStatus,
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


# ---------------------------------------------------------------------------
# Listing analysis
# ---------------------------------------------------------------------------

async def analyze_amazon_listing(
    request: ListingAnalyzeRequest,
    db: AsyncSession,
) -> ListingAnalysis:
    """Analyze an Amazon listing by ASIN or URL.

    In a production system this would scrape or use the Amazon Product
    Advertising API. For now we accept the listing data inline or
    return a scaffold analysis when only an ASIN/URL is provided.
    """
    asin = request.asin
    if not asin and request.url:
        asin = _extract_asin_from_url(request.url)

    # In production, we would fetch listing data from Amazon here.
    # For the MVP we return a scaffold analysis with placeholder data.
    analysis = analyze_listing(
        title="",
        blurb="",
        keywords=[],
        categories=[],
        price=None,
        genre=None,
        asin=asin,
    )

    return analysis


async def analyze_listing_with_data(
    title: str,
    blurb: str,
    keywords: Optional[list[str]] = None,
    categories: Optional[list[str]] = None,
    price: Optional[float] = None,
    genre: Optional[str] = None,
    asin: Optional[str] = None,
) -> ListingAnalysis:
    """Analyze a listing with provided data (no scraping needed)."""
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
    except Exception:
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
    now = datetime.utcnow()

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

    return _ab_test_to_response(ab_test)


async def get_ab_test(
    test_id: UUID,
    db: AsyncSession,
) -> Optional[ABTestResponse]:
    """Get A/B test by ID with results."""
    result = await db.execute(
        select(ABTest).where(
            ABTest.id == test_id,
            ABTest.deleted_at.is_(None),
        )
    )
    ab_test = result.scalar_one_or_none()
    if ab_test is None:
        return None

    return _ab_test_to_response(ab_test)


async def start_ab_test(
    test_id: UUID,
    db: AsyncSession,
) -> Optional[ABTestResponse]:
    """Start an A/B test."""
    result = await db.execute(
        select(ABTest).where(
            ABTest.id == test_id,
            ABTest.deleted_at.is_(None),
        )
    )
    ab_test = result.scalar_one_or_none()
    if ab_test is None:
        return None

    ab_test.status = ABTestStatus.RUNNING
    ab_test.started_at = datetime.utcnow()
    await db.flush()

    return _ab_test_to_response(ab_test)


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
    sections.append(LookInsideSection(
        section="first_page",
        score=first_page_score,
        feedback=_first_page_feedback(first_page_score),
        suggestions=_first_page_suggestions(first_page, first_page_score),
    ))

    # --- Hook strength ---
    first_paragraph = _extract_first_paragraph(preview_text)
    hook_score = _score_hook(first_paragraph, genre)
    sections.append(LookInsideSection(
        section="opening_hook",
        score=hook_score,
        feedback=_hook_feedback(hook_score),
        suggestions=_hook_suggestions(hook_score),
    ))

    # --- Pacing ---
    pacing_score = _score_pacing(preview_text)
    sections.append(LookInsideSection(
        section="pacing",
        score=pacing_score,
        feedback=f"Pacing score: {pacing_score}/100.",
        suggestions=_pacing_suggestions(pacing_score),
    ))

    # --- Table of contents ---
    toc_score = _score_toc(chapter_titles)
    sections.append(LookInsideSection(
        section="table_of_contents",
        score=toc_score,
        feedback=_toc_feedback(toc_score, chapter_titles),
        suggestions=_toc_suggestions(toc_score, chapter_titles),
    ))

    # Overall score (weighted)
    overall = (
        first_page_score * 0.30
        + hook_score * 0.30
        + pacing_score * 0.20
        + toc_score * 0.20
    )

    # Build recommendations from sections with low scores
    for section in sections:
        if section.score < 60:
            for suggestion in section.suggestions:
                recommendations.append(Recommendation(
                    area=f"look_inside_{section.section}",
                    severity="critical" if section.score < 40 else "warning",
                    message=section.feedback,
                    suggestion=suggestion,
                ))

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

    In production this would pull from cached analysis results.
    For now returns a placeholder.
    """
    return ConversionScores(
        book_id=book_id,
        listing_score=None,
        blurb_score=None,
        mobile_score=None,
        look_inside_score=None,
        overall_score=0.0,
        last_analyzed_at=None,
        recommendations_count=0,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_asin_from_url(url: str) -> Optional[str]:
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


def _ab_test_to_response(ab_test: ABTest) -> ABTestResponse:
    """Convert an ABTest model to response schema."""
    # Calculate CTR
    a_ctr = (
        ab_test.variant_a_clicks / ab_test.variant_a_impressions * 100
        if ab_test.variant_a_impressions > 0
        else 0.0
    )
    b_ctr = (
        ab_test.variant_b_clicks / ab_test.variant_b_impressions * 100
        if ab_test.variant_b_impressions > 0
        else 0.0
    )

    # Determine winner if test is completed
    winner = None
    confidence = None
    if ab_test.status == ABTestStatus.COMPLETED:
        if a_ctr > b_ctr:
            winner = "A"
        elif b_ctr > a_ctr:
            winner = "B"
        else:
            winner = "tie"
        # Simplified confidence (in production use proper statistical testing)
        total_impressions = ab_test.variant_a_impressions + ab_test.variant_b_impressions
        confidence = min(95.0, 50.0 + (total_impressions / 100) * 5)

    return ABTestResponse(
        id=ab_test.id,
        book_id=ab_test.book_id,
        name=ab_test.name,
        status=ab_test.status,
        variant_a=ABTestVariantResult(
            variant_label="A",
            content=ab_test.variant_a_content,
            impressions=ab_test.variant_a_impressions,
            clicks=ab_test.variant_a_clicks,
            click_through_rate=round(a_ctr, 2),
            conversion_rate=0.0,
            estimated_score=0.0,
        ),
        variant_b=ABTestVariantResult(
            variant_label="B",
            content=ab_test.variant_b_content,
            impressions=ab_test.variant_b_impressions,
            clicks=ab_test.variant_b_clicks,
            click_through_rate=round(b_ctr, 2),
            conversion_rate=0.0,
            estimated_score=0.0,
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
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
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
    short_paras = sum(1 for l in lengths if l <= 15)
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
    generic_count = sum(
        1 for t in chapter_titles
        if re.match(r"^chapter\s+\d+$", t.lower().strip())
    )
    descriptive_ratio = 1 - (generic_count / max(len(chapter_titles), 1))
    score += descriptive_ratio * 20

    # Intriguing titles (contain interesting words)
    intriguing_words = ["secret", "dark", "last", "first", "blood", "fire", "night", "truth"]
    intriguing_count = sum(
        1 for t in chapter_titles
        if any(w in t.lower() for w in intriguing_words)
    )
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
