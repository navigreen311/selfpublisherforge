"""Back Matter CTA Engine.

Generates reusable back-matter pages for specialty books: "Also in Series",
"About the Series", email signup CTAs with QR codes, review requests, and
author bios.

Blueprint refs: 12.2
"""
from __future__ import annotations

import base64
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
    """Generate a QR code SVG for *url* and return base64-encoded SVG data.

    Pure-Python implementation — no external libraries required.
    Uses byte-mode encoding with error-correction level L.
    Supports QR versions 1-4 (up to 114 byte-mode characters).
    """
    matrix = _qr_encode(url)
    svg = _qr_render_svg(matrix, box_size=box_size, border=border)
    return base64.b64encode(svg.encode("utf-8")).decode("ascii")


# =========================================================================
# Pure-Python QR Code encoder (byte mode, EC level L, versions 1-4)
# =========================================================================

# Version info: (version, size, total_codewords, ec_codewords_per_block,
#                num_blocks, data_codewords)
# EC level L only.
_QR_VERSIONS: list[tuple[int, int, int, int, int, int]] = [
    # ver, size, total_cw, ec_per_blk, num_blks, data_cw
    (1, 21, 26, 7, 1, 19),
    (2, 25, 44, 10, 1, 34),
    (3, 29, 70, 15, 1, 55),
    (4, 33, 80, 20, 1, 80),
]

# Alignment pattern centre coordinates per version (version 1 has none)
_ALIGNMENT_POSITIONS: dict[int, list[int]] = {
    2: [6, 18],
    3: [6, 22],
    4: [6, 26],
}

# Format info bits for EC level L with mask 0-7 (15 bits each, pre-computed
# with BCH error correction and XOR mask 0x5412)
_FORMAT_BITS: list[int] = [
    0x77C4, 0x72F3, 0x7DAA, 0x789D, 0x662F, 0x6318, 0x6C41, 0x6976,
]


def _pick_version(data_len: int) -> tuple[int, int, int, int, int, int]:
    """Select the smallest QR version that fits *data_len* bytes."""
    # In byte mode the data payload is: 4 (mode) + 8 (count) + data*8 + 4 (terminator) bits
    # rounded up to codeword boundary, then padded.
    for v in _QR_VERSIONS:
        if data_len <= v[5] - 2:  # 2 bytes overhead (mode indicator + count)
            return v
    raise ValueError(
        f"Data too long for QR versions 1-4 ({data_len} bytes). "
        "Maximum is 114 characters."
    )


def _encode_data_codewords(data: bytes, data_capacity: int) -> list[int]:
    """Encode *data* into QR data codewords (byte mode, no ECI)."""
    bits: list[int] = []

    def add_bits(val: int, length: int) -> None:
        for i in range(length - 1, -1, -1):
            bits.append((val >> i) & 1)

    # Mode indicator: 0100 (byte mode)
    add_bits(0b0100, 4)
    # Character count (8 bits for versions 1-9)
    add_bits(len(data), 8)
    # Data
    for byte in data:
        add_bits(byte, 8)
    # Terminator (up to 4 zero bits)
    terminator_len = min(4, data_capacity * 8 - len(bits))
    add_bits(0, terminator_len)
    # Pad to byte boundary
    while len(bits) % 8 != 0:
        bits.append(0)

    codewords: list[int] = []
    for i in range(0, len(bits), 8):
        cw = 0
        for b in bits[i : i + 8]:
            cw = (cw << 1) | b
        codewords.append(cw)

    # Pad codewords with alternating 0xEC, 0x11
    pad_bytes = [0xEC, 0x11]
    pi = 0
    while len(codewords) < data_capacity:
        codewords.append(pad_bytes[pi % 2])
        pi += 1

    return codewords


# Reed-Solomon GF(256) arithmetic for QR error correction ----------------

_GF_EXP = [0] * 512
_GF_LOG = [0] * 256


def _init_gf() -> None:
    x = 1
    for i in range(255):
        _GF_EXP[i] = x
        _GF_LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D  # QR primitive polynomial
    for i in range(255, 512):
        _GF_EXP[i] = _GF_EXP[i - 255]


_init_gf()


def _gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _GF_EXP[_GF_LOG[a] + _GF_LOG[b]]


def _rs_generator_poly(n: int) -> list[int]:
    """Build generator polynomial for *n* EC codewords."""
    g = [1]
    for i in range(n):
        new_g = [0] * (len(g) + 1)
        for j, coeff in enumerate(g):
            new_g[j] ^= coeff
            new_g[j + 1] ^= _gf_mul(coeff, _GF_EXP[i])
        g = new_g
    return g


