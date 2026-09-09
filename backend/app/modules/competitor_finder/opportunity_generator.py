"""AI-powered opportunity blueprint generator.

Given weakness data from review analysis, generates a comprehensive blueprint
for how to write a better competing book.
"""

from __future__ import annotations

import logging

from app.config import get_settings
from app.modules.competitor_finder.schemas import (
    ContentStrategy,
    PricingStrategy,
    Severity,
    WeaknessCategory,
    WeaknessSignalCreate,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class OpportunityBlueprintData:
    """Data container for a generated opportunity blueprint."""

    def __init__(
        self,
        title_suggestions: list[str] | None = None,
        content_strategy: dict | None = None,
        format_recommendations: list[str] | None = None,
        pricing_strategy: dict | None = None,
        differentiators: list[str] | None = None,
        target_audience: str | None = None,
        estimated_opportunity_score: float | None = None,
        full_blueprint: dict | None = None,
    ):
        self.title_suggestions = title_suggestions or []
        self.content_strategy = content_strategy or {}
        self.format_recommendations = format_recommendations or []
        self.pricing_strategy = pricing_strategy or {}
        self.differentiators = differentiators or []
        self.target_audience = target_audience
        self.estimated_opportunity_score = estimated_opportunity_score
        self.full_blueprint = full_blueprint or {}


async def generate_opportunity_blueprint(
    weaknesses: list[WeaknessSignalCreate],
    book_title: str = "",
    book_category: str = "",
    book_price: float | None = None,
    book_rating: float | None = None,
) -> OpportunityBlueprintData:
    """Generate an opportunity blueprint from weakness signals.

    Uses a rule-based engine with optional AI enhancement.
    """
    # Start with rule-based generation
    blueprint = _generate_rule_based_blueprint(
        weaknesses=weaknesses,
        book_title=book_title,
        book_category=book_category,
        book_price=book_price,
        book_rating=book_rating,
    )

    # Attempt AI enhancement
    try:
        enhanced = await _enhance_with_ai(
            blueprint=blueprint,
            weaknesses=weaknesses,
            book_title=book_title,
            book_category=book_category,
        )
        if enhanced:
            return enhanced
    except (RuntimeError, ValueError, OSError) as e:
        logger.warning(
            "AI blueprint enhancement failed, using rule-based blueprint: %s",
            e,
            exc_info=True,
        )

    return blueprint


def _generate_rule_based_blueprint(
    weaknesses: list[WeaknessSignalCreate],
    book_title: str,
    book_category: str,
    book_price: float | None,
    book_rating: float | None,
) -> OpportunityBlueprintData:
    """Generate blueprint using rule-based heuristics from weakness data."""
    title_suggestions = _generate_title_suggestions(weaknesses, book_title, book_category)
    content_strategy = _build_content_strategy(weaknesses)
    format_recs = _build_format_recommendations(weaknesses)
    pricing = _build_pricing_strategy(weaknesses, book_price)
    differentiators = _build_differentiators(weaknesses)
    target_audience = _infer_target_audience(weaknesses, book_category)
    opportunity_score = _calculate_opportunity_score(weaknesses, book_rating)

    full_blueprint = {
        "competitor_book": book_title,
        "category": book_category,
        "opportunity_score": opportunity_score,
        "strategy_summary": (
            f"Based on analysis of {len(weaknesses)} weakness signals, "
            f"there is a {'strong' if opportunity_score > 0.7 else 'moderate' if opportunity_score > 0.4 else 'limited'} "
            f"opportunity to create a superior competing book."
        ),
        "key_actions": [s.suggestion for s in weaknesses[:5] if s.suggestion],
    }

    return OpportunityBlueprintData(
        title_suggestions=title_suggestions,
        content_strategy=content_strategy,
        format_recommendations=format_recs,
        pricing_strategy=pricing,
        differentiators=differentiators,
        target_audience=target_audience,
        estimated_opportunity_score=opportunity_score,
        full_blueprint=full_blueprint,
    )


def _generate_title_suggestions(
    weaknesses: list[WeaknessSignalCreate],
    book_title: str,
    book_category: str,
) -> list[str]:
    """Generate title improvement suggestions based on competitor weaknesses."""
    suggestions = []

    has_content_issues = any(w.category == WeaknessCategory.CONTENT_QUALITY for w in weaknesses)
    has_coverage_gaps = any(w.category == WeaknessCategory.COVERAGE_GAPS for w in weaknesses)
    has_missing_features = any(w.category == WeaknessCategory.MISSING_FEATURES for w in weaknesses)

    if has_content_issues:
        suggestions.append(
            f"Consider a title emphasizing depth and expertise, e.g., "
            f"'The Complete/Definitive Guide to {book_category}'"
        )
    if has_coverage_gaps:
        suggestions.append(
            "Use a title that signals comprehensive coverage, e.g., " "'Everything You Need to Know About...'"
        )
    if has_missing_features:
        suggestions.append(
            "Highlight bonus materials in subtitle, e.g., " "'...with Workbook, Templates & Online Resources'"
        )

    if not suggestions:
        suggestions.append(
            f"Craft a title that clearly differentiates from '{book_title}' "
            "by emphasizing your unique value proposition."
        )

    return suggestions


def _build_content_strategy(weaknesses: list[WeaknessSignalCreate]) -> dict:
    """Build a content strategy dictionary from weakness signals."""
    key_topics: list[str] = []
    unique_angles: list[str] = []
    depth_level = "intermediate"

    content_weaknesses = [w for w in weaknesses if w.category == WeaknessCategory.CONTENT_QUALITY]
    coverage_weaknesses = [w for w in weaknesses if w.category == WeaknessCategory.COVERAGE_GAPS]

    if content_weaknesses:
        key_topics.append("In-depth, well-researched content addressing reader complaints")
        unique_angles.append("Provide original research, case studies, or expert interviews " "that competitors lack")
        # If content is shallow, go deeper
        if any("shallow" in w.signal_text.lower() for w in content_weaknesses):
            depth_level = "advanced"

    if coverage_weaknesses:
        for w in coverage_weaknesses[:3]:
            key_topics.append(f"Cover topic gap: {w.signal_text}")

    if not key_topics:
        key_topics.append("Focus on clear, actionable content with practical examples")

    return ContentStrategy(
        key_topics=key_topics,
        unique_angles=unique_angles,
        depth_level=depth_level,
        suggested_length=None,
        structure_notes="Organize with clear chapters, summaries, and actionable takeaways",
    ).model_dump()


def _build_format_recommendations(weaknesses: list[WeaknessSignalCreate]) -> list[str]:
    """Build format recommendations from format/layout weaknesses."""
    recs: list[str] = []

    format_weaknesses = [w for w in weaknesses if w.category == WeaknessCategory.FORMAT_LAYOUT]
    feature_weaknesses = [w for w in weaknesses if w.category == WeaknessCategory.MISSING_FEATURES]

    if format_weaknesses:
        recs.append("Invest in professional formatting for all platforms (Kindle, print, PDF)")
        recs.append("Include a detailed, clickable table of contents")
        recs.append("Use clear, readable fonts and generous margins")
        recs.append("Ensure all images and diagrams are high-resolution")

    if feature_weaknesses:
        for w in feature_weaknesses[:3]:
            recs.append(f"Add: {w.suggestion or w.signal_text}")

    if not recs:
        recs.append("Ensure professional formatting and cross-platform compatibility")

    return recs


def _build_pricing_strategy(weaknesses: list[WeaknessSignalCreate], current_price: float | None) -> dict:
    """Build pricing strategy based on competitor weaknesses and price."""
    pricing_weaknesses = [w for w in weaknesses if w.category == WeaknessCategory.PRICING]

    recommended_price = current_price
    rationale = "Price competitively while delivering superior value."
    bundle_suggestions: list[str] = []

    if pricing_weaknesses and current_price:
        # Competitor has pricing complaints - consider strategic pricing
        if any("expensive" in w.signal_text.lower() for w in pricing_weaknesses):
            recommended_price = round(current_price * 0.85, 2)
            rationale = (
                "Price 10-15% below the competitor to capture value-conscious readers " "who complained about pricing."
            )
        elif any("value" in w.signal_text.lower() for w in pricing_weaknesses):
            rationale = (
                "Match or slightly exceed competitor price, but ensure clear " "value proposition with bonus materials."
            )
            bundle_suggestions.append("Include bonus workbook or templates to justify price")
            bundle_suggestions.append("Offer a bundle with audiobook for added value")

    price_range_low = round((recommended_price or 9.99) * 0.8, 2)
    price_range_high = round((recommended_price or 9.99) * 1.2, 2)

    return PricingStrategy(
        recommended_price=recommended_price,
        price_range_low=price_range_low,
        price_range_high=price_range_high,
        rationale=rationale,
        bundle_suggestions=bundle_suggestions,
    ).model_dump()


def _build_differentiators(weaknesses: list[WeaknessSignalCreate]) -> list[str]:
    """Build a list of differentiators based on competitor weaknesses."""
    diffs: list[str] = []

    category_actions: dict[WeaknessCategory, str] = {
        WeaknessCategory.CONTENT_QUALITY: ("Deeper, well-researched content with original insights and expert backing"),
        WeaknessCategory.FORMAT_LAYOUT: ("Professional formatting and design across all reading platforms"),
        WeaknessCategory.MISSING_FEATURES: ("Comprehensive bonus materials (workbook, templates, online resources)"),
        WeaknessCategory.PRICING: ("Better value proposition with competitive pricing and included extras"),
        WeaknessCategory.COVERAGE_GAPS: ("Complete topic coverage addressing gaps readers identified"),
    }

    seen_categories: set[WeaknessCategory] = set()
    for w in weaknesses:
        if w.category not in seen_categories:
            seen_categories.add(w.category)
            if w.category in category_actions:
                diffs.append(category_actions[w.category])

    if not diffs:
        diffs.append("Focus on quality, completeness, and reader experience")

    return diffs


def _infer_target_audience(weaknesses: list[WeaknessSignalCreate], book_category: str) -> str:
    """Infer the target audience from weakness patterns."""
    has_shallow_complaints = any(
        w.category == WeaknessCategory.CONTENT_QUALITY
        and any(kw in w.signal_text.lower() for kw in ["shallow", "basic", "superficial"])
        for w in weaknesses
    )

    if has_shallow_complaints:
        return (
            f"Intermediate to advanced readers in {book_category} who want depth "
            "and actionable insights beyond the basics."
        )

    return (
        f"Readers in {book_category} who are looking for a comprehensive, "
        "well-organized, and professionally produced book."
    )


def _calculate_opportunity_score(weaknesses: list[WeaknessSignalCreate], book_rating: float | None) -> float:
    """Calculate an opportunity score from 0.0 to 1.0.

    Higher score means greater opportunity to create a superior competitor.
    """
    if not weaknesses:
        return 0.1

    # Factor 1: Number and severity of weaknesses (0 to 0.4)
    severity_weights = {
        Severity.CRITICAL: 4,
        Severity.HIGH: 3,
        Severity.MEDIUM: 2,
        Severity.LOW: 1,
    }
    total_severity = sum(severity_weights.get(w.severity, 1) for w in weaknesses)
    max_severity = len(weaknesses) * 4
    severity_factor = min(total_severity / max(max_severity, 1), 1.0) * 0.4

    # Factor 2: Category diversity (0 to 0.3) - weaknesses across more categories = bigger opp
    unique_categories = len(set(w.category for w in weaknesses))
    category_factor = min(unique_categories / 5.0, 1.0) * 0.3

    # Factor 3: Rating-based opportunity (0 to 0.3) - lower competitor rating = higher opp
    if book_rating is not None:
        rating_factor = max(0, (5.0 - book_rating) / 4.0) * 0.3
    else:
        rating_factor = 0.15  # Assume moderate if unknown

    score = severity_factor + category_factor + rating_factor
    return round(min(max(score, 0.0), 1.0), 4)


async def _enhance_with_ai(
    blueprint: OpportunityBlueprintData,
    weaknesses: list[WeaknessSignalCreate],
    book_title: str,
    book_category: str,
) -> OpportunityBlueprintData | None:
    """Enhance the rule-based blueprint with AI insights.

    ASSUMPTION: An LLM client will be injected at infrastructure level.
    Returns None if AI is unavailable, allowing the caller to fall back.
    """
    logger.info(
        "AI blueprint enhancement would be invoked here for '%s' with %d weaknesses",
        book_title,
        len(weaknesses),
    )
    # Return None to signal that AI enhancement was not available
    return None
