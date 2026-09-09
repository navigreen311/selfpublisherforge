"""Global search service -- ILIKE across a few key text fields per type.

Results are always grouped by type. Failures for any individual source are
swallowed and logged so partial results are still returned.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.search.schemas import SearchResponse, SearchResultItem

logger = logging.getLogger(__name__)

ALL_TYPES = {"projects", "books", "recipes", "chapters", "reviews"}


async def _search_projects(db: AsyncSession, org_id: UUID, like: str) -> list[SearchResultItem]:
    try:
        from app.models.project import Project

        stmt = (
            select(Project)
            .where(
                Project.org_id == org_id,
                Project.deleted_at.is_(None),
                or_(
                    Project.title.ilike(like),
                    Project.description.ilike(like),
                ),
            )
            .limit(10)
        )
        result = await db.execute(stmt)
        return [
            SearchResultItem(
                id=p.id,
                title=p.title,
                snippet=(p.description or "")[:180],
                resource_type="project",
            )
            for p in result.scalars().all()
        ]
    except Exception as exc:
        logger.debug("search projects failed: %s", exc)
        return []


async def _search_books(db: AsyncSession, org_id: UUID, like: str) -> list[SearchResultItem]:
    try:
        from app.models.project import Book, Project

        stmt = (
            select(Book)
            .join(Project, Project.id == Book.project_id)
            .where(
                Project.org_id == org_id,
                Book.deleted_at.is_(None),
                or_(
                    Book.title.ilike(like),
                    Book.subtitle.ilike(like),
                ),
            )
            .limit(10)
        )
        result = await db.execute(stmt)
        return [
            SearchResultItem(
                id=b.id,
                title=b.title,
                snippet=b.subtitle,
                resource_type="book",
            )
            for b in result.scalars().all()
        ]
    except Exception as exc:
        logger.debug("search books failed: %s", exc)
        return []


async def _search_chapters(db: AsyncSession, org_id: UUID, like: str) -> list[SearchResultItem]:
    try:
        from app.models.content import Chapter

        stmt = (
            select(Chapter)
            .where(
                Chapter.deleted_at.is_(None) if hasattr(Chapter, "deleted_at") else True,
                or_(
                    Chapter.title.ilike(like),
                    Chapter.content.ilike(like) if hasattr(Chapter, "content") else Chapter.title.ilike(like),
                ),
            )
            .limit(10)
        )
        result = await db.execute(stmt)
        return [
            SearchResultItem(
                id=c.id,
                title=getattr(c, "title", "Chapter"),
                snippet=(getattr(c, "content", None) or "")[:180],
                resource_type="chapter",
            )
            for c in result.scalars().all()
        ]
    except Exception as exc:
        logger.debug("search chapters failed: %s", exc)
        return []


async def _search_recipes(db: AsyncSession, org_id: UUID, like: str) -> list[SearchResultItem]:
    try:
        from app.modules.specialty.cookbook.models import Recipe  # type: ignore

        stmt = (
            select(Recipe)
            .where(
                getattr(Recipe, "org_id", None) == org_id if hasattr(Recipe, "org_id") else True,
                Recipe.title.ilike(like),
            )
            .limit(10)
        )
        result = await db.execute(stmt)
        return [
            SearchResultItem(
                id=r.id,
                title=r.title,
                snippet=(getattr(r, "description", None) or "")[:180],
                resource_type="recipe",
            )
            for r in result.scalars().all()
        ]
    except Exception as exc:
        logger.debug("search recipes failed: %s", exc)
        return []


async def _search_reviews(db: AsyncSession, org_id: UUID, like: str) -> list[SearchResultItem]:
    try:
        from app.modules.review_intelligence.models import BookReview

        stmt = (
            select(BookReview)
            .where(
                BookReview.org_id == org_id,
                BookReview.body.ilike(like),
            )
            .limit(10)
        )
        result = await db.execute(stmt)
        return [
            SearchResultItem(
                id=r.id,
                title=f"Review ({getattr(r, 'star_rating', '?')}★)",
                snippet=(r.body or "")[:180],
                resource_type="review",
            )
            for r in result.scalars().all()
        ]
    except Exception as exc:
        logger.debug("search reviews failed: %s", exc)
        return []


_SEARCHERS = {
    "projects": _search_projects,
    "books": _search_books,
    "chapters": _search_chapters,
    "recipes": _search_recipes,
    "reviews": _search_reviews,
}


async def search(
    db: AsyncSession,
    org_id: UUID,
    query: str,
    types: list[str] | None = None,
) -> SearchResponse:
    """Run a global search across the given types (defaults to all)."""
    q = (query or "").strip()
    if not q:
        return SearchResponse(query="", results_by_type={}, total_count=0)

    like = f"%{q}%"
    requested = set(types) if types else set(ALL_TYPES)
    requested = requested & ALL_TYPES

    results_by_type: dict[str, list[SearchResultItem]] = {}
    for t in requested:
        searcher = _SEARCHERS.get(t)
        if not searcher:
            continue
        items = await searcher(db, org_id, like)
        results_by_type[t] = items

    total = sum(len(v) for v in results_by_type.values())
    return SearchResponse(query=q, results_by_type=results_by_type, total_count=total)
