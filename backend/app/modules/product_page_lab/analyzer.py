"""Listing analysis engine for the Product Page Conversion Lab.

Provides scoring and recommendations for title, blurb, keywords,
category fit, and pricing of Amazon book listings.
"""

from __future__ import annotations

import re

from app.modules.product_page_lab.schemas import (
    BlurbAnalysis,
    CategoryAnalysis,
    KeywordAnalysis,
    ListingAnalysis,
    PriceAnalysis,
    Recommendation,
    TitleAnalysis,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

POWER_WORDS = [
    "secret",
    "discover",
    "ultimate",
    "proven",
    "exclusive",
    "shocking",
    "revealed",
    "breakthrough",
    "essential",
    "powerful",
    "untold",
    "compelling",
    "gripping",
    "riveting",
    "unforgettable",
    "masterpiece",
    "bestselling",
    "award-winning",
    "captivating",
    "thrilling",
    "stunning",
    "epic",
    "extraordinary",
    "remarkable",
    "incredible",
    "magnificent",
    "breathtaking",
    "spellbinding",
    "unputdownable",
    "heart-pounding",
]

CTA_PHRASES = [
    "buy now",
    "get your copy",
    "order today",
    "download now",
    "read now",
    "grab your copy",
    "click",
    "scroll up",
    "add to cart",
    "one-click",
    "don't miss",
    "start reading",
    "available now",
    "get it now",
]

EMOTIONAL_WORDS = [
    "love",
    "hate",
    "fear",
    "joy",
    "hope",
    "despair",
    "passion",
    "rage",
    "betrayal",
    "trust",
    "loss",
    "desire",
    "revenge",
    "redemption",
    "sacrifice",
    "courage",
    "haunting",
    "heartwarming",
    "devastating",
    "inspiring",
    "terrifying",
    "exhilarating",
    "poignant",
    "bittersweet",
]

# Genre average prices (ebook)
GENRE_AVG_PRICES: dict[str, float] = {
    "romance": 3.99,
    "thriller": 4.99,
    "mystery": 4.99,
    "fantasy": 4.99,
    "science_fiction": 4.99,
    "literary_fiction": 5.99,
    "non_fiction": 6.99,
    "self_help": 5.99,
    "memoir": 5.99,
    "horror": 3.99,
    "young_adult": 3.99,
    "children": 2.99,
    "historical_fiction": 4.99,
    "other": 4.99,
}

OPTIMAL_TITLE_LENGTH = (40, 80)
OPTIMAL_BLURB_WORD_COUNT = (100, 300)
MOBILE_TITLE_CHAR_LIMIT = 60
MOBILE_BLURB_FOLD_CHARS = 200


# ---------------------------------------------------------------------------
# Title analysis
# ---------------------------------------------------------------------------


def analyze_title(
    title: str,
    target_keywords: list[str] | None = None,
) -> TitleAnalysis:
    """Analyze a listing title for conversion optimization."""
    target_keywords = target_keywords or []
    issues: list[str] = []
    score = 100.0

    title_lower = title.lower()
    length = len(title)

    # Length check
    if length < OPTIMAL_TITLE_LENGTH[0]:
        penalty = min(20, (OPTIMAL_TITLE_LENGTH[0] - length) * 0.5)
        score -= penalty
        issues.append(
            f"Title is short ({length} chars). Aim for {OPTIMAL_TITLE_LENGTH[0]}-{OPTIMAL_TITLE_LENGTH[1]} characters."
        )
    elif length > OPTIMAL_TITLE_LENGTH[1]:
        penalty = min(15, (length - OPTIMAL_TITLE_LENGTH[1]) * 0.2)
        score -= penalty
        issues.append(
            f"Title is long ({length} chars). Aim for {OPTIMAL_TITLE_LENGTH[0]}-{OPTIMAL_TITLE_LENGTH[1]} characters."
        )

    # Keyword presence
    keyword_matches = [kw for kw in target_keywords if kw.lower() in title_lower]
    has_keywords = len(keyword_matches) > 0
    if target_keywords and not has_keywords:
        score -= 15
        issues.append("No target keywords found in title.")

    # Power words
    found_power_words = [pw for pw in POWER_WORDS if pw in title_lower]

    if not found_power_words:
        score -= 10
        issues.append("No power words detected. Consider adding compelling adjectives.")

    # Check for all-caps abuse
    words = title.split()
    caps_words = [w for w in words if w.isupper() and len(w) > 2]
    if len(caps_words) > 2:
        score -= 10
        issues.append("Excessive ALL CAPS words may reduce trust.")

    # Check for special characters abuse
    special_count = len(re.findall(r"[!@#$%^&*(){}|<>]", title))
    if special_count > 3:
        score -= 5
        issues.append("Too many special characters in title.")

    # Colon / subtitle pattern (positive signal)
    if ":" in title or " - " in title:
        score += 5  # Subtitle format is good for discoverability

    score = max(0, min(100, score))

    return TitleAnalysis(
        score=round(score, 1),
        length=length,
        has_keywords=has_keywords,
        keyword_matches=keyword_matches,
        power_words=found_power_words,
        issues=issues,
    )


# ---------------------------------------------------------------------------
# Blurb analysis
# ---------------------------------------------------------------------------


def analyze_blurb(blurb: str) -> BlurbAnalysis:
    """Analyze a listing blurb/description for conversion optimization."""
    issues: list[str] = []
    score = 100.0

    blurb_lower = blurb.lower()
    words = blurb.split()
    word_count = len(words)

    # Word count
    if word_count < OPTIMAL_BLURB_WORD_COUNT[0]:
        penalty = min(20, (OPTIMAL_BLURB_WORD_COUNT[0] - word_count) * 0.2)
        score -= penalty
        issues.append(
            f"Blurb is short ({word_count} words). Aim for {OPTIMAL_BLURB_WORD_COUNT[0]}-{OPTIMAL_BLURB_WORD_COUNT[1]} words."
        )
    elif word_count > OPTIMAL_BLURB_WORD_COUNT[1]:
        penalty = min(15, (word_count - OPTIMAL_BLURB_WORD_COUNT[1]) * 0.05)
        score -= penalty
        issues.append(f"Blurb is long ({word_count} words). Consider trimming to {OPTIMAL_BLURB_WORD_COUNT[1]} words.")

    # Hook detection: first sentence should be compelling
    first_sentence = _extract_first_sentence(blurb)
    has_hook = _has_hook(first_sentence)
    if not has_hook:
        score -= 15
        issues.append("First sentence lacks a strong hook. Open with a question, bold claim, or emotional statement.")

    # Bullet points / formatting
    has_bullet_points = bool(re.search(r"(?:^|\n)\s*[*\-\u2022]\s", blurb))
    if not has_bullet_points:
        score -= 5
        issues.append("Consider using bullet points to highlight key selling points.")

    # CTA detection
    has_cta = any(cta in blurb_lower for cta in CTA_PHRASES)
    if not has_cta:
        score -= 10
        issues.append("No call-to-action detected. End with a compelling CTA.")

    # HTML formatting
    has_html = bool(re.search(r"<(b|i|em|strong|br|h[1-6]|ul|li|p)\b", blurb, re.IGNORECASE))
    if not has_html:
        score -= 5
        issues.append("No HTML formatting detected. Use <b>, <i>, <br> for visual appeal on Amazon.")

    # Readability (simplified Flesch-Kincaid approximation)
    readability_grade = _calculate_readability(blurb)
    if readability_grade > 12:
        score -= 10
        issues.append(f"Readability grade {readability_grade:.1f} is too high. Aim for grade 6-8.")
    elif readability_grade > 10:
        score -= 5
        issues.append(f"Readability grade {readability_grade:.1f} is slightly high. Aim for grade 6-8.")

    # Emotional words
    found_emotional = [ew for ew in EMOTIONAL_WORDS if ew in blurb_lower]
    if not found_emotional:
        score -= 5
        issues.append("No emotional trigger words detected. Add words that evoke feelings.")

    score = max(0, min(100, score))

    return BlurbAnalysis(
        score=round(score, 1),
        word_count=word_count,
        has_hook=has_hook,
        has_bullet_points=has_bullet_points,
        has_cta=has_cta,
        has_html_formatting=has_html,
        readability_grade=round(readability_grade, 1),
        emotional_words=found_emotional,
        issues=issues,
    )


# ---------------------------------------------------------------------------
# Keyword analysis
# ---------------------------------------------------------------------------


def analyze_keywords(
    text: str,
    target_keywords: list[str] | None = None,
    genre: str | None = None,
) -> KeywordAnalysis:
    """Analyze keyword usage across listing text."""
    target_keywords = target_keywords or []
    issues: list[str] = []
    score = 70.0  # Start at baseline

    text_lower = text.lower()
    total_words = len(text.split())

    # Find present keywords
    keywords_found = [kw for kw in target_keywords if kw.lower() in text_lower]

    # Keyword density
    keyword_occurrences = sum(text_lower.count(kw.lower()) for kw in target_keywords) if target_keywords else 0
    keyword_density = (keyword_occurrences / max(total_words, 1)) * 100

    # Score based on found keywords
    if target_keywords:
        found_ratio = len(keywords_found) / len(target_keywords)
        score += found_ratio * 20
    else:
        score += 10  # No target keywords specified, neutral

    # Check for keyword stuffing
    over_stuffed = keyword_density > 5.0
    if over_stuffed:
        score -= 15
        issues.append(f"Keyword density is too high ({keyword_density:.1f}%). Aim for 1-3%.")

    # Determine missing high-value keywords
    missing = [kw for kw in target_keywords if kw.lower() not in text_lower]

    if missing:
        penalty = min(15, len(missing) * 3)
        score -= penalty

    score = max(0, min(100, score))

    return KeywordAnalysis(
        score=round(score, 1),
        keywords_found=keywords_found,
        keyword_density=round(keyword_density, 2),
        missing_high_value_keywords=missing,
        over_stuffed=over_stuffed,
    )


# ---------------------------------------------------------------------------
# Category analysis
# ---------------------------------------------------------------------------


def analyze_category(
    current_categories: list[str] | None = None,
    genre: str | None = None,
) -> CategoryAnalysis:
    """Analyze category selection for the listing."""
    current_categories = current_categories or []
    score = 50.0  # baseline without detailed category data

    suggested_categories: list[str] = []
    rank_potential = None

    if current_categories:
        score += 20  # Having categories is positive
        if len(current_categories) >= 2:
            score += 10  # Using multiple categories
    else:
        score -= 10

    # Genre-based suggestions
    genre_category_map: dict[str, list[str]] = {
        "romance": [
            "Kindle Store > Kindle eBooks > Romance",
            "Books > Romance > Contemporary",
        ],
        "thriller": [
            "Kindle Store > Kindle eBooks > Mystery, Thriller & Suspense > Thrillers",
            "Books > Mystery, Thriller & Suspense",
        ],
        "mystery": [
            "Kindle Store > Kindle eBooks > Mystery, Thriller & Suspense > Mystery",
            "Books > Mystery, Thriller & Suspense > Mystery",
        ],
        "fantasy": [
            "Kindle Store > Kindle eBooks > Science Fiction & Fantasy > Fantasy",
            "Books > Science Fiction & Fantasy > Fantasy",
        ],
        "science_fiction": [
            "Kindle Store > Kindle eBooks > Science Fiction & Fantasy > Science Fiction",
            "Books > Science Fiction & Fantasy > Science Fiction",
        ],
        "non_fiction": [
            "Kindle Store > Kindle eBooks > Nonfiction",
            "Books > Nonfiction",
        ],
        "self_help": [
            "Kindle Store > Kindle eBooks > Self-Help",
            "Books > Self-Help",
        ],
    }

    if genre and genre in genre_category_map:
        suggested_categories = genre_category_map[genre]
        rank_potential = "high" if len(current_categories) < 2 else "moderate"

    score = max(0, min(100, score))

    return CategoryAnalysis(
        score=round(score, 1),
        current_categories=current_categories,
        suggested_categories=suggested_categories,
        category_rank_potential=rank_potential,
    )


# ---------------------------------------------------------------------------
# Price analysis
# ---------------------------------------------------------------------------


def analyze_price(
    current_price: float | None = None,
    genre: str | None = None,
) -> PriceAnalysis:
    """Analyze pricing for the listing."""
    issues: list[str] = []
    score = 70.0

    genre_avg = GENRE_AVG_PRICES.get(genre or "other", 4.99)

    if current_price is not None:
        # Check if price is in the sweet spot
        low_bound = genre_avg * 0.5
        high_bound = genre_avg * 2.0

        if current_price < 0.99:
            score -= 20
            issues.append("Price below $0.99 disqualifies for 70% royalty on KDP.")
        elif current_price < low_bound:
            score -= 10
            issues.append(f"Price ${current_price:.2f} is significantly below genre average ${genre_avg:.2f}.")
        elif current_price > high_bound:
            score -= 15
            issues.append(f"Price ${current_price:.2f} is well above genre average ${genre_avg:.2f}.")
        elif current_price > 9.99:
            score -= 10
            issues.append("Price above $9.99 drops KDP royalty from 70% to 35%.")
        else:
            score += 15  # In the sweet spot

        suggested_range = f"${max(0.99, genre_avg * 0.7):.2f} - ${min(9.99, genre_avg * 1.5):.2f}"
    else:
        score = 50.0  # Can't score without a price
        issues.append("No price data available for analysis.")
        suggested_range = f"${genre_avg:.2f} (genre average)"

    score = max(0, min(100, score))

    return PriceAnalysis(
        score=round(score, 1),
        current_price=current_price,
        genre_avg_price=genre_avg,
        suggested_range=suggested_range,
        issues=issues,
    )


# ---------------------------------------------------------------------------
# Full listing analysis
# ---------------------------------------------------------------------------


def analyze_listing(
    title: str = "",
    blurb: str = "",
    keywords: list[str] | None = None,
    categories: list[str] | None = None,
    price: float | None = None,
    genre: str | None = None,
    asin: str | None = None,
) -> ListingAnalysis:
    """Run full listing analysis and produce a consolidated report."""
    keywords = keywords or []

    title_result = analyze_title(title, target_keywords=keywords)
    blurb_result = analyze_blurb(blurb)

    # Combine title + blurb text for keyword analysis
    full_text = f"{title} {blurb}"
    keyword_result = analyze_keywords(full_text, target_keywords=keywords, genre=genre)

    category_result = analyze_category(current_categories=categories, genre=genre)
    price_result = analyze_price(current_price=price, genre=genre)

    # Weighted overall score
    overall = (
        title_result.score * 0.20
        + blurb_result.score * 0.30
        + keyword_result.score * 0.20
        + category_result.score * 0.15
        + price_result.score * 0.15
    )

    # Collect recommendations
    recommendations: list[Recommendation] = []

    for issue in title_result.issues:
        recommendations.append(
            Recommendation(
                area="title",
                severity=_issue_severity(title_result.score),
                message=issue,
                suggestion=_generate_suggestion("title", issue),
            )
        )

    for issue in blurb_result.issues:
        recommendations.append(
            Recommendation(
                area="blurb",
                severity=_issue_severity(blurb_result.score),
                message=issue,
                suggestion=_generate_suggestion("blurb", issue),
            )
        )

    for kw in keyword_result.missing_high_value_keywords:
        recommendations.append(
            Recommendation(
                area="keywords",
                severity="warning",
                message=f"Missing keyword: '{kw}'",
                suggestion=f"Incorporate '{kw}' naturally into your title or blurb.",
            )
        )

    if keyword_result.over_stuffed:
        recommendations.append(
            Recommendation(
                area="keywords",
                severity="warning",
                message="Keyword stuffing detected",
                suggestion="Reduce keyword repetition to maintain natural readability.",
            )
        )

    for issue in price_result.issues:
        recommendations.append(
            Recommendation(
                area="price",
                severity=_issue_severity(price_result.score),
                message=issue,
                suggestion=_generate_suggestion("price", issue),
            )
        )

    return ListingAnalysis(
        asin=asin,
        title=title if title else None,
        title_score=title_result.score,
        blurb_score=blurb_result.score,
        keyword_score=keyword_result.score,
        category_score=category_result.score,
        price_score=price_result.score,
        overall_score=round(overall, 1),
        title_analysis=title_result,
        blurb_analysis=blurb_result,
        keyword_analysis=keyword_result,
        category_analysis=category_result,
        price_analysis=price_result,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_first_sentence(text: str) -> str:
    """Extract the first sentence from text."""
    match = re.match(r"^(.+?[.!?])\s", text)
    if match:
        return match.group(1)
    # Fallback: take first 100 chars
    return text[:100]


def _has_hook(sentence: str) -> bool:
    """Determine if a sentence qualifies as a strong hook."""
    s = sentence.strip().lower()
    # Question hook
    if s.endswith("?"):
        return True
    # Bold / emphatic statement
    if s.endswith("!"):
        return True
    # Starts with trigger words
    hook_starters = [
        "what if",
        "imagine",
        "discover",
        "when",
        "in a world",
        "everything changed",
        "nothing prepared",
        "she never expected",
        "he thought",
        "they said",
        "one moment",
        "the day",
    ]
    if any(s.startswith(starter) for starter in hook_starters):
        return True
    # Contains emotional / power words in first sentence
    for word in EMOTIONAL_WORDS[:10] + POWER_WORDS[:10]:
        if word in s:
            return True
    return False


def _calculate_readability(text: str) -> float:
    """Simplified Flesch-Kincaid grade level approximation."""
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    num_sentences = max(len(sentences), 1)

    words = text.split()
    num_words = max(len(words), 1)

    # Approximate syllable count
    num_syllables = sum(_count_syllables(w) for w in words)

    # Flesch-Kincaid Grade Level formula
    grade = 0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59
    return max(0, grade)


def _count_syllables(word: str) -> int:
    """Rough syllable count for English words."""
    word = word.lower().strip(".,!?;:'\"")
    if not word:
        return 1
    count = 0
    vowels = "aeiouy"
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    # Handle silent 'e'
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def _issue_severity(score: float) -> str:
    """Determine severity based on component score."""
    if score < 40:
        return "critical"
    if score < 70:
        return "warning"
    return "info"


def _generate_suggestion(area: str, issue: str) -> str:
    """Generate a brief suggestion for an issue."""
    suggestions_map: dict[str, str] = {
        "title": "Review and optimize your title following Amazon best practices.",
        "blurb": "Revise your blurb to include hooks, formatting, and a clear CTA.",
        "keywords": "Research high-value keywords using Publisher Rocket or similar tools.",
        "price": "Review genre pricing trends and adjust to maximize royalties.",
    }
    return suggestions_map.get(area, "Review this area for potential improvements.")
