"""Back Matter CTA Engine.

Generates reusable back-matter pages for specialty books: "Also in Series",
"About the Series", email signup CTAs with QR codes, review requests, and
author bios.

Blueprint refs: 12.2
"""
from __future__ import annotations

import base64
import io
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty.models.shared import BookSeries


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BackMatterPage:
    """Rendered back-matter page content."""

    page_type: str
    title: str
    html_content: str
    assets: dict[str, str]  # key -> base64 image data or URL


# ---------------------------------------------------------------------------
# QR Code generator
# ---------------------------------------------------------------------------

def generate_qr_code(url: str, box_size: int = 10, border: int = 4) -> str:
    """Generate a QR code image for *url* and return base64-encoded PNG data.

    Uses the ``qrcode`` library.  If the library is unavailable a
    placeholder SVG data URI is returned so the rest of the module
    continues to work during development.
    """
    try:
        import qrcode  # type: ignore[import-untyped]
        from qrcode.image.pil import PilImage  # type: ignore[import-untyped]

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img: PilImage = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("ascii")
    except ImportError:
        # Fallback: return a minimal placeholder so callers can proceed.
        placeholder_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            '<rect width="100" height="100" fill="#eee"/>'
            '<text x="50" y="55" text-anchor="middle" font-size="10" fill="#888">QR</text>'
            "</svg>"
        )
        return base64.b64encode(placeholder_svg.encode()).decode("ascii")


# ---------------------------------------------------------------------------
# Page generators
# ---------------------------------------------------------------------------

async def generate_also_in_series(
    db: AsyncSession,
    series_id: uuid.UUID,
    current_book_id: uuid.UUID,
) -> BackMatterPage:
    """Generate an "Also in this Series" page listing other volumes.

    Shows cover thumbnails and titles for every volume in the series
    except *current_book_id*.
    """
    stmt = select(BookSeries).where(BookSeries.id == series_id)
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()
    if series is None:
        raise ValueError(f"Series {series_id} not found")

    # In production this would query the actual book records to get cover
    # images and titles.  For now we build a structural template.
    volume_count = series.volume_count or 0

    items_html_parts: list[str] = []
    for vol_num in range(1, volume_count + 1):
        items_html_parts.append(
            f'<div class="also-volume">'
            f'<div class="volume-cover-placeholder">Vol. {vol_num}</div>'
            f'<p class="volume-title">{series.name} - Volume {vol_num}</p>'
            f"</div>"
        )

    html = (
        f'<div class="back-matter also-in-series">'
        f"<h2>Also in the {series.name} Series</h2>"
        f'<div class="volume-grid">{"".join(items_html_parts)}</div>'
        f"</div>"
    )

    return BackMatterPage(
        page_type="also_in_series",
        title=f"Also in the {series.name} Series",
        html_content=html,
        assets={},
    )


async def generate_about_series(
    db: AsyncSession,
    series_id: uuid.UUID,
) -> BackMatterPage:
    """Generate an "About this Series" description page."""
    stmt = select(BookSeries).where(BookSeries.id == series_id)
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()
    if series is None:
        raise ValueError(f"Series {series_id} not found")

    config = series.branding_config or {}
    description = config.get("description", "")

    html = (
        f'<div class="back-matter about-series">'
        f"<h2>About the {series.name} Series</h2>"
        f'<p class="series-description">{description}</p>'
        f"<p><strong>Volumes available:</strong> {series.volume_count}</p>"
        f"</div>"
    )

    return BackMatterPage(
        page_type="about_series",
        title=f"About the {series.name} Series",
        html_content=html,
        assets={},
    )


def generate_email_cta(cta_url: str) -> BackMatterPage:
    """Generate an email signup CTA page with QR code.

    The QR code encodes *cta_url* so readers can scan with their phone
    to reach the signup page.
    """
    qr_data = generate_qr_code(cta_url)

    html = (
        '<div class="back-matter email-cta">'
        "<h2>Join Our Mailing List!</h2>"
        "<p>Get notified about new releases, exclusive content, and special offers.</p>"
        '<div class="qr-container">'
        f'<img src="data:image/png;base64,{qr_data}" alt="QR Code" class="qr-code" />'
        "</div>"
        f'<p class="cta-url">Visit: <a href="{cta_url}">{cta_url}</a></p>'
        "<p>Scan the QR code above or visit the link to sign up.</p>"
        "</div>"
    )

    return BackMatterPage(
        page_type="email_cta",
        title="Join Our Mailing List",
        html_content=html,
        assets={"qr_code": qr_data},
    )


def generate_review_request() -> BackMatterPage:
    """Generate a page asking the reader for an Amazon review.

    Uses a friendly, non-pushy tone aligned with KDP best practices.
    """
    html = (
        '<div class="back-matter review-request">'
        "<h2>Did You Enjoy This Book?</h2>"
        "<p>Thank you for purchasing this book! We hope you had a wonderful time.</p>"
        "<p>If you enjoyed it, we would greatly appreciate a short review on Amazon. "
        "Your feedback helps other readers discover our books and helps us create "
        "even better content.</p>"
        '<div class="review-steps">'
        "<p><strong>How to leave a review:</strong></p>"
        "<ol>"
        "<li>Go to Amazon.com and search for this book title</li>"
        "<li>Scroll down to the Customer Reviews section</li>"
        '<li>Click "Write a customer review"</li>'
        "<li>Share your honest thoughts - even a sentence or two helps!</li>"
        "</ol>"
        "</div>"
        "<p>Thank you for your support!</p>"
        "</div>"
    )

    return BackMatterPage(
        page_type="review_request",
        title="Please Leave a Review",
        html_content=html,
        assets={},
    )


def generate_about_author(author_info: dict[str, Any]) -> BackMatterPage:
    """Generate an "About the Author" bio page.

    Parameters
    ----------
    author_info:
        Dict with keys: ``name``, ``bio``, ``photo_url`` (optional),
        ``website`` (optional), ``social`` (optional dict of platform->url).
    """
    name = author_info.get("name", "The Author")
    bio = author_info.get("bio", "")
    photo_url = author_info.get("photo_url")
    website = author_info.get("website")
    social: dict[str, str] = author_info.get("social") or {}

    photo_html = ""
    if photo_url:
        photo_html = f'<img src="{photo_url}" alt="{name}" class="author-photo" />'

    social_html_parts: list[str] = []
    for platform, url in social.items():
        social_html_parts.append(f'<li><a href="{url}">{platform.title()}</a></li>')
    social_block = ""
    if social_html_parts:
        social_block = f'<ul class="social-links">{"".join(social_html_parts)}</ul>'

    website_block = ""
    if website:
        website_block = f'<p class="author-website">Visit: <a href="{website}">{website}</a></p>'

    html = (
        '<div class="back-matter about-author">'
        f"<h2>About the Author</h2>"
        f"{photo_html}"
        f"<h3>{name}</h3>"
        f'<p class="author-bio">{bio}</p>'
        f"{website_block}"
        f"{social_block}"
        "</div>"
    )

    assets: dict[str, str] = {}
    if photo_url:
        assets["author_photo"] = photo_url

    return BackMatterPage(
        page_type="about_author",
        title=f"About {name}",
        html_content=html,
        assets=assets,
    )
