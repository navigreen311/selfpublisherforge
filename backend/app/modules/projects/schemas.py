"""Pydantic request/response schemas for the projects module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class ProjectCreateRequest(BaseModel):
    """Request to create a new project."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    project_type: str = Field(default="book", pattern="^(book|series|course)$")


class ProjectUpdateRequest(BaseModel):
    """Request to update project details."""
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: str | None = Field(None, pattern="^(planning|in_progress|completed|archived)$")


class ProjectListRequest(BaseModel):
    """Request parameters for listing projects."""
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    project_type: str | None = None
    status: str | None = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class ProjectResponse(BaseModel):
    """Project details."""
    id: UUID
    title: str
    description: str | None
    project_type: str
    status: str
    organization_id: UUID
    created_at: datetime
    updated_at: datetime


class ProjectListItem(BaseModel):
    """Project summary for list view."""
    id: UUID
    title: str
    project_type: str
    status: str
    created_at: datetime


class ProjectListResponse(BaseModel):
    """Response containing list of projects."""
    projects: list[ProjectListItem]
    total: int