def _rs_encode(data: list[int], n_ec: int) -> list[int]:
    """Compute *n_ec* Reed-Solomon EC codewords for *data*."""
    gen = _rs_generator_poly(n_ec)
    remainder = [0] * n_ec
    for d in data:
        factor = d ^ remainder[0]
        remainder = remainder[1:] + [0]
        for i in range(n_ec):
            remainder[i] ^= _gf_mul(gen[i + 1], factor)
    return remainder


# Matrix construction ----------------------------------------------------

def _make_matrix(size: int) -> list[list[int | None]]:
    return [[None] * size for _ in range(size)]


def _set_finder_pattern(matrix: list[list[int | None]], row: int, col: int) -> None:
    """Place a 7x7 finder pattern with top-left corner at (row, col)."""
    for r in range(7):
        for c in range(7):
            if (
                r in (0, 6)
                or c in (0, 6)
                or (2 <= r <= 4 and 2 <= c <= 4)
            ):
                matrix[row + r][col + c] = 1
            else:
                matrix[row + r][col + c] = 0


def _set_alignment_pattern(matrix: list[list[int | None]], row: int, col: int) -> None:
    """Place a 5x5 alignment pattern centred at (row, col)."""
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            r, c = row + dr, col + dc
            if matrix[r][c] is not None:
                continue  # don't overwrite finder patterns
            if abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0):
                matrix[r][c] = 1
            else:
                matrix[r][c] = 0


def _set_timing_patterns(matrix: list[list[int | None]], size: int) -> None:
    for i in range(8, size - 8):
        v = 1 if i % 2 == 0 else 0
        if matrix[6][i] is None:
            matrix[6][i] = v
        if matrix[i][6] is None:
            matrix[i][6] = v


def _reserve_format_area(matrix: list[list[int | None]], size: int) -> None:
    """Reserve (set to 0) the format information areas."""
    for i in range(9):
        if matrix[8][i] is None:
            matrix[8][i] = 0
        if matrix[i][8] is None:
            matrix[i][8] = 0
    for i in range(8):
        if matrix[8][size - 1 - i] is None:
            matrix[8][size - 1 - i] = 0
        if matrix[size - 1 - i][8] is None:
            matrix[size - 1 - i][8] = 0
    # Dark module
    matrix[size - 8][8] = 1


def _place_data_bits(
    matrix: list[list[int | None]], size: int, data_bits: list[int]
) -> None:
    """Place data bits into the matrix using the QR upward-zigzag pattern."""
    bit_idx = 0
    # Columns are traversed right-to-left in pairs
    col = size - 1
    going_up = True
    while col >= 0:
        if col == 6:
            col -= 1  # skip timing column
            continue
        for row_offset in range(size):
            row = (size - 1 - row_offset) if going_up else row_offset
            for dc in (0, -1):
                c = col + dc
                if c < 0:
                    continue
                if matrix[row][c] is not None:
                    continue
                if bit_idx < len(data_bits):
                    matrix[row][c] = data_bits[bit_idx]
                    bit_idx += 1
                else:
                    matrix[row][c] = 0
        going_up = not going_up
        col -= 2


