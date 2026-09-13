"""
FastAPI dependency injection utilities.

Provides ``get_current_user`` for JWT-based authentication and
``require_role`` for role-based access control.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract and validate the current user from a JWT bearer token.

    Returns a dict with ``user_id``, ``org_id``, and ``role`` keys. ``org_id``
    is always a UUID, never None — see below.

    Raises
    ------
    HTTPException(401)
        If the token is missing, invalid, lacks a subject, or carries no
        organization.
    """
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        org_id_raw = payload.get("org_id", "")
        if not org_id_raw:
            # Every tenant-scoped query in this codebase reads
            # current_user["org_id"] and passes it straight into a filter.
            # Returning None here meant those became `org_id IS NULL` rather
            # than a refusal, across ~470 call sites. A token with no
            # organization cannot be used for anything, so reject it at the
            # boundary instead.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing organization",
            )
        return {
            "user_id": UUID(user_id),
            "org_id": UUID(org_id_raw),
            "role": payload.get("role", "viewer"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e


def require_role(*roles: str):
    """Create a FastAPI dependency that enforces role-based access.

    Usage::

        @router.get("/admin")
        async def admin_endpoint(user=Depends(require_role("admin", "owner"))):
            ...
    """

    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


async def require_platform_admin(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Require the caller to be a platform administrator.

    Distinct from ``require_role("admin", "owner")``, which asks about a role
    *within an organization*. Everything under ``/admin`` is platform-wide —
    it lists users across every tenant and sets global feature flags — so an
    organization role is the wrong question to ask there.

    The bit is read from the database rather than the token, so revoking it
    takes effect on the next request instead of whenever the access token
    happens to expire.
    """
    from sqlalchemy import select

    from app.models.user import User

    result = await db.execute(select(User.is_platform_admin).where(User.id == current_user["user_id"]))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator access required",
        )
    return current_user
