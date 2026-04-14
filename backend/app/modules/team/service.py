"""Service layer for team management (roles + invitations)."""
from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException


class TeamService:
    """All team/role logic lives here; stateless + explicit db session."""

    # ── Roles ─────────────────────────────────────────────────────────────

    @staticmethod
    async def list_roles(db: AsyncSession, org_id: UUID) -> list[dict[str, Any]]:
        rows = (
            await db.execute(
                sa_text(
                    "SELECT id, org_id, name, description, permissions, "
                    "is_system, created_at FROM roles "
                    "WHERE org_id = :oid ORDER BY is_system DESC, name"
                ),
                {"oid": org_id},
            )
        ).mappings().all()
        return [_normalize_role(dict(r)) for r in rows]

    @staticmethod
    async def get_role(db: AsyncSession, org_id: UUID, role_id: UUID) -> dict[str, Any]:
        row = (
            await db.execute(
                sa_text(
                    "SELECT id, org_id, name, description, permissions, "
                    "is_system, created_at FROM roles "
                    "WHERE id = :rid AND org_id = :oid"
                ),
                {"rid": role_id, "oid": org_id},
            )
        ).mappings().first()
        if not row:
            raise AppException(status_code=404, code="ROLE_NOT_FOUND",
                               message="Role not found")
        return _normalize_role(dict(row))

    @staticmethod
    async def create_role(
        db: AsyncSession,
        org_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        role_id = uuid4()
        now = datetime.now(UTC)
        await db.execute(
            sa_text(
                "INSERT INTO roles (id, org_id, name, description, permissions, "
                "is_system, created_at, updated_at) VALUES "
                "(:id, :oid, :n, :d, :p, false, :now, :now)"
            ),
            {
                "id": role_id,
                "oid": org_id,
                "n": data["name"],
                "d": data.get("description"),
                "p": json.dumps(data.get("permissions") or {}),
                "now": now,
            },
        )
        await db.flush()
        return await TeamService.get_role(db, org_id, role_id)

    @staticmethod
    async def update_role(
        db: AsyncSession,
        org_id: UUID,
        role_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        role = await TeamService.get_role(db, org_id, role_id)
        if role["is_system"]:
            raise AppException(status_code=400, code="SYSTEM_ROLE_IMMUTABLE",
                               message="System roles cannot be modified")
        fields = {k: v for k, v in data.items() if v is not None}
        if not fields:
            return role
        set_parts = []
        params: dict[str, Any] = {"rid": role_id, "oid": org_id,
                                  "now": datetime.now(UTC)}
        for k, v in fields.items():
            if k == "permissions":
                set_parts.append("permissions = CAST(:permissions AS JSONB)")
                params["permissions"] = json.dumps(v)
            else:
                set_parts.append(f"{k} = :{k}")
                params[k] = v
        set_parts.append("updated_at = :now")
        await db.execute(
            sa_text(
                f"UPDATE roles SET {', '.join(set_parts)} "
                "WHERE id = :rid AND org_id = :oid"
            ),
            params,
        )
        await db.flush()
        return await TeamService.get_role(db, org_id, role_id)

    @staticmethod
    async def delete_role(db: AsyncSession, org_id: UUID, role_id: UUID) -> None:
        role = await TeamService.get_role(db, org_id, role_id)
        if role["is_system"]:
            raise AppException(status_code=400, code="SYSTEM_ROLE_IMMUTABLE",
                               message="System roles cannot be deleted")
        await db.execute(
            sa_text("DELETE FROM roles WHERE id = :rid AND org_id = :oid"),
            {"rid": role_id, "oid": org_id},
        )
        await db.flush()

    # ── Team members ──────────────────────────────────────────────────────

    @staticmethod
    async def list_team(db: AsyncSession, org_id: UUID) -> list[dict[str, Any]]:
        rows = (
            await db.execute(
                sa_text(
                    """
                    SELECT u.id AS user_id, u.email, u.name,
                           u.role_id, r.name AS role_name,
                           'active' AS status, u.created_at AS joined_at
                    FROM users u
                    LEFT JOIN roles r ON r.id = u.role_id
                    WHERE u.org_id = :oid AND u.deleted_at IS NULL
                    ORDER BY u.created_at
                    """
                ),
                {"oid": org_id},
            )
        ).mappings().all()
        return [dict(r) for r in rows]

    @staticmethod
    async def assign_role(
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        role_id: UUID,
    ) -> None:
        # Validate role belongs to this org
        await TeamService.get_role(db, org_id, role_id)
        result = await db.execute(
            sa_text(
                "UPDATE users SET role_id = :rid, updated_at = :now "
                "WHERE id = :uid AND org_id = :oid AND deleted_at IS NULL"
            ),
            {
                "rid": role_id, "uid": user_id, "oid": org_id,
                "now": datetime.now(UTC),
            },
        )
        if result.rowcount == 0:  # type: ignore[attr-defined]
            raise AppException(status_code=404, code="MEMBER_NOT_FOUND",
                               message="Member not found")
        await db.flush()

    @staticmethod
    async def remove_member(
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
    ) -> None:
        result = await db.execute(
            sa_text(
                "UPDATE users SET deleted_at = :now, updated_at = :now "
                "WHERE id = :uid AND org_id = :oid AND deleted_at IS NULL"
            ),
            {"uid": user_id, "oid": org_id, "now": datetime.now(UTC)},
        )
        if result.rowcount == 0:  # type: ignore[attr-defined]
            raise AppException(status_code=404, code="MEMBER_NOT_FOUND",
                               message="Member not found")
        await db.flush()

    # ── Invitations ───────────────────────────────────────────────────────

    @staticmethod
    async def list_invitations(db: AsyncSession, org_id: UUID) -> list[dict[str, Any]]:
        rows = (
            await db.execute(
                sa_text(
                    "SELECT i.id, i.org_id, i.email, i.role_id, r.name AS role_name, "
                    "i.status, i.expires_at, i.accepted_at, i.created_at "
                    "FROM team_invitations i "
                    "LEFT JOIN roles r ON r.id = i.role_id "
                    "WHERE i.org_id = :oid ORDER BY i.created_at DESC"
                ),
                {"oid": org_id},
            )
        ).mappings().all()
        return [dict(r) for r in rows]

    @staticmethod
    async def invite(
        db: AsyncSession,
        org_id: UUID,
        invited_by: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        await TeamService.get_role(db, org_id, data["role_id"])
        existing = await db.execute(
            sa_text(
                "SELECT id FROM team_invitations "
                "WHERE org_id = :oid AND email = :email AND status = 'pending'"
            ),
            {"oid": org_id, "email": data["email"]},
        )
        if existing.first():
            raise AppException(status_code=409, code="INVITE_EXISTS",
                               message="A pending invitation exists for this email")

        invite_id = uuid4()
        now = datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        expires = now + timedelta(days=7)

        await db.execute(
            sa_text(
                "INSERT INTO team_invitations (id, org_id, email, role_id, "
                "invited_by, message, status, token, expires_at, created_at) "
                "VALUES (:id, :oid, :email, :rid, :ib, :msg, 'pending', "
                ":token, :expires, :now)"
            ),
            {
                "id": invite_id, "oid": org_id, "email": data["email"],
                "rid": data["role_id"], "ib": invited_by,
                "msg": data.get("message"),
                "token": token, "expires": expires, "now": now,
            },
        )
        await db.flush()
        return await TeamService._get_invitation(db, org_id, invite_id)

    @staticmethod
    async def resend_invitation(
        db: AsyncSession,
        org_id: UUID,
        invite_id: UUID,
    ) -> dict[str, Any]:
        invite = await TeamService._get_invitation(db, org_id, invite_id)
        if invite["status"] != "pending":
            raise AppException(status_code=400, code="INVITE_NOT_PENDING",
                               message="Can only resend pending invitations")
        new_token = secrets.token_urlsafe(32)
        new_expires = datetime.now(UTC) + timedelta(days=7)
        await db.execute(
            sa_text(
                "UPDATE team_invitations SET token = :token, expires_at = :exp "
                "WHERE id = :id AND org_id = :oid"
            ),
            {"token": new_token, "exp": new_expires,
             "id": invite_id, "oid": org_id},
        )
        await db.flush()
        return await TeamService._get_invitation(db, org_id, invite_id)

    @staticmethod
    async def _get_invitation(
        db: AsyncSession, org_id: UUID, invite_id: UUID
    ) -> dict[str, Any]:
        row = (
            await db.execute(
                sa_text(
                    "SELECT i.id, i.org_id, i.email, i.role_id, r.name AS role_name, "
                    "i.status, i.expires_at, i.accepted_at, i.created_at "
                    "FROM team_invitations i "
                    "LEFT JOIN roles r ON r.id = i.role_id "
                    "WHERE i.id = :id AND i.org_id = :oid"
                ),
                {"id": invite_id, "oid": org_id},
            )
        ).mappings().first()
        if not row:
            raise AppException(status_code=404, code="INVITE_NOT_FOUND",
                               message="Invitation not found")
        return dict(row)


def _normalize_role(row: dict[str, Any]) -> dict[str, Any]:
    perms = row.get("permissions")
    if isinstance(perms, str):
        try:
            row["permissions"] = json.loads(perms)
        except (TypeError, ValueError):
            row["permissions"] = {}
    elif perms is None:
        row["permissions"] = {}
    return row
