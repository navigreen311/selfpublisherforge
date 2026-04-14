"""Reusable FastAPI permission dependencies for the RBAC system.

Usage::

    from app.modules.team.permissions import require_permission

    @router.post(
        "/cookbooks",
        dependencies=[Depends(require_permission("cookbooks", "create"))],
    )
    async def create_cookbook(...): ...

The dependency loads the caller's effective permissions by joining the
``users`` row to its ``role_id`` (or, for legacy users, by mapping
``users.role`` to the matching system role). It raises ``403`` when the
requested ``(module, action)`` entry is missing or False.

Action is one of: ``view``, ``create``, ``edit``, ``delete``, ``publish``.
"""
from __future__ import annotations

from typing import Any, Literal, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db

Action = Literal["view", "create", "edit", "delete", "publish"]

# Mapping from legacy ``users.role`` enum to the system role name seeded by
# migration 022. Used as a fallback when users have no ``role_id`` yet.
_LEGACY_ROLE_MAP = {
    "owner": "Owner",
    "admin": "Admin",
    "editor": "Editor",
    "writer": "Editor",
    "designer": "Designer",
    "viewer": "Viewer",
    "va": "VA",
}


async def load_effective_permissions(
    db: AsyncSession,
    user_id: UUID,
    org_id: Optional[UUID],
    legacy_role: Optional[str] = None,
) -> dict[str, dict[str, bool]]:
    """Return the ``permissions`` JSONB dict for the given user.

    Looks up ``users.role_id`` first; if missing, falls back to the system
    role matching ``users.role`` (legacy). Returns ``{}`` if nothing matches
    (which will deny every permission check).
    """
    row = (
        await db.execute(
            sa_text(
                """
                SELECT r.permissions
                FROM users u
                LEFT JOIN roles r ON r.id = u.role_id
                WHERE u.id = :uid
                LIMIT 1
                """
            ),
            {"uid": user_id},
        )
    ).mappings().first()

    if row and row["permissions"]:
        perms = row["permissions"]
        if isinstance(perms, str):
            import json
            try:
                perms = json.loads(perms)
            except (TypeError, ValueError):
                perms = {}
        return perms or {}

    # Legacy fallback — look up system role by name for this org.
    if legacy_role and org_id is not None:
        name = _LEGACY_ROLE_MAP.get(legacy_role.lower())
        if name:
            row = (
                await db.execute(
                    sa_text(
                        "SELECT permissions FROM roles "
                        "WHERE org_id = :oid AND name = :n AND is_system = true"
                    ),
                    {"oid": org_id, "n": name},
                )
            ).mappings().first()
            if row and row["permissions"]:
                perms = row["permissions"]
                if isinstance(perms, str):
                    import json
                    try:
                        perms = json.loads(perms)
                    except (TypeError, ValueError):
                        perms = {}
                return perms or {}

    return {}


def require_permission(module: str, action: Action):
    """FastAPI dependency factory for permission enforcement.

    Grants access when ``permissions[module][action]`` is truthy. Owners
    (legacy role) are always allowed as a safety hatch so the org cannot
    lock itself out during migration.
    """

    async def _checker(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        # Safety hatch: legacy owners always allowed. This is especially
        # important pre-022 migration run in the live DB.
        if current_user.get("role") == "owner":
            return current_user

        perms = await load_effective_permissions(
            db,
            current_user["user_id"],
            current_user.get("org_id"),
            legacy_role=current_user.get("role"),
        )
        mod_perms = perms.get(module) or {}
        if not mod_perms.get(action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for {module}:{action}",
            )
        return current_user

    return _checker
