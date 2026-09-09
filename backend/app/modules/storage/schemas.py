"""Pydantic schemas for the storage module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AssetType(str, Enum):
    MANUSCRIPT = "manuscript"
    IMAGE = "image"
    COVER = "cover"
    EXPORT = "export"


class AssetStatus(str, Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


class UploadRequest(BaseModel):
    """Request body to obtain a presigned upload URL."""

    file_name: str = Field(..., min_length=1, max_length=255, description="Original file name")
    content_type: str = Field(..., min_length=1, max_length=127, description="MIME type, e.g. application/pdf")
    size: int = Field(..., gt=0, description="File size in bytes")
    asset_type: AssetType = Field(..., description="Logical asset category")


class UploadResponse(BaseModel):
    """Presigned URL and new asset ID returned to the client."""

    upload_url: str
    asset_id: UUID
    expires_in: int = Field(default=3600, description="URL expiration in seconds")


class UploadCompleteRequest(BaseModel):
    """Client confirms that the upload finished."""

    asset_id: UUID


# ---------------------------------------------------------------------------
# Asset CRUD
# ---------------------------------------------------------------------------


class AssetResponse(BaseModel):
    """Public representation of a stored asset."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    file_name: str
    content_type: str
    size: int
    asset_type: AssetType
    status: AssetStatus
    s3_key: str
    download_url: str | None = None
    metadata: dict | None = None
    created_at: datetime
    updated_at: datetime


class AssetListParams(BaseModel):
    """Query parameters for listing assets."""

    asset_type: AssetType | None = None
    cursor: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class ProcessRequest(BaseModel):
    """Trigger async processing on an uploaded asset."""

    action: str = Field(
        default="auto",
        description="Processing action: auto, resize, parse_pdf, generate_thumbnail",
    )
    options: dict | None = None
