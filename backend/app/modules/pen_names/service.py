"""Pen Names service layer."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Book, PenName, Project


async def list_pen_names(db: AsyncSession, org_id: UUID) -> list[PenName]:
    stmt = (
        select(PenName)
        .where(PenName.org_id == org_id, PenName.deleted_at.is_(None))
        .order_by(PenName.is_default.desc(), PenName.created_at.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


async def get_pen_name(db: AsyncSession, org_id: UUID, pen_id: UUID) -> PenName:
    stmt = select(PenName).where(
        PenName.id == pen_id,
        PenName.org_id == org_id,
        PenName.deleted_at.is_(None),
    )
    pen = (await db.execute(stmt)).scalar_one_or_none()
    if not pen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pen name not found")
    return pen


async def _clear_default(db: AsyncSession, org_id: UUID) -> None:
    await db.execute(
        update(PenName)
        .where(PenName.org_id == org_id, PenName.is_default.is_(True))
        .values(is_default=False)
    )


async def create_pen_name(
    db: AsyncSession,
    *,
    org_id: UUID,
    user_id: UUID | None,
    display_name: str,
    amazon_url: str | None,
    bio: str | None,
    photo_url: str | None,
    genres: list[str],
    is_default: bool,
) -> PenName:
    if is_default:
        await _clear_default(db, org_id)

    # If this is the org's first pen name, force it to default.
    existing = (
        await db.execute(
            select(func.count(PenName.id)).where(
                PenName.org_id == org_id, PenName.deleted_at.is_(None)
            )
        )
    ).scalar_one()
    if existing == 0:
        is_default = True

    pen = PenName(
        org_id=org_id,
        user_id=user_id,
        name=display_name,
        display_name=display_name,
        amazon_author_url=amazon_url,
        bio=bio,
        photo_url=photo_url,
        genres=genres or [],
        is_default=is_default,
        book_count=0,
    )
    db.add(pen)
    await db.flush()
    await db.refresh(pen)
    return pen


async def update_pen_name(
    db: AsyncSession,
    *,
    org_id: UUID,
    pen_id: UUID,
    display_name: str | None = None,
    amazon_url: str | None = None,
    bio: str | None = None,
    photo_url: str | None = None,
    genres: list[str] | None = None,
    is_default: bool | None = None,
) -> PenName:
    pen = await get_pen_name(db, org_id, pen_id)
    if display_name is not None:
        pen.display_name = display_name
        pen.name = display_name
    if amazon_url is not None:
        pen.amazon_author_url = amazon_url
    if bio is not None:
        pen.bio = bio
    if photo_url is not None:
        pen.photo_url = photo_url
    if genres is not None:
        pen.genres = genres
    if is_default is True:
        await _clear_default(db, org_id)
        pen.is_default = True
    elif is_default is False:
        pen.is_default = False
    await db.flush()
    await db.refresh(pen)
    return pen


async def delete_pen_name(db: AsyncSession, org_id: UUID, pen_id: UUID) -> None:
    pen = await get_pen_name(db, org_id, pen_id)
    if pen.is_default:
        # Make sure we never leave the org without a default if any remain.
        remaining = (
            await db.execute(
                select(PenName).where(
                    PenName.org_id == org_id,
                    PenName.id != pen_id,
                    PenName.deleted_at.is_(None),
                )
            )
        ).scalars().first()
        if remaining is not None:
            remaining.is_default = True
    from datetime import datetime, timezone

    pen.deleted_at = datetime.now(timezone.utc)
    await db.flush()


async def set_default(db: AsyncSession, org_id: UUID, pen_id: UUID) -> PenName:
    pen = await get_pen_name(db, org_id, pen_id)
    await _clear_default(db, org_id)
    pen.is_default = True
    await db.flush()
    await db.refresh(pen)
    return pen


async def list_books_for_pen(
    db: AsyncSession, org_id: UUID, pen_id: UUID
) -> list[dict]:
    await get_pen_name(db, org_id, pen_id)  # verify access

    # Books can be attributed two ways: directly via books.pen_name_id, or via
    # their parent project's pen_name_id. Union both so the UI shows everything.
    direct = (
        select(Book.id, Book.title, Project.type, Book.status)
        .join(Project, Project.id == Book.project_id)
        .where(
            Book.pen_name_id == pen_id,
            Project.org_id == org_id,
            Book.deleted_at.is_(None),
        )
    )
    inherited = (
        select(Book.id, Book.title, Project.type, Book.status)
        .join(Project, Project.id == Book.project_id)
        .where(
            Project.pen_name_id == pen_id,
            Project.org_id == org_id,
            Book.deleted_at.is_(None),
            Book.pen_name_id.is_(None),
        )
    )
    rows = (await db.execute(direct.union(inherited))).all()
    return [
        {
            "id": r[0],
            "title": r[1],
            "type": getattr(r[2], "value", r[2]) if r[2] is not None else None,
            "status": getattr(r[3], "value", r[3]) if r[3] is not None else None,
        }
        for r in rows
    ]


async def pen_analytics(
    db: AsyncSession, org_id: UUID, pen_id: UUID, period: str
) -> dict:
    """Stub analytics aggregation -- real numbers wire in via the analytics
    module once per-pen filters land there. For now we return the book count
    and zeroed metrics so the UI has a stable contract."""
    books = await list_books_for_pen(db, org_id, pen_id)
    return {
        "revenue": 0.0,
        "sales": 0,
        "books_count": len(books),
        "avg_rating": 0.0,
        "period": period,
    }


def to_response(pen: PenName) -> dict:
    return {
        "id": pen.id,
        "display_name": pen.display_name or pen.name,
        "amazon_url": pen.amazon_author_url,
        "bio": pen.bio,
        "photo_url": pen.photo_url,
        "genres": list(pen.genres or []),
        "is_default": bool(pen.is_default),
        "book_count": pen.book_count or 0,
        "created_at": pen.created_at,
        "updated_at": pen.updated_at,
    }
