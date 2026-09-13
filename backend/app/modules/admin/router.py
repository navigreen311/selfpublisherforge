"""FastAPI router for admin endpoints (/api/v1/admin/...)."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_platform_admin, require_role
from app.core.tier_guard import require_module
from app.database import get_db
from app.modules.admin import schemas, service
from app.schemas.common import MessageResponse

# Every endpoint in this router is platform-wide: `list_users` selects across
# all tenants, the feature flags carry no org_id, and `get_organizations`
# enumerates every organization. The guard therefore belongs on the router, so
# an endpoint added later cannot quietly omit it.
#
# `require_admin` below is a *tier* check despite its name — require_module
# asks whether the org's plan includes the admin module. It is not a role or a
# permission check, and on its own it let any Enterprise org's owner read
# every tenant's users.
router = APIRouter(dependencies=[Depends(require_platform_admin)])


# Admin access requires all three:
# 1. Platform administrator (router-level, above)
# 2. Enterprise tier (module-level)
# 3. Admin or owner role (endpoint-level)
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
    result = await service.deactivate_user(db, user_id)
    return MessageResponse(message=result["message"])


# ---------------------------------------------------------------------------
# GET /stats
# ---------------------------------------------------------------------------
@router.get(
    "/stats",
    response_model=schemas.PlatformStatsResponse,
    summary="Get platform statistics",
    description="Get platform-wide statistics including users, organizations, and books.",
)
async def get_platform_stats(
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get platform statistics (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    return await service.get_platform_stats(db)


# ---------------------------------------------------------------------------
# GET /activity
# ---------------------------------------------------------------------------
@router.get(
    "/activity",
    response_model=schemas.ActivityLogResponse,
    summary="Get activity log",
    description="Get activity log with optional filtering.",
)
async def get_activity_log(
    action: str | None = Query(None, description="Filter by action type"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    from_date: datetime | None = Query(None, description="Filter from date"),
    to_date: datetime | None = Query(None, description="Filter to date"),
    limit: int = Query(50, ge=1, le=500, description="Number of entries to return"),
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get activity log (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    filters = schemas.ActivityLogFilters(
        action=action,
        resource_type=resource_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
    return await service.get_activity_log(db, filters)


# ---------------------------------------------------------------------------
# GET /users/{user_id}
# ---------------------------------------------------------------------------
@router.get(
    "/users/{user_id}",
    response_model=schemas.AdminUserDetail,
    summary="Get user detail",
    description="Get detailed information about a specific user.",
)
async def get_user_detail(
    user_id: UUID,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get user detail (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    return await service.get_user_detail(db, user_id)


# ---------------------------------------------------------------------------
# POST /users/invite
# ---------------------------------------------------------------------------
@router.post(
    "/users/invite",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Invite user",
    description="Invite a new user to the platform.",
)
async def invite_user(
    body: schemas.InviteUserRequest,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Invite a user (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    result = await service.invite_user(db, current_user.organization_id, body)
    return MessageResponse(message=result["message"])


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}
# ---------------------------------------------------------------------------
@router.patch(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="Update user",
    description="Update user settings including role and status.",
)
async def update_user(
    user_id: UUID,
    body: schemas.UpdateUserRequest,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    result = await service.update_user(db, user_id, body)
    return MessageResponse(message=result["message"])


# ---------------------------------------------------------------------------
# POST /users/{user_id}/reset-password
# ---------------------------------------------------------------------------
@router.post(
    "/users/{user_id}/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset user password",
    description="Send password reset email to user.",
)
async def reset_user_password(
    user_id: UUID,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reset user password (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    result = await service.reset_user_password(db, user_id)
    return MessageResponse(message=result["message"])


# ---------------------------------------------------------------------------
# POST /users/{user_id}/deactivate
# ---------------------------------------------------------------------------
@router.post(
    "/users/{user_id}/deactivate",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate user",
    description="Deactivate a user account (alternative endpoint).",
)
async def deactivate_user_post(
    user_id: UUID,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user account (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    result = await service.deactivate_user(db, user_id)
    return MessageResponse(message=result["message"])


# ---------------------------------------------------------------------------
# GET /organizations
# ---------------------------------------------------------------------------
@router.get(
    "/organizations",
    response_model=list[schemas.AdminOrgDetail],
    summary="List organizations",
    description="Get a list of all organizations with details.",
)
async def get_organizations(
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List organizations (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    return await service.get_organizations(db)


# ---------------------------------------------------------------------------
# GET /organizations/{org_id}
# ---------------------------------------------------------------------------
@router.get(
    "/organizations/{org_id}",
    response_model=schemas.AdminOrgDetail,
    summary="Get organization detail",
    description="Get detailed information about a specific organization.",
)
async def get_org_detail(
    org_id: UUID,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get organization detail (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    return await service.get_org_detail(db, org_id)


# ---------------------------------------------------------------------------
# PATCH /organizations/{org_id}
# ---------------------------------------------------------------------------
@router.patch(
    "/organizations/{org_id}",
    response_model=MessageResponse,
    summary="Update organization",
    description="Update organization settings.",
)
async def update_org(
    org_id: UUID,
    body: schemas.UpdateOrgRequest,
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update organization (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    result = await service.update_org(db, org_id, body)
    return MessageResponse(message=result["message"])


# ---------------------------------------------------------------------------
# GET /billing
# ---------------------------------------------------------------------------
@router.get(
    "/billing",
    response_model=schemas.BillingOverview,
    summary="Get billing overview",
    description="Get billing overview for the current organization.",
)
async def get_billing_overview(
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get billing overview (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    return await service.get_billing_overview(db, current_user.organization_id)


# ---------------------------------------------------------------------------
# GET /billing/usage
# ---------------------------------------------------------------------------
@router.get(
    "/billing/usage",
    summary="Get billing usage",
    description="Get current billing usage for the organization.",
)
async def get_billing_usage(
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get billing usage (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    return await service.get_billing_usage(db, current_user.organization_id)


# ---------------------------------------------------------------------------
# GET /billing/invoices
# ---------------------------------------------------------------------------
@router.get(
    "/billing/invoices",
    summary="Get billing invoices",
    description="Get invoice history for the organization.",
)
async def get_billing_invoices(
    current_user=Depends(require_role("admin", "owner")),
    _tier_check=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get billing invoices (admin only).

    Requires Enterprise tier and admin/owner role.
    """
    # Return empty list for now - would integrate with billing service
    return {"invoices": []}
