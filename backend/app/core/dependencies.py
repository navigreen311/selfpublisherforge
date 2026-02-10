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

    Returns a dict with ``user_id``, ``org_id``, and ``role`` keys.

    Raises
    ------
    HTTPException(401)
        If the token is missing, invalid, or does not contain a subject.
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
        return {
            "user_id": UUID(user_id),
            "org_id": UUID(org_id_raw) if org_id_raw else None,
            "role": payload.get("role", "viewer"),
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


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
