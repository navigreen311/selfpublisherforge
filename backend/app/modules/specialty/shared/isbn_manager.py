"""ISBN & Barcode Management.

Manages a pool of ISBNs per organisation, tracks assignment to books, and
generates EAN-13 barcodes for back-cover placement.

Blueprint refs: 12.4
"""
from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty.models.enums import ISBNStatus
from app.modules.specialty.models.shared import ISBNPool


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ISBNRecord:
    """Lightweight representation of an ISBN pool entry."""

    id: uuid.UUID
    org_id: uuid.UUID
    isbn: str
    publisher_name: str | None
    assigned_to_book_type: str | None
    assigned_to_book_id: uuid.UUID | None
    barcode_data: str | None
    status: str


@dataclass
class PoolStatus:
    """Aggregated ISBN pool statistics."""

    total: int
    assigned: int
    available: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_record(row: ISBNPool) -> ISBNRecord:
    return ISBNRecord(
        id=row.id,
        org_id=row.org_id,
        isbn=row.isbn,
        publisher_name=row.publisher_name,
        assigned_to_book_type=row.assigned_to_book_type,
        assigned_to_book_id=row.assigned_to_book_id,
        barcode_data=row.barcode_url,
        status=row.status,
    )


def _validate_isbn13(isbn: str) -> bool:
    """Validate an ISBN-13 check digit."""
    digits = isbn.replace("-", "").replace(" ", "")
    if len(digits) != 13 or not digits.isdigit():
        return False
    total = sum(
        int(d) * (1 if i % 2 == 0 else 3)
        for i, d in enumerate(digits)
    )
    return total % 10 == 0


# ---------------------------------------------------------------------------
# Barcode generation
# ---------------------------------------------------------------------------

def generate_barcode(isbn: str) -> str:
    """Generate an EAN-13 barcode SVG for *isbn*.

    Returns base64-encoded SVG data.  Implemented in pure Python with no
    external dependencies.  The barcode follows the EAN-13 specification
    with proper L/G/R encoding, guard patterns, and human-readable digits.
    """
    clean_isbn = isbn.replace("-", "").replace(" ", "")

    if len(clean_isbn) != 13 or not clean_isbn.isdigit():
        raise ValueError(f"EAN-13 barcode requires exactly 13 digits, got: {clean_isbn!r}")

    svg = _render_ean13_svg(clean_isbn)
    return base64.b64encode(svg.encode("utf-8")).decode("ascii")


# EAN-13 encoding tables -----------------------------------------------

# L-codes (odd parity, left half)
_L_CODES: list[str] = [
    "0001101",  # 0
    "0011001",  # 1
    "0010011",  # 2
    "0111101",  # 3
    "0100011",  # 4
    "0110001",  # 5
    "0101111",  # 6
    "0111011",  # 7
    "0110111",  # 8
    "0001011",  # 9
]

# G-codes (even parity, left half)
_G_CODES: list[str] = [
    "0100111",  # 0
    "0110011",  # 1
    "0011011",  # 2
    "0100001",  # 3
    "0011101",  # 4
    "0111001",  # 5
    "0000101",  # 6
    "0010001",  # 7
    "0001001",  # 8
    "0010111",  # 9
]

# R-codes (right half — complement of L-codes)
_R_CODES: list[str] = [
    "1110010",  # 0
    "1100110",  # 1
    "1101100",  # 2
    "1000010",  # 3
    "1011100",  # 4
    "1001110",  # 5
    "1010000",  # 6
    "1000100",  # 7
    "1001000",  # 8
    "1110100",  # 9
]

# First-digit parity patterns (which of L/G to use for digits 2-7)
# L = 0, G = 1
_FIRST_DIGIT_PATTERNS: list[str] = [
    "LLLLLL",  # 0
    "LLGLGG",  # 1
    "LLGGLG",  # 2
    "LLGGGL",  # 3
    "LGLLGG",  # 4
    "LGGLLG",  # 5
    "LGGGLL",  # 6
    "LGLGLG",  # 7
    "LGLGGL",  # 8
    "LGGLGL",  # 9
]


def _ean13_binary(digits: str) -> str:
    """Convert 13-digit string to the full EAN-13 binary bar pattern.

    Returns a string of '0' (space) and '1' (bar) characters.
    """
    first_digit = int(digits[0])
    parity = _FIRST_DIGIT_PATTERNS[first_digit]

    bars: list[str] = []

    # Start guard: 101
    bars.append("101")

    # Left half: digits[1..6] encoded with L or G per parity pattern
    for i in range(6):
        d = int(digits[1 + i])
        if parity[i] == "L":
            bars.append(_L_CODES[d])
        else:
            bars.append(_G_CODES[d])

    # Centre guard: 01010
    bars.append("01010")

    # Right half: digits[7..12] encoded with R-codes
    for i in range(6):
        d = int(digits[7 + i])
        bars.append(_R_CODES[d])

    # End guard: 101
    bars.append("101")

    return "".join(bars)


