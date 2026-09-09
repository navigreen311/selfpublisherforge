"""Service implementing bulk operations on books.

Operates on app.models.project.Book, scoped by the organization that owns
the book's parent project.
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.project import Book, BookStatus, Project

logger = logging.getLogger(__name__)


async def _load_books_for_org(
    db: AsyncSession,
    book_ids: list[UUID],
    org_id: UUID,
) -> list[Book]:
    """Return all not-deleted books from book_ids that belong to org_id.

    Joins Book -> Project on project_id; filters by Project.org_id == org_id.
    """
    if not book_ids:
        return []

    query = (
        select(Book)
        .join(Project, Project.id == Book.project_id)
        .where(
            Book.id.in_(book_ids),
            Book.deleted_at.is_(None),
            Project.org_id == org_id,
            Project.deleted_at.is_(None),
        )
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def bulk_archive(
    db: AsyncSession,
    book_ids: list[UUID],
    org_id: UUID,
) -> tuple[int, list[UUID]]:
    """Archive the given books. Returns (affected, skipped_ids)."""
    books = await _load_books_for_org(db, book_ids, org_id)
    found_ids = {b.id for b in books}
    for b in books:
        b.status = BookStatus.ARCHIVED
        b.updated_at = datetime.now(UTC)
    await db.commit()
    skipped = [bid for bid in book_ids if bid not in found_ids]
    return len(books), skipped


async def bulk_delete(
    db: AsyncSession,
    book_ids: list[UUID],
    org_id: UUID,
) -> tuple[int, list[UUID]]:
    """Soft-delete the given books. Returns (affected, skipped_ids)."""
    books = await _load_books_for_org(db, book_ids, org_id)
    found_ids = {b.id for b in books}
    now = datetime.now(UTC)
    for b in books:
        b.deleted_at = now
    await db.commit()
    skipped = [bid for bid in book_ids if bid not in found_ids]
    return len(books), skipped


async def bulk_change_price(
    db: AsyncSession,
    book_ids: list[UUID],
    org_id: UUID,
    price: float,
) -> tuple[int, list[UUID]]:
    """Set metadata.price for the given books. Returns (affected, skipped_ids)."""
    books = await _load_books_for_org(db, book_ids, org_id)
    found_ids = {b.id for b in books}
    for b in books:
        md = dict(b.metadata_ or {})
        md["price"] = float(price)
        b.metadata_ = md
        flag_modified(b, "metadata_")
        b.updated_at = datetime.now(UTC)
    await db.commit()
    skipped = [bid for bid in book_ids if bid not in found_ids]
    return len(books), skipped


async def bulk_add_tags(
    db: AsyncSession,
    book_ids: list[UUID],
    org_id: UUID,
    tags: list[str],
) -> tuple[int, list[UUID]]:
    """Merge `tags` into each book's metadata.tags (dedup, preserve order)."""
    books = await _load_books_for_org(db, book_ids, org_id)
    found_ids = {b.id for b in books}
    incoming = [str(t).strip() for t in tags if str(t).strip()]
    for b in books:
        md = dict(b.metadata_ or {})
        existing = md.get("tags") or []
        if not isinstance(existing, list):
            existing = []
        merged: list[str] = []
        seen: set[str] = set()
        for t in list(existing) + incoming:
            ts = str(t)
            if ts not in seen:
                merged.append(ts)
                seen.add(ts)
        md["tags"] = merged
        b.metadata_ = md
        flag_modified(b, "metadata_")
        b.updated_at = datetime.now(UTC)
    await db.commit()
    skipped = [bid for bid in book_ids if bid not in found_ids]
    return len(books), skipped


async def export_metadata_csv(
    db: AsyncSession,
    book_ids: list[UUID],
    org_id: UUID,
) -> str:
    """Return CSV text with metadata rows for each selected book."""
    books = await _load_books_for_org(db, book_ids, org_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "project_id",
            "title",
            "subtitle",
            "isbn",
            "asin",
            "format",
            "status",
            "price",
            "tags",
            "created_at",
            "updated_at",
        ]
    )
    for b in books:
        md = b.metadata_ or {}
        price = md.get("price", "")
        tags = md.get("tags") or []
        tags_str = ";".join(str(t) for t in tags) if isinstance(tags, list) else ""
        writer.writerow(
            [
                str(b.id),
                str(b.project_id),
                b.title or "",
                b.subtitle or "",
                b.isbn or "",
                b.asin or "",
                b.format.value if hasattr(b.format, "value") else str(b.format),
                b.status.value if hasattr(b.status, "value") else str(b.status),
                price,
                tags_str,
                b.created_at.isoformat() if b.created_at else "",
                b.updated_at.isoformat() if b.updated_at else "",
            ]
        )
    return buf.getvalue()
