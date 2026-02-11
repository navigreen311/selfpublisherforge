"""Mobile conversion checker for Amazon book listings.

Simulates how a listing appears on mobile devices, checking for title
truncation, blurb fold point, image sizing, and other mobile-specific
conversion factors.
"""

from __future__ import annotations

from app.modules.product_page_lab.schemas import (
    MobileCheckResult,
    MobileTruncation,
    Recommendation,
)

# ---------------------------------------------------------------------------
# Device configurations
# ---------------------------------------------------------------------------

DEVICE_CONFIGS = {
    "iphone_se": {
        "name": "iPhone SE",
        "screen_width": 375,
        "title_char_limit": 50,
        "subtitle_char_limit": 40,
        "blurb_fold_chars": 180,
        "thumbnail_width": 120,
    },
    "iphone_14": {
        "name": "iPhone 14",
        "screen_width": 390,
        "title_char_limit": 55,
        "subtitle_char_limit": 45,
        "blurb_fold_chars": 200,
        "thumbnail_width": 130,
    },
    "iphone_14_pro_max": {
        "name": "iPhone 14 Pro Max",
        "screen_width": 430,
        "title_char_limit": 65,
        "subtitle_char_limit": 50,
        "blurb_fold_chars": 240,
        "thumbnail_width": 140,
    },
    "samsung_galaxy_s23": {
        "name": "Samsung Galaxy S23",
        "screen_width": 360,
        "title_char_limit": 52,
        "subtitle_char_limit": 42,
        "blurb_fold_chars": 190,
        "thumbnail_width": 125,
    },
    "pixel_7": {
        "name": "Google Pixel 7",
        "screen_width": 412,
        "title_char_limit": 60,
        "subtitle_char_limit": 48,
        "blurb_fold_chars": 220,
        "thumbnail_width": 135,
    },
}

# Default mobile configuration (average of common devices)
DEFAULT_MOBILE_CONFIG = {
    "title_char_limit": 55,
    "subtitle_char_limit": 45,
    "blurb_fold_chars": 200,
    "thumbnail_width": 130,
}

# Cover image aspect ratio for Amazon (ideal is 1.6:1 / 1600x2560)
IDEAL_COVER_RATIO = 1.6
COVER_RATIO_TOLERANCE = 0.2


# ---------------------------------------------------------------------------
# Mobile check logic
# ---------------------------------------------------------------------------

