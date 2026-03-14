"""ISBN & Barcode Management.

Manages a pool of ISBNs per organisation, tracks assignment to books, and
generates EAN-13 barcodes for back-cover placement.

Blueprint refs: 12.4
"""
from __future__ import annotations

import base64
import io
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
    """Generate an EAN-13 barcode image for *isbn*.

    Returns base64-encoded PNG data.  Uses ``python-barcode`` when
    available, otherwise returns a placeholder.
    """
    clean_isbn = isbn.replace("-", "").replace(" ", "")

    try:
        import barcode as barcode_lib  # type: ignore[import-untyped]
        from barcode.writer import ImageWriter  # type: ignore[import-untyped]

        ean = barcode_lib.get_barcode_class("ean13")
        code = ean(clean_isbn, writer=ImageWriter())

        buf = io.BytesIO()
        code.write(buf)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("ascii")
    except (ImportError, Exception):
        # Fallback placeholder
        placeholder_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">'
            '<rect width="200" height="100" fill="#fff" stroke="#000"/>'
            f'<text x="100" y="55" text-anchor="middle" font-size="12">{clean_isbn}</text>'
            '<text x="100" y="75" text-anchor="middle" font-size="9" fill="#888">EAN-13</text>'
            "</svg>"
        )
        return base64.b64encode(placeholder_svg.encode()).decode("ascii")


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
