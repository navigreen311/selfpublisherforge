"""Pydantic request/response schemas for the projects module."""

from datetime import date, datetime
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
    book_type: str | None = Field(
        None,
        description=(
            "Project book type: nonfiction, fiction, childrens, coloring, "
            "puzzle, comic, cookbook, other."
        ),
    )
    target_launch_date: date | None = None
    genre: str | None = None
    subgenre: str | None = None
    pen_name: str | None = None
    target_audience: str | None = None
    keywords: list[str] | None = Field(None, max_length=20)
    target_word_count: int | None = Field(None, ge=1000, le=500000)
    target_date: date | None = None
    marketplace: str | None = Field(None, pattern="^(kdp|ingram_spark|d2d|acx|multiple)$")
    template: str | None = None
    cover_image_url: str | None = None
    language: str | None = Field(None, max_length=10)
    content_rating: str | None = Field(None, pattern="^(general|mature)$")
    has_ai_content: bool = False
    is_public_domain: bool = False


class ProjectUpdateRequest(BaseModel):
    """Request to update project details."""
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    book_type: str | None = None
    target_launch_date: date | None = None
    status: str | None = Field(None, pattern="^(planning|in_progress|completed|archived|draft|active)$")
    genre: str | None = None
    subgenre: str | None = None
    target_audience: str | None = None
    keywords: list[str] | None = None
    target_word_count: int | None = Field(None, ge=1000, le=500000)
    target_date: date | None = None
    marketplace: str | None = None
    template: str | None = None
    cover_image_url: str | None = None
    language: str | None = None
    content_rating: str | None = None
    has_ai_content: bool | None = None
    is_public_domain: bool | None = None


class ProjectListRequest(BaseModel):
    """Request parameters for listing projects."""
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    project_type: str | None = None
    status: str | None = None
    book_type: str | None = None
    search: str | None = None
    sort: str | None = Field(
        default=None,
        description="Sort key: created_at, -created_at, title, -title, target_date, -target_date.",
    )


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class ProjectModuleProgress(BaseModel):
    """Linked module summary for a project."""
    module_type: str
    status: str
    progress_pct: int = 0
    count: int = 0


class ProjectResponse(BaseModel):
    """Project details."""
    id: UUID
    title: str
    description: str | None
    project_type: str
    book_type: str | None = None
    target_launch_date: date | None = None
    status: str
    organization_id: UUID
    linked_modules: list[ProjectModuleProgress] = []
    genre: str | None = None
    subgenre: str | None = None
    target_audience: str | None = None
    keywords: list[str] | None = None
    target_word_count: int | None = None
    target_date: date | None = None
    marketplace: str | None = None
    template: str | None = None
    cover_image_url: str | None = None
    language: str | None = None
    content_rating: str | None = None
    has_ai_content: bool = False
    is_public_domain: bool = False
    created_at: datetime
    updated_at: datetime


class ProjectListItem(BaseModel):
    """Project summary for list view."""
    id: UUID
    title: str
    project_type: str
    status: str
    book_type: str | None = None
    target_launch_date: date | None = None
    genre: str | None = None
    target_date: date | None = None
    target_word_count: int | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Response containing list of projects."""
    projects: list[ProjectListItem]
    total: int
