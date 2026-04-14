"""Service layer for Pen Name Management."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException


class PenNameService:
    @staticmethod
    async def list_pen_names(db: AsyncSession, org_id: UUID) -> list[dict[str, Any]]:
        rows = (
            await db.execute(
                sa_text(
                    "SELECT id, org_id, user_id, display_name, name, bio, "
                    "amazon_author_url, photo_url, genres, is_default, "
                    "book_count, created_at, updated_at "
                    "FROM pen_names "
                    "WHERE org_id = :oid AND deleted_at IS NULL "
                    "ORDER BY is_default DESC, display_name"
                ),
                {"oid": org_id},
            )
        ).mappings().all()
        return [_normalize(dict(r)) for r in rows]

    @staticmethod
    async def get(db: AsyncSession, org_id: UUID, pen_name_id: UUID) -> dict[str, Any]:
        row = (
            await db.execute(
                sa_text(
                    "SELECT id, org_id, user_id, display_name, name, bio, "
                    "amazon_author_url, photo_url, genres, is_default, "
                    "book_count, created_at, updated_at "
                    "FROM pen_names WHERE id = :id AND org_id = :oid "
                    "AND deleted_at IS NULL"
                ),
                {"id": pen_name_id, "oid": org_id},
            )
        ).mappings().first()
        if not row:
            raise AppException(status_code=404, code="PEN_NAME_NOT_FOUND",
                               message="Pen name not found")
        return _normalize(dict(row))

    @staticmethod
    async def create(
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        pid = uuid4()
        now = datetime.now(UTC)
        is_default = bool(data.get("is_default"))
        if is_default:
            await _unset_defaults(db, org_id)
        await db.execute(
            sa_text(
                "INSERT INTO pen_names (id, org_id, user_id, name, display_name, "
                "bio, amazon_author_url, photo_url, genres, is_default, "
                "book_count, active, created_at, updated_at) VALUES "
                "(:id, :oid, :uid, :name, :dn, :bio, :url, :photo, :genres, "
                ":default, 0, true, :now, :now)"
            ),
            {
                "id": pid, "oid": org_id, "uid": user_id,
                "name": data["display_name"],
                "dn": data["display_name"],
                "bio": data.get("bio"),
                "url": data.get("amazon_author_url"),
                "photo": data.get("photo_url"),
                "genres": data.get("genres") or [],
                "default": is_default,
                "now": now,
            },
        )
        await db.flush()
        return await PenNameService.get(db, org_id, pid)

    @staticmethod
    async def update(
        db: AsyncSession,
        org_id: UUID,
        pen_name_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        await PenNameService.get(db, org_id, pen_name_id)
        fields = {k: v for k, v in data.items() if v is not None}
        if not fields:
            return await PenNameService.get(db, org_id, pen_name_id)
        if fields.get("is_default") is True:
            await _unset_defaults(db, org_id, exclude_id=pen_name_id)

        set_parts = []
        params: dict[str, Any] = {
            "id": pen_name_id, "oid": org_id, "now": datetime.now(UTC),
        }
        for k, v in fields.items():
            if k == "display_name":
                # keep legacy `name` in sync for back-compat
                set_parts.append("display_name = :display_name")
                set_parts.append("name = :display_name")
                params["display_name"] = v
            else:
                set_parts.append(f"{k} = :{k}")
                params[k] = v
        set_parts.append("updated_at = :now")
        await db.execute(
            sa_text(
                f"UPDATE pen_names SET {', '.join(set_parts)} "
                "WHERE id = :id AND org_id = :oid"
            ),
            params,
        )
        await db.flush()
        return await PenNameService.get(db, org_id, pen_name_id)

    @staticmethod
    async def delete(db: AsyncSession, org_id: UUID, pen_name_id: UUID) -> None:
        pn = await PenNameService.get(db, org_id, pen_name_id)
        if pn.get("is_default"):
            raise AppException(status_code=400, code="CANNOT_DELETE_DEFAULT",
                               message="Cannot delete the default pen name")
        await db.execute(
            sa_text(
                "UPDATE pen_names SET deleted_at = :now, updated_at = :now "
                "WHERE id = :id AND org_id = :oid"
            ),
            {"id": pen_name_id, "oid": org_id, "now": datetime.now(UTC)},
        )
        await db.flush()

    @staticmethod
    async def list_books(
        db: AsyncSession, org_id: UUID, pen_name_id: UUID
    ) -> list[dict[str, Any]]:
        await PenNameService.get(db, org_id, pen_name_id)
        rows = (
            await db.execute(
                sa_text(
                    "SELECT id, title, type, status FROM projects "
                    "WHERE org_id = :oid AND pen_name_id = :pid "
                    "AND deleted_at IS NULL ORDER BY created_at DESC"
                ),
                {"oid": org_id, "pid": pen_name_id},
            )
        ).mappings().all()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("type") is not None:
                d["type"] = str(d["type"])
            if d.get("status") is not None:
                d["status"] = str(d["status"])
            result.append(d)
        return result

    @staticmethod
    async def get_analytics(
        db: AsyncSession,
        org_id: UUID,
        pen_name_id: UUID,
        period: str = "30d",
    ) -> dict[str, Any]:
        """Aggregate revenue/sales/books for this pen name.

        Keeps queries defensive: if analytics tables are absent on a given
        environment, falls back to zeros and the book count.
        """
        await PenNameService.get(db, org_id, pen_name_id)

        books_row = (
            await db.execute(
                sa_text(
                    "SELECT COUNT(*) AS c FROM projects "
                    "WHERE org_id = :oid AND pen_name_id = :pid "
                    "AND deleted_at IS NULL"
                ),
                {"oid": org_id, "pid": pen_name_id},
            )
        ).mappings().first()
        books_count = (books_row or {}).get("c", 0) or 0

        revenue = 0.0
        sales = 0
        avg_rating = None
        try:
            row = (
                await db.execute(
                    sa_text(
                        """
                        SELECT COALESCE(SUM(rr.revenue), 0) AS revenue,
                               COALESCE(SUM(rr.units), 0) AS sales
                        FROM royalty_records rr
                        JOIN books b ON b.id = rr.book_id
                        JOIN projects p ON p.id = b.project_id
                        WHERE p.org_id = :oid AND p.pen_name_id = :pid
                        """
                    ),
                    {"oid": org_id, "pid": pen_name_id},
                )
            ).mappings().first()
            if row:
                revenue = float(row.get("revenue") or 0)
                sales = int(row.get("sales") or 0)
        except Exception:
            pass

        return {
            "revenue": revenue,
            "sales": sales,
            "books_count": int(books_count),
            "avg_rating": avg_rating,
            "period": period,
        }


async def _unset_defaults(
    db: AsyncSession, org_id: UUID, exclude_id: UUID | None = None
) -> None:
    if exclude_id is not None:
        await db.execute(
            sa_text(
                "UPDATE pen_names SET is_default = false "
                "WHERE org_id = :oid AND id != :id AND is_default = true"
            ),
            {"oid": org_id, "id": exclude_id},
        )
    else:
        await db.execute(
            sa_text(
                "UPDATE pen_names SET is_default = false "
                "WHERE org_id = :oid AND is_default = true"
            ),
            {"oid": org_id},
        )


def _normalize(row: dict[str, Any]) -> dict[str, Any]:
    # Fallbacks for rows that predate migration 021.
    if not row.get("display_name"):
        row["display_name"] = row.get("name") or ""
    genres = row.get("genres")
    if genres is None:
        row["genres"] = []
    elif isinstance(genres, str):
        try:
            row["genres"] = json.loads(genres)
        except (TypeError, ValueError):
            row["genres"] = []
    return row
