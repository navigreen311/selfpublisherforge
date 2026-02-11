"""Storage API router — presigned uploads, asset CRUD, and processing triggers."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.pagination import PaginatedResponse
from app.database import get_db
from app.modules.storage.schemas import (
    AssetResponse,
    AssetType,
    ProcessRequest,
    UploadCompleteRequest,
    UploadRequest,
    UploadResponse,
)
from app.modules.storage.service import StorageService
from app.schemas.common import MessageResponse

router = APIRouter()


def _service(db: AsyncSession) -> StorageService:
    return StorageService(db=db)


# ---------------------------------------------------------------------------
# POST /upload — get presigned upload URL
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
    summary="Request presigned upload URL",
    description="Validate file metadata and return a presigned S3 PUT URL for direct upload.",
)
async def request_upload(
    body: UploadRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """Validate file metadata and return a presigned S3 PUT URL."""
    svc = _service(db)
    return await svc.create_presigned_upload(
        org_id=current_user["org_id"],
        file_name=body.file_name,
        content_type=body.content_type,
        size=body.size,
        asset_type=body.asset_type,
    )


# ---------------------------------------------------------------------------
# POST /upload/complete — confirm upload
# ---------------------------------------------------------------------------

@router.post(
    "/upload/complete",
    response_model=AssetResponse,
    summary="Complete file upload",
    description="Confirm that the file has been uploaded to S3 and mark the asset as uploaded.",
)
async def complete_upload(
    body: UploadCompleteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    """Confirm that the file has been uploaded to S3 and mark the asset as uploaded."""
    svc = _service(db)
    return await svc.complete_upload(
        asset_id=body.asset_id,
        org_id=current_user["org_id"],
    )


# ---------------------------------------------------------------------------
# GET /assets — list org assets (paginated, filterable by type)
# ---------------------------------------------------------------------------

@router.get(
    "/assets",
    response_model=PaginatedResponse[AssetResponse],
    summary="List assets",
    description="List assets belonging to the organization with optional type filter.",
)
async def list_assets(
    asset_type: AssetType | None = None,
    cursor: str | None = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List assets belonging to the caller's organisation."""
    svc = _service(db)
    return await svc.list_assets(
        org_id=current_user["org_id"],
        asset_type=asset_type,
        cursor=cursor,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# GET /assets/{id} — get asset details + download URL
# ---------------------------------------------------------------------------

@router.get(
    "/assets/{asset_id}",
    response_model=AssetResponse,
    summary="Get asset detail",
    description="Return asset details including a presigned download URL.",
)
async def get_asset(
    asset_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    """Return asset details including a presigned download URL."""
    svc = _service(db)
    return await svc.get_asset(
        asset_id=asset_id,
        org_id=current_user["org_id"],
    )


# ---------------------------------------------------------------------------
# DELETE /assets/{id} — soft-delete asset
# ---------------------------------------------------------------------------

@router.delete(
    "/assets/{asset_id}",
    response_model=MessageResponse,
    summary="Delete asset",
    description="Soft-delete an asset by setting a deleted_at timestamp.",
)
async def delete_asset(
    asset_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Soft-delete an asset (sets deleted_at timestamp)."""
    svc = _service(db)
    await svc.delete_asset(
        asset_id=asset_id,
        org_id=current_user["org_id"],
    )
    return MessageResponse(message="Asset deleted successfully.")


# ---------------------------------------------------------------------------
# POST /assets/{id}/process — trigger processing
# ---------------------------------------------------------------------------

@router.post(
    "/assets/{asset_id}/process",
    response_model=AssetResponse,
    summary="Process asset",
    description="Trigger asynchronous processing (image resize, PDF parse, etc.) on an asset.",
)
async def process_asset(
    asset_id: UUID,
    body: ProcessRequest | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    """Trigger asynchronous processing (image resize, PDF parse, etc.)."""
    body = body or ProcessRequest()
    svc = _service(db)
    return await svc.trigger_processing(
        asset_id=asset_id,
        org_id=current_user["org_id"],
        action=body.action,
        options=body.options,
    )
