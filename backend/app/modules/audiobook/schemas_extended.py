"""Extended Pydantic schemas for audiobook export & download."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExportRequest(BaseModel):
    """Request body for starting an audiobook export."""

    format: str = Field(
        ...,
        description="Output audio format.",
        pattern="^(mp3|m4b|flac|wav)$",
    )
    include_chapters: bool = Field(
        True,
        description="Include chapter markers in the exported file.",
    )
    include_cover: bool = Field(
        True,
        description="Embed cover art in the exported file.",
    )
    platform: str = Field(
        "generic",
        description="Target distribution platform.",
        pattern="^(acx|findaway|authors_republic|generic)$",
    )


class ExportJobResponse(BaseModel):
    """Response for a single export job."""

    id: UUID
    audiobook_id: UUID
    format: str
    target_platform: str
    status: str
    file_url: str | None = None
    file_size_bytes: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExportListResponse(BaseModel):
    """List of export jobs."""

    items: list[ExportJobResponse]
    total: int


class DownloadResponse(BaseModel):
    """Pre-signed download URL response."""

    download_url: str
    expires_at: datetime
    filename: str
    file_size_bytes: int