def _render_ean13_svg(digits: str) -> str:
    """Render a complete EAN-13 barcode as an SVG string."""
    binary = _ean13_binary(digits)

    module_w = 2          # width of narrowest bar in SVG units
    bar_h = 70            # normal bar height
    guard_extra = 5       # extra height for guard bars
    font_size = 12
    text_y = bar_h + guard_extra + font_size + 2
    quiet_zone = 10 * module_w  # quiet zone width (≥ 9 modules recommended)

    total_modules = len(binary)  # 95 modules for EAN-13
    svg_w = total_modules * module_w + 2 * quiet_zone
    svg_h = text_y + 4

    # Identify guard bar positions (start: 0-2, centre: 45-49, end: 92-94)
    guard_positions: set[int] = set()
    for p in range(3):
        guard_positions.add(p)        # start guard
    for p in range(45, 50):
        guard_positions.add(p)        # centre guard
    for p in range(92, 95):
        guard_positions.add(p)        # end guard

    # Build bar rectangles
    rects: list[str] = []
    for i, ch in enumerate(binary):
        if ch == "1":
            x = quiet_zone + i * module_w
            h = bar_h + guard_extra if i in guard_positions else bar_h
            rects.append(
                f'<rect x="{x}" y="0" width="{module_w}" height="{h}" fill="#000"/>'
            )

    # Human-readable digits -------------------------------------------------
    texts: list[str] = []

    # First digit (to the left of the start guard)
    texts.append(
        f'<text x="{quiet_zone - 4}" y="{text_y}" '
        f'font-family="monospace" font-size="{font_size}" text-anchor="end">'
        f"{digits[0]}</text>"
    )

    # Left group (digits 1-6), centred under left bars (modules 3-44)
    left_centre = quiet_zone + (3 + 42) * module_w // 2
    left_text = digits[1:7]
    texts.append(
        f'<text x="{left_centre}" y="{text_y}" '
        f'font-family="monospace" font-size="{font_size}" text-anchor="middle" '
        f'letter-spacing="2">{left_text}</text>'
    )

    # Right group (digits 7-12), centred under right bars (modules 50-91)
    right_centre = quiet_zone + (50 + 91) * module_w // 2
    right_text = digits[7:13]
    texts.append(
        f'<text x="{right_centre}" y="{text_y}" '
        f'font-family="monospace" font-size="{font_size}" text-anchor="middle" '
        f'letter-spacing="2">{right_text}</text>'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">'
        f'<rect width="{svg_w}" height="{svg_h}" fill="#fff"/>'
        + "".join(rects)
        + "".join(texts)
        + "</svg>"
    )
    return svg


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def add_isbn_to_pool(
    db: AsyncSession,
    org_id: uuid.UUID,
    isbn: str,
    publisher_name: str | None = None,
) -> ISBNRecord:
    """Add a new ISBN to the organisation's pool.

    Validates ISBN-13 format and check digit before inserting.
    """
    if not _validate_isbn13(isbn):
        raise ValueError(f"Invalid ISBN-13: {isbn}")

    clean = isbn.replace("-", "").replace(" ", "")

    row = ISBNPool(
        org_id=org_id,
        isbn=clean,
        publisher_name=publisher_name,
        status=ISBNStatus.available,
    )
    db.add(row)
    await db.flush()

    return _row_to_record(row)


async def assign_isbn(
    db: AsyncSession,
    isbn_id: uuid.UUID,
    book_type: str,
    book_id: uuid.UUID,
) -> ISBNRecord:
    """Assign an ISBN from the pool to a specific book.

    Also generates the EAN-13 barcode and stores it.
    """
    stmt = select(ISBNPool).where(ISBNPool.id == isbn_id)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise ValueError(f"ISBN record {isbn_id} not found")

    if row.status != ISBNStatus.available.value and row.status != ISBNStatus.available:
        raise ValueError(f"ISBN {row.isbn} is not available (status: {row.status})")

    barcode_data = generate_barcode(row.isbn)

    row.assigned_to_book_type = book_type
    row.assigned_to_book_id = book_id
    row.status = ISBNStatus.assigned
    row.barcode_url = barcode_data
    await db.flush()

    return _row_to_record(row)


async def get_pool_status(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> PoolStatus:
    """Return aggregated pool statistics for an organisation."""
    total_stmt = (
        select(func.count())
        .select_from(ISBNPool)
        .where(ISBNPool.org_id == org_id)
    )
    assigned_stmt = (
        select(func.count())
        .select_from(ISBNPool)
        .where(
            ISBNPool.org_id == org_id,
            ISBNPool.status.in_([ISBNStatus.assigned, ISBNStatus.used]),
        )
    )
    available_stmt = (
        select(func.count())
        .select_from(ISBNPool)
        .where(
            ISBNPool.org_id == org_id,
            ISBNPool.status == ISBNStatus.available,
        )
    )

    total = (await db.execute(total_stmt)).scalar() or 0
    assigned = (await db.execute(assigned_stmt)).scalar() or 0
    available = (await db.execute(available_stmt)).scalar() or 0

    return PoolStatus(total=total, assigned=assigned, available=available)