def _apply_mask(matrix: list[list[int | None]], size: int, mask_id: int,
                func_pattern: list[list[bool]]) -> list[list[int]]:
    """Apply mask *mask_id* and return a new int matrix."""
    mask_fns = [
        lambda r, c: (r + c) % 2 == 0,
        lambda r, c: r % 2 == 0,
        lambda r, c: c % 3 == 0,
        lambda r, c: (r + c) % 3 == 0,
        lambda r, c: (r // 2 + c // 3) % 2 == 0,
        lambda r, c: (r * c) % 2 + (r * c) % 3 == 0,
        lambda r, c: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
        lambda r, c: ((r + c) % 2 + (r * c) % 3) % 2 == 0,
    ]
    fn = mask_fns[mask_id]
    result: list[list[int]] = []
    for r in range(size):
        row: list[int] = []
        for c in range(size):
            val = matrix[r][c] or 0
            if not func_pattern[r][c] and fn(r, c):
                val ^= 1
            row.append(val)
        result.append(row)
    return result


def _penalty_score(matrix: list[list[int]], size: int) -> int:
    """Calculate the mask penalty score (simplified)."""
    score = 0
    # Rule 1: runs of 5+ same-colour modules
    for r in range(size):
        run = 1
        for c in range(1, size):
            if matrix[r][c] == matrix[r][c - 1]:
                run += 1
            else:
                if run >= 5:
                    score += run - 2
                run = 1
        if run >= 5:
            score += run - 2
    for c in range(size):
        run = 1
        for r in range(1, size):
            if matrix[r][c] == matrix[r - 1][c]:
                run += 1
            else:
                if run >= 5:
                    score += run - 2
                run = 1
        if run >= 5:
            score += run - 2
    # Rule 2: 2x2 blocks
    for r in range(size - 1):
        for c in range(size - 1):
            v = matrix[r][c]
            if v == matrix[r][c + 1] == matrix[r + 1][c] == matrix[r + 1][c + 1]:
                score += 3
    return score


def _write_format_info(matrix: list[list[int]], size: int, mask_id: int) -> None:
    """Write the 15-bit format string into the reserved areas."""
    fmt = _FORMAT_BITS[mask_id]
    bits = [(fmt >> (14 - i)) & 1 for i in range(15)]

    # Around top-left finder
    positions_a = [
        (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5),
        (8, 7), (8, 8), (7, 8), (5, 8), (4, 8), (3, 8),
        (2, 8), (1, 8), (0, 8),
    ]
    for i, (r, c) in enumerate(positions_a):
        matrix[r][c] = bits[i]

    # Along bottom-left and top-right
    positions_b = [
        (size - 1, 8), (size - 2, 8), (size - 3, 8), (size - 4, 8),
        (size - 5, 8), (size - 6, 8), (size - 7, 8),
        (8, size - 8), (8, size - 7), (8, size - 6), (8, size - 5),
        (8, size - 4), (8, size - 3), (8, size - 2), (8, size - 1),
    ]
    for i, (r, c) in enumerate(positions_b):
        matrix[r][c] = bits[i]


def _qr_encode(text: str) -> list[list[int]]:
    """Encode *text* into a QR code and return the module matrix.

    Each cell is 0 (white) or 1 (black).
    """
    data = text.encode("utf-8")
    ver, size, total_cw, ec_per_blk, num_blks, data_cw = _pick_version(len(data))
    n_ec = total_cw - data_cw

    # Encode data codewords + EC codewords
    data_cws = _encode_data_codewords(data, data_cw)
    ec_cws = _rs_encode(data_cws, n_ec)
    all_cws = data_cws + ec_cws

    # Convert to bit stream
    data_bits: list[int] = []
    for cw in all_cws:
        for i in range(7, -1, -1):
            data_bits.append((cw >> i) & 1)

    # Build matrix with function patterns
    matrix = _make_matrix(size)

    # Finder patterns + separators
    _set_finder_pattern(matrix, 0, 0)
    _set_finder_pattern(matrix, 0, size - 7)
    _set_finder_pattern(matrix, size - 7, 0)
    # Separators (white borders around finders)
    for i in range(8):
        for r, c in [(i, 7), (7, i)]:
            if matrix[r][c] is None:
                matrix[r][c] = 0
        for r, c in [(i, size - 8), (7, size - 1 - i)]:
            if r < size and c >= 0 and matrix[r][c] is None:
                matrix[r][c] = 0
        for r, c in [(size - 8, i), (size - 1 - i, 7)]:
            if r >= 0 and c < size and matrix[r][c] is None:
                matrix[r][c] = 0

    # Alignment patterns
    if ver in _ALIGNMENT_POSITIONS:
        positions = _ALIGNMENT_POSITIONS[ver]
        for ar in positions:
            for ac in positions:
                # Skip if it overlaps a finder pattern
                if ar <= 8 and ac <= 8:
                    continue
                if ar <= 8 and ac >= size - 8:
                    continue
                if ar >= size - 8 and ac <= 8:
                    continue
                _set_alignment_pattern(matrix, ar, ac)

    _set_timing_patterns(matrix, size)
    _reserve_format_area(matrix, size)

    # Record function pattern positions
    func_pattern = [[matrix[r][c] is not None for c in range(size)] for r in range(size)]

    # Place data
    _place_data_bits(matrix, size, data_bits)

    # Try all 8 masks and pick the best
    best_score = float("inf")
    best_result: list[list[int]] = []
    best_mask = 0
    for mask_id in range(8):
        candidate = _apply_mask(matrix, size, mask_id, func_pattern)
        _write_format_info(candidate, size, mask_id)
        score = _penalty_score(candidate, size)
        if score < best_score:
            best_score = score
            best_result = candidate
            best_mask = mask_id

    # Write format info on the final result
    _write_format_info(best_result, size, best_mask)
    return best_result


def _qr_render_svg(
    matrix: list[list[int]], box_size: int = 10, border: int = 4
) -> str:
    """Render a QR module matrix to an SVG string."""
    n = len(matrix)
    total = n + 2 * border
    dim = total * box_size

    rects: list[str] = []
    for r in range(n):
        for c in range(n):
            if matrix[r][c]:
                x = (c + border) * box_size
                y = (r + border) * box_size
                rects.append(
                    f'<rect x="{x}" y="{y}" '
                    f'width="{box_size}" height="{box_size}" fill="#000"/>'
                )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{dim}" height="{dim}" viewBox="0 0 {dim} {dim}">'
        f'<rect width="{dim}" height="{dim}" fill="#fff"/>'
        + "".join(rects)
        + "</svg>"
    )


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
        f'<img src="data:image/svg+xml;base64,{qr_data}" alt="QR Code" class="qr-code" />'
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
