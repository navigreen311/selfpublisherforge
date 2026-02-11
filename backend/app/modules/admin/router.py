"""FastAPI router for admin endpoints (/api/v1/admin/...)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.core.tier_guard import require_module
from app.database import get_db
from app.modules.admin import schemas, service
from app.schemas.common import MessageResponse

router = APIRouter()


# Admin access requires both:
# 1. Enterprise tier (module-level)
# 2. Admin or owner role (endpoint-level)
require_admin = require_module("admin")


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------
@router.get(
    "/users",
    response_model=schemas.UserListResponse,
    summary="List all users",
    description="Get a paginated list of all users with optional filtering.",
)
async def list_users(
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    tier: str | None = None,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    request = schemas.UserListRequest(
        limit=limit,
        offset=offset,
        search=search,
        tier=tier,
    )
    return await service.list_users(db, request)


# ---------------------------------------------------------------------------
# GET /feature-flags
# ---------------------------------------------------------------------------
@router.get(
    "/feature-flags",
    response_model=schemas.FeatureFlagsResponse,
    summary="Get feature flags",
    description="Retrieve all platform feature flags.",
)
async def get_feature_flags(
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all feature flags (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    return await service.get_feature_flags(db)


# ---------------------------------------------------------------------------
# PUT /feature-flags/{flag_key}
# ---------------------------------------------------------------------------
@router.put(
    "/feature-flags/{flag_key}",
    response_model=schemas.FeatureFlag,
    summary="Update feature flag",
    description="Enable or disable a feature flag.",
)
async def update_feature_flag(
    flag_key: str,
    body: schemas.FeatureFlagUpdateRequest,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a feature flag (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    return await service.update_feature_flag(
        db,
        flag_key=flag_key,
        enabled=body.enabled,
        description=body.description,
    )


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}
# ---------------------------------------------------------------------------
@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate user",
    description="Deactivate a user account.",
)
async def deactivate_user(
    user_id: UUID,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user account (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    await service.deactivate_user(db, user_id)
    return MessageResponse(message=f"User {user_id} deactivated successfully")
