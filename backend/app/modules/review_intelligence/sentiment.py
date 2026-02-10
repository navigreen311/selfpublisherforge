"""NLP sentiment analysis: positive/negative/neutral classification,
theme extraction, complaint categorization (AI-powered via LLM).
"""

import json
import logging
from typing import Optional

from app.config import get_settings
from app.modules.review_intelligence.schemas import (
    SentimentAnalysisResult,
    SentimentLabel,
    ThemeItem,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# --- Keyword-based fallback for when LLM is unavailable ---

POSITIVE_KEYWORDS = {
    "love",
    "loved",
    "amazing",
    "excellent",
    "fantastic",
    "great",
    "wonderful",
    "brilliant",
    "outstanding",
    "superb",
    "perfect",
    "best",
    "enjoyed",
    "enjoyable",
    "recommend",
    "recommended",
    "masterpiece",
    "beautiful",
    "captivating",
    "engaging",
    "page-turner",
    "couldn't put it down",
    "must-read",
    "well-written",
    "compelling",
    "riveting",
    "delightful",
    "heartwarming",
    "thrilling",
    "impressive",
}

NEGATIVE_KEYWORDS = {
    "terrible",
    "awful",
    "horrible",
    "boring",
    "waste",
    "disappointed",
    "disappointing",
    "poorly",
    "worst",
    "bad",
    "hate",
    "hated",
    "confusing",
    "slow",
    "dull",
    "flat",
    "mediocre",
    "predictable",
    "unoriginal",
    "cliche",
    "overrated",
    "poorly-written",
    "errors",
    "typos",
    "editing",
    "unrealistic",
    "frustrating",
    "painful",
    "struggled",
    "dnf",
}

THEME_KEYWORDS = {
    "plot": ["plot", "story", "storyline", "narrative", "arc", "twist"],
    "characters": [
        "character",
        "characters",
        "protagonist",
        "hero",
        "heroine",
        "villain",
    ],
    "writing_style": [
        "writing",
        "prose",
        "style",
        "voice",
        "tone",
        "language",
        "dialogue",
    ],
    "pacing": ["pacing", "pace", "slow", "fast", "rushed", "dragged"],
    "world_building": ["world", "setting", "world-building", "worldbuilding", "atmosphere"],
    "editing": ["editing", "typos", "errors", "grammar", "formatting", "proofread"],
    "emotional_impact": [
        "emotional",
        "moving",
        "touching",
        "heartbreaking",
        "tears",
        "laughed",
        "cried",
    ],
    "value": ["price", "value", "worth", "money", "expensive", "cheap", "free"],
    "ending": ["ending", "conclusion", "finale", "resolution", "cliffhanger"],
    "series": ["series", "sequel", "next book", "continuation", "book 2", "book 3"],
}


def _keyword_sentiment(text: str) -> SentimentAnalysisResult:
    """Fallback keyword-based sentiment analysis."""
    text_lower = text.lower()
    words = set(text_lower.split())

    pos_count = len(words & POSITIVE_KEYWORDS)
    neg_count = len(words & NEGATIVE_KEYWORDS)
    total = pos_count + neg_count

    if total == 0:
        sentiment = SentimentLabel.NEUTRAL
        score = 0.0
    elif pos_count > neg_count * 2:
        sentiment = SentimentLabel.POSITIVE
        score = min(pos_count / max(total, 1), 1.0)
    elif neg_count > pos_count * 2:
        sentiment = SentimentLabel.NEGATIVE
        score = -min(neg_count / max(total, 1), 1.0)
    elif pos_count > 0 and neg_count > 0:
        sentiment = SentimentLabel.MIXED
        score = (pos_count - neg_count) / max(total, 1)
    elif pos_count > neg_count:
        sentiment = SentimentLabel.POSITIVE
        score = 0.5
    elif neg_count > pos_count:
        sentiment = SentimentLabel.NEGATIVE
        score = -0.5
    else:
        sentiment = SentimentLabel.NEUTRAL
        score = 0.0

    # Extract themes
    themes = []
    for theme_name, keywords in THEME_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            themes.append(theme_name)

    # Extract simple complaints and praise
    complaints = []
    praise = []

    if neg_count > 0:
        for kw in NEGATIVE_KEYWORDS:
            if kw in text_lower:
                complaints.append(kw)
    if pos_count > 0:
        for kw in POSITIVE_KEYWORDS:
            if kw in text_lower:
                praise.append(kw)

    return SentimentAnalysisResult(
        sentiment=sentiment,
        score=round(score, 3),
        themes=themes[:5],
        key_phrases=[],
        complaints=complaints[:5],
        praise=praise[:5],
    )


async def analyze_sentiment_llm(
    review_text: str, star_rating: Optional[float] = None
) -> SentimentAnalysisResult:
    """Analyze sentiment using LLM (with keyword fallback).

    Attempts to call Anthropic API for sophisticated sentiment analysis.
    Falls back to keyword-based analysis if LLM is unavailable.
    """
    if not review_text or not review_text.strip():
        return SentimentAnalysisResult(
            sentiment=SentimentLabel.NEUTRAL,
            score=0.0,
            themes=[],
            key_phrases=[],
            complaints=[],
            praise=[],
        )

    # Try LLM-based analysis
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        rating_context = (
            f"\nStar rating: {star_rating}/5" if star_rating is not None else ""
        )

        prompt = f"""Analyze the sentiment of this book review. Return a JSON object with these fields:
- "sentiment": one of "positive", "negative", "neutral", "mixed"
- "score": float from -1.0 (most negative) to 1.0 (most positive)
- "themes": list of up to 5 theme strings (e.g. "plot", "characters", "writing_style")
- "key_phrases": list of up to 5 notable phrases from the review
- "complaints": list of up to 5 specific complaints
- "praise": list of up to 5 specific praise points

Review:{rating_context}
{review_text}

Return ONLY valid JSON, no other text."""

        message = await client.messages.create(
            model=settings.DEFAULT_LLM_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()
        # Parse JSON from LLM response
        result_data = json.loads(response_text)

        return SentimentAnalysisResult(
            sentiment=SentimentLabel(result_data.get("sentiment", "neutral")),
            score=max(-1.0, min(1.0, float(result_data.get("score", 0.0)))),
            themes=result_data.get("themes", [])[:5],
            key_phrases=result_data.get("key_phrases", [])[:5],
            complaints=result_data.get("complaints", [])[:5],
            praise=result_data.get("praise", [])[:5],
        )
    except ImportError:
        logger.info("Anthropic SDK not available, using keyword-based sentiment analysis")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning("LLM sentiment response parsing failed, falling back to keywords: %s", e)
    except OSError as e:
        logger.warning("LLM sentiment network request failed, falling back to keywords: %s", e)

    return _keyword_sentiment(review_text)


async def analyze_sentiment_batch(
    reviews: list[dict],
) -> list[SentimentAnalysisResult]:
    """Analyze sentiment for a batch of reviews.

    Args:
        reviews: List of dicts with 'text' and optional 'star_rating' keys.

    Returns:
        List of SentimentAnalysisResult, one per review.
    """
    results = []
    for review in reviews:
        text = review.get("text", review.get("body", ""))
        rating = review.get("star_rating")
        result = await analyze_sentiment_llm(text, rating)
        results.append(result)
    return results


def extract_themes_from_results(
    results: list[SentimentAnalysisResult],
) -> list[ThemeItem]:
    """Aggregate theme data from multiple sentiment analysis results."""
    theme_counts: dict[str, dict] = {}

    for result in results:
        for theme in result.themes:
            theme_lower = theme.lower().replace(" ", "_")
            if theme_lower not in theme_counts:
                theme_counts[theme_lower] = {
                    "count": 0,
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "quotes": [],
                }
            theme_counts[theme_lower]["count"] += 1
            sent = result.sentiment.value
            if sent in ("positive", "negative", "neutral"):
                theme_counts[theme_lower][sent] += 1
            else:
                theme_counts[theme_lower]["neutral"] += 1

    theme_items = []
    for theme_name, data in sorted(
        theme_counts.items(), key=lambda x: x[1]["count"], reverse=True
    ):
        # Determine dominant sentiment for theme
        if data["positive"] > data["negative"] and data["positive"] > data["neutral"]:
            dominant = SentimentLabel.POSITIVE
        elif data["negative"] > data["positive"] and data["negative"] > data["neutral"]:
            dominant = SentimentLabel.NEGATIVE
        else:
            dominant = SentimentLabel.NEUTRAL

        theme_items.append(
            ThemeItem(
                theme=theme_name,
                count=data["count"],
                sentiment=dominant,
                example_quotes=data["quotes"][:3],
            )
        )

    return theme_items