def check_mobile_display(
    title: str,
    blurb: str,
    author_name: str,
    subtitle: str | None = None,
    cover_image_url: str | None = None,
    price: float | None = None,
) -> MobileCheckResult:
    """Simulate mobile display and check for conversion issues."""
    recommendations: list[Recommendation] = []
    score = 100.0

    # --- Title truncation ---
    title_limit = DEFAULT_MOBILE_CONFIG["title_char_limit"]
    title_display = _check_truncation("title", title, title_limit)
    if title_display.is_truncated:
        score -= 15
        recommendations.append(Recommendation(
            area="mobile_title",
            severity="warning",
            message=f"Title truncated on mobile at {title_limit} chars (yours: {len(title)} chars).",
            suggestion=f"Shorten title to {title_limit} characters or ensure the most important keywords appear first.",
            current_value=title,
            recommended_value=title[:title_limit],
        ))

    # --- Subtitle truncation ---
    subtitle_display: MobileTruncation | None = None
    if subtitle:
        sub_limit = DEFAULT_MOBILE_CONFIG["subtitle_char_limit"]
        subtitle_display = _check_truncation("subtitle", subtitle, sub_limit)
        if subtitle_display.is_truncated:
            score -= 8
            recommendations.append(Recommendation(
                area="mobile_subtitle",
                severity="info",
                message=f"Subtitle truncated on mobile at {sub_limit} chars.",
                suggestion=f"Shorten subtitle to {sub_limit} characters.",
                current_value=subtitle,
                recommended_value=subtitle[:sub_limit],
            ))

    # --- Blurb fold point ---
    blurb_fold = DEFAULT_MOBILE_CONFIG["blurb_fold_chars"]
    # Strip HTML for fold calculation
    blurb_plain = _strip_html(blurb)
    blurb_above_fold = blurb_plain[:blurb_fold]
    blurb_above_fold_words = len(blurb_above_fold.split())

    if len(blurb_plain) > blurb_fold:
        # Check if the above-fold content is compelling
        if not _has_above_fold_hook(blurb_above_fold):
            score -= 15
            recommendations.append(Recommendation(
                area="mobile_blurb",
                severity="critical",
                message="Blurb above the fold lacks a compelling hook on mobile.",
                suggestion="Front-load your blurb with the most compelling hook and key value proposition.",
            ))
        else:
            score -= 5  # Still penalize slightly for being long
            recommendations.append(Recommendation(
                area="mobile_blurb",
                severity="info",
                message=f"Blurb extends below the fold ({len(blurb_plain)} chars > {blurb_fold} visible).",
                suggestion="Consider condensing your opening to keep key info above the fold.",
            ))

    # --- Cover image ---
    cover_aspect_ok = True
    cover_readable = True
    if cover_image_url:
        # We can't actually check the image, but we can flag the need for check
        recommendations.append(Recommendation(
            area="mobile_cover",
            severity="info",
            message="Cover image provided. Ensure it is readable at thumbnail size (130px wide).",
            suggestion="Use large, bold fonts on your cover. Test at 130px wide to verify readability.",
        ))
    else:
        score -= 5
        cover_readable = False
        recommendations.append(Recommendation(
            area="mobile_cover",
            severity="warning",
            message="No cover image URL provided for mobile preview check.",
            suggestion="Provide a cover image URL to check mobile thumbnail readability.",
        ))

    # --- Author name length ---
    if len(author_name) > 30:
        score -= 3
        recommendations.append(Recommendation(
            area="mobile_author",
            severity="info",
            message=f"Author name is long ({len(author_name)} chars) and may be truncated on mobile.",
            suggestion="Consider using a shorter pen name or initials for better mobile display.",
        ))

    # --- Price visibility ---
    price_visibility = "good"
    if price is not None:
        if price == 0:
            price_visibility = "excellent"  # Free books get prominent badge
        elif price > 9.99:
            price_visibility = "neutral"
            score -= 3
            recommendations.append(Recommendation(
                area="mobile_price",
                severity="info",
                message="Higher price point may reduce impulse purchases on mobile.",
                suggestion="Consider promotional pricing for mobile discovery.",
            ))
    else:
        price_visibility = "unknown"

    # --- Buy button proximity ---
    buy_button_proximity = "optimal"
    if title_display.is_truncated or (subtitle_display and subtitle_display.is_truncated):
        buy_button_proximity = "good"  # Truncation pushes content but buy button is always visible

    # --- Device-specific previews ---
    device_previews: dict[str, dict] = {}
    for device_id, config in DEVICE_CONFIGS.items():
        title_limit = int(config["title_char_limit"])  # type: ignore[arg-type,call-overload]
        blurb_fold = int(config["blurb_fold_chars"])  # type: ignore[arg-type,call-overload]
        device_title = _check_truncation("title", title, title_limit)
        device_blurb_above = blurb_plain[:blurb_fold]  # type: ignore[misc]
        device_previews[device_id] = {
            "device_name": config["name"],
            "title_truncated": device_title.is_truncated,
            "visible_title": device_title.visible_text,
            "blurb_above_fold_chars": config["blurb_fold_chars"],
            "blurb_above_fold": device_blurb_above,
        }

    score = max(0, min(100, score))

    return MobileCheckResult(
        overall_score=round(score, 1),
        title_display=title_display,
        subtitle_display=subtitle_display,
        blurb_fold_point=blurb_fold,
        blurb_above_fold=blurb_above_fold,
        blurb_above_fold_word_count=blurb_above_fold_words,
        cover_aspect_ratio_ok=cover_aspect_ok,
        cover_readable_at_thumbnail=cover_readable,
        price_visibility=price_visibility,
        buy_button_proximity=buy_button_proximity,
        recommendations=recommendations,
        device_previews=device_previews,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_truncation(field: str, text: str, char_limit: int) -> MobileTruncation:
    """Check if text will be truncated on mobile."""
    original_length = len(text)
    is_truncated = original_length > char_limit
    visible_text = text[:char_limit] + ("..." if is_truncated else "")
    truncated_text = text[char_limit:] if is_truncated else None

    return MobileTruncation(
        field=field,
        original_length=original_length,
        visible_length=min(original_length, char_limit),
        is_truncated=is_truncated,
        visible_text=visible_text,
        truncated_text=truncated_text,
    )


def _strip_html(text: str) -> str:
    """Remove HTML tags from text for character counting."""
    import re
    return re.sub(r"<[^>]+>", "", text)


def _has_above_fold_hook(text: str) -> bool:
    """Check if the above-fold blurb text has a compelling hook."""
    text_lower = text.lower().strip()

    # Question hook
    if "?" in text:
        return True

    # Exclamation
    if "!" in text:
        return True

    # Strong opening words
    hook_words = [
        "discover", "imagine", "secret", "what if", "reveal",
        "never", "always", "shocking", "incredible", "powerful",
        "exclusive", "finally", "the truth", "you won't",
    ]
    return any(word in text_lower for word in hook_words)
