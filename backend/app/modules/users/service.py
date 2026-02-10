"""Service layer for User & Organization management.

Handles all business logic: user CRUD, org management, invitation flow,
role validation, session management, and API key operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4
import hashlib
import json
import secrets

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException


# ─── Helpers ──────────────────────────────────────────────────────────────────

_ROLE_HIERARCHY: dict[str, int] = {
    "owner": 100,
    "admin": 80,
    "editor": 60,
    "writer": 40,
    "viewer": 20,
}


def _role_level(role: str) -> int:
    return _ROLE_HIERARCHY.get(role, 0)


def _generate_api_key() -> tuple[str, str]:
    """Return (full_key, prefix) for a new API key."""
    raw = secrets.token_urlsafe(32)
    prefix = raw[:8]
    return raw, prefix


# ─── Service Class ────────────────────────────────────────────────────────────

class UserService:
    """Stateless service; every method receives a db session."""

    # ── User Profile ──────────────────────────────────────────────────────

    @staticmethod
    async def get_user_profile(db: AsyncSession, user_id: UUID) -> dict[str, Any]:
        """Retrieve user profile by id."""
        from app.models.user import User
        from sqlalchemy import select, inspect as sa_inspect

        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise AppException(
                status_code=404,
                code="USER_NOT_FOUND",
                message="User not found",
            )
        # Convert ORM instance to dict using column inspection
        mapper = sa_inspect(User)
        return {col.key: getattr(user, col.key) for col in mapper.mapper.column_attrs}

    @staticmethod
    async def update_user_profile(
        db: AsyncSession,
        user_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update mutable profile fields."""
        data = {k: v for k, v in data.items() if v is not None}
        if not data:
            raise AppException(
                status_code=400,
                code="NO_FIELDS",
                message="No fields to update",
            )
        data["updated_at"] = datetime.now(timezone.utc)

        set_clause = ", ".join(f"{k} = :{k}" for k in data)
        data["user_id"] = user_id
        await db.execute(
            sa_text(f"UPDATE users SET {set_clause} WHERE id = :user_id"),
            data,
        )
        await db.flush()
        return await UserService.get_user_profile(db, user_id)

    @staticmethod
    async def update_preferences(
        db: AsyncSession,
        user_id: UUID,
        preferences: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge-update the JSONB preferences column."""
        await db.execute(
            sa_text(
                "UPDATE users SET preferences = COALESCE(preferences, '{}'::jsonb) || :prefs::jsonb, "
                "updated_at = :now WHERE id = :user_id"
            ),
            {
                "prefs": json.dumps(preferences),
                "now": datetime.now(timezone.utc),
                "user_id": user_id,
            },
        )
        await db.flush()
        return await UserService.get_user_profile(db, user_id)

    # ── Sessions ──────────────────────────────────────────────────────────

    @staticmethod
    async def list_sessions(db: AsyncSession, user_id: UUID) -> list[dict[str, Any]]:
        """Return all active sessions for the user."""
        result = await db.execute(
            sa_text(
                "SELECT id, ip_address, user_agent, created_at, last_active_at "
                "FROM user_sessions WHERE user_id = :uid AND revoked_at IS NULL "
                "ORDER BY last_active_at DESC NULLS LAST"
            ),
            {"uid": user_id},
        )
        return [dict(r) for r in result.mappings().all()]

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        user_id: UUID,
        session_id: UUID,
    ) -> None:
        """Soft-revoke a session."""
        result = await db.execute(
            sa_text(
                "UPDATE user_sessions SET revoked_at = :now "
                "WHERE id = :sid AND user_id = :uid AND revoked_at IS NULL"
            ),
            {
                "now": datetime.now(timezone.utc),
                "sid": session_id,
                "uid": user_id,
            },
        )
        if result.rowcount == 0:
            raise AppException(
                status_code=404,
                code="SESSION_NOT_FOUND",
                message="Session not found or already revoked",
            )

    # ── Organization ──────────────────────────────────────────────────────

    @staticmethod
    async def get_org(db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        """Return organization details."""
        result = await db.execute(
            sa_text("SELECT * FROM organizations WHERE id = :oid AND deleted_at IS NULL"),
            {"oid": org_id},
        )
        row = result.mappings().first()
        if not row:
            raise AppException(
                status_code=404,
                code="ORG_NOT_FOUND",
                message="Organization not found",
            )
        return dict(row)

    @staticmethod
    async def update_org(
        db: AsyncSession,
        org_id: UUID,
        data: dict[str, Any],
        current_user: dict[str, Any],
    ) -> dict[str, Any]:
        """Update organization (owner/admin only)."""
        if current_user["role"] not in ("owner", "admin"):
            raise AppException(
                status_code=403,
                code="FORBIDDEN",
                message="Only owner or admin can update organization settings",
            )
        data = {k: v for k, v in data.items() if v is not None}
        if not data:
            raise AppException(
                status_code=400,
                code="NO_FIELDS",
                message="No fields to update",
            )

        data["updated_at"] = datetime.now(timezone.utc)
        set_clause = ", ".join(f"{k} = :{k}" for k in data)
        data["oid"] = org_id
        await db.execute(
            sa_text(f"UPDATE organizations SET {set_clause} WHERE id = :oid"),
            data,
        )
        await db.flush()
        return await UserService.get_org(db, org_id)

    @staticmethod
    async def list_members(db: AsyncSession, org_id: UUID) -> list[dict[str, Any]]:
        """Return all active members of an organization."""
        result = await db.execute(
            sa_text(
                "SELECT u.id AS user_id, u.email, u.name, u.role, u.created_at AS joined_at "
                "FROM users u WHERE u.org_id = :oid AND u.deleted_at IS NULL "
                "ORDER BY u.created_at"
            ),
            {"oid": org_id},
        )
        return [dict(r) for r in result.mappings().all()]

    @staticmethod
    async def invite_member(
        db: AsyncSession,
        org_id: UUID,
        email: str,
        role: str,
        inviter: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a pending invitation for a user."""
        if inviter["role"] not in ("owner", "admin"):
            raise AppException(
                status_code=403,
                code="FORBIDDEN",
                message="Only owner or admin can invite members",
            )

        # Prevent inviting to a higher role than inviter
        if _role_level(role) >= _role_level(inviter["role"]):
            raise AppException(
                status_code=403,
                code="ROLE_ESCALATION",
                message="Cannot invite to a role equal or higher than your own",
            )

        # Check duplicate pending invites
        existing = await db.execute(
            sa_text(
                "SELECT id FROM invitations "
                "WHERE org_id = :oid AND email = :email AND status = 'pending'"
            ),
            {"oid": org_id, "email": email},
        )
        if existing.first():
            raise AppException(
                status_code=409,
                code="INVITE_EXISTS",
                message="A pending invitation already exists for this email",
            )

        now = datetime.now(timezone.utc)
        invite_id = uuid4()
        expires = now + timedelta(days=7)

        await db.execute(
            sa_text(
                "INSERT INTO invitations (id, org_id, email, role, invited_by, status, created_at, expires_at) "
                "VALUES (:id, :oid, :email, :role, :invited_by, 'pending', :created_at, :expires_at)"
            ),
            {
                "id": invite_id,
                "oid": org_id,
                "email": email,
                "role": role,
                "invited_by": inviter["user_id"],
                "created_at": now,
                "expires_at": expires,
            },
        )
        await db.flush()
        return {
            "id": invite_id,
            "email": email,
            "role": role,
            "invited_at": now,
            "expires_at": expires,
        }

    @staticmethod
    async def change_member_role(
        db: AsyncSession,
        org_id: UUID,
        target_user_id: UUID,
        new_role: str,
        current_user: dict[str, Any],
    ) -> dict[str, Any]:
        """Change a member's role (owner only)."""
        if current_user["role"] != "owner":
            raise AppException(
                status_code=403,
                code="FORBIDDEN",
                message="Only the organization owner can change roles",
            )
        if str(target_user_id) == str(current_user["user_id"]):
            raise AppException(
                status_code=400,
                code="SELF_ROLE_CHANGE",
                message="Cannot change your own role",
            )

        result = await db.execute(
            sa_text(
                "UPDATE users SET role = :role, updated_at = :now "
                "WHERE id = :uid AND org_id = :oid AND deleted_at IS NULL"
            ),
            {
                "role": new_role,
                "now": datetime.now(timezone.utc),
                "uid": target_user_id,
                "oid": org_id,
            },
        )
        if result.rowcount == 0:
            raise AppException(
                status_code=404,
                code="MEMBER_NOT_FOUND",
                message="Member not found in this organization",
            )
        await db.flush()
        return {"user_id": target_user_id, "role": new_role}

    @staticmethod
    async def remove_member(
        db: AsyncSession,
        org_id: UUID,
        target_user_id: UUID,
        current_user: dict[str, Any],
    ) -> None:
        """Remove a member from the organization (admin+)."""
        if current_user["role"] not in ("owner", "admin"):
            raise AppException(
                status_code=403,
                code="FORBIDDEN",
                message="Only owner or admin can remove members",
            )
        if str(target_user_id) == str(current_user["user_id"]):
            raise AppException(
                status_code=400,
                code="SELF_REMOVE",
                message="Cannot remove yourself from the organization",
            )

        # Check target role — can't remove someone of equal/higher rank
        target_result = await db.execute(
            sa_text(
                "SELECT role FROM users WHERE id = :uid AND org_id = :oid AND deleted_at IS NULL"
            ),
            {"uid": target_user_id, "oid": org_id},
        )
        target_row = target_result.mappings().first()
        if not target_row:
            raise AppException(
                status_code=404,
                code="MEMBER_NOT_FOUND",
                message="Member not found in this organization",
            )
        if _role_level(target_row["role"]) >= _role_level(current_user["role"]):
            raise AppException(
                status_code=403,
                code="ROLE_ESCALATION",
                message="Cannot remove a member with equal or higher role",
            )

        await db.execute(
            sa_text(
                "UPDATE users SET deleted_at = :now, updated_at = :now "
                "WHERE id = :uid AND org_id = :oid"
            ),
            {
                "now": datetime.now(timezone.utc),
                "uid": target_user_id,
                "oid": org_id,
            },
        )
        await db.flush()

    # ── API Keys ──────────────────────────────────────────────────────────

    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        org_id: UUID,
        data: dict[str, Any],
        current_user: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new API key for the organization."""
        if current_user["role"] not in ("owner", "admin"):
            raise AppException(
                status_code=403,
                code="FORBIDDEN",
                message="Only owner or admin can create API keys",
            )

        raw_key, prefix = _generate_api_key()
        key_id = uuid4()
        now = datetime.now(timezone.utc)
        expires_at = None
        if data.get("expires_in_days"):
            expires_at = now + timedelta(days=data["expires_in_days"])

        await db.execute(
            sa_text(
                "INSERT INTO api_keys (id, org_id, name, key_hash, prefix, scopes, "
                "created_by, created_at, expires_at, is_active) "
                "VALUES (:id, :oid, :name, :key_hash, :prefix, :scopes, "
                ":created_by, :created_at, :expires_at, true)"
            ),
            {
                "id": key_id,
                "oid": org_id,
                "name": data["name"],
                "key_hash": hashlib.sha256(raw_key.encode()).hexdigest(),
                "prefix": prefix,
                "scopes": json.dumps(data.get("scopes", ["read"])),
                "created_by": current_user["user_id"],
                "created_at": now,
                "expires_at": expires_at,
            },
        )
        await db.flush()
        return {
            "id": key_id,
            "name": data["name"],
            "prefix": prefix,
            "scopes": data.get("scopes", ["read"]),
            "created_at": now,
            "expires_at": expires_at,
            "last_used_at": None,
            "is_active": True,
            "key": raw_key,
        }

    @staticmethod
    async def list_api_keys(db: AsyncSession, org_id: UUID) -> list[dict[str, Any]]:
        """List all API keys for the organization."""
        result = await db.execute(
            sa_text(
                "SELECT id, name, prefix, scopes, created_at, expires_at, "
                "last_used_at, is_active "
                "FROM api_keys WHERE org_id = :oid AND is_active = true "
                "ORDER BY created_at DESC"
            ),
            {"oid": org_id},
        )
        rows = []
        for r in result.mappings().all():
            row = dict(r)
            # scopes may come back as a JSON string
            if isinstance(row.get("scopes"), str):
                row["scopes"] = json.loads(row["scopes"])
            rows.append(row)
        return rows

    @staticmethod
    async def revoke_api_key(
        db: AsyncSession,
        org_id: UUID,
        key_id: UUID,
        current_user: dict[str, Any],
    ) -> None:
        """Revoke (soft-delete) an API key."""
        if current_user["role"] not in ("owner", "admin"):
            raise AppException(
                status_code=403,
                code="FORBIDDEN",
                message="Only owner or admin can revoke API keys",
            )

        result = await db.execute(
            sa_text(
                "UPDATE api_keys SET is_active = false, updated_at = :now "
                "WHERE id = :kid AND org_id = :oid AND is_active = true"
            ),
            {
                "now": datetime.now(timezone.utc),
                "kid": key_id,
                "oid": org_id,
            },
        )
        if result.rowcount == 0:
            raise AppException(
                status_code=404,
                code="API_KEY_NOT_FOUND",
                message="API key not found or already revoked",
            )

