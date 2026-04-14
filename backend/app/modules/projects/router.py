"""FastAPI router for projects endpoints (/api/v1/projects/...)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.projects import schemas, service
from app.schemas.common import MessageResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /projects
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=schemas.ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="Create a new book, series, or course project.",
)
async def create_project(
    body: schemas.ProjectCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    org_id = current_user["org_id"]

    return await service.create_project(
        db,
        organization_id=org_id,
        title=body.title,
        description=body.description,
        project_type=body.project_type,
        book_type=body.book_type,
        target_launch_date=body.target_launch_date,
        genre=body.genre,
        subgenre=body.subgenre,
        target_audience=body.target_audience,
        keywords=body.keywords,
        target_word_count=body.target_word_count,
        target_date=body.target_date,
        marketplace=body.marketplace,
        template=body.template,
        cover_image_url=body.cover_image_url,
        language=body.language,
        content_rating=body.content_rating,
        has_ai_content=body.has_ai_content,
        is_public_domain=body.is_public_domain,
    )


# ---------------------------------------------------------------------------
# GET /projects
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=schemas.ProjectListResponse,
    summary="List projects",
    description="Get all projects for the current organization.",
)
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    project_type: str | None = None,
    status: str | None = None,
    book_type: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the current organization."""
    org_id = current_user["org_id"]

    request = schemas.ProjectListRequest(
        limit=limit,
        offset=offset,
        project_type=project_type,
        status=status,
        book_type=book_type,
        search=search,
        sort=sort,
    )

    return await service.list_projects(db, org_id, request)


# ---------------------------------------------------------------------------
# GET /projects/{project_id}
# ---------------------------------------------------------------------------
@router.get(
    "/{project_id}",
    response_model=schemas.ProjectResponse,
    summary="Get project",
    description="Retrieve project details by ID.",
)
async def get_project(
    project_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project by ID."""
    project = await service.get_project(db, project_id, current_user["org_id"])
    return project


# ---------------------------------------------------------------------------
# PUT /projects/{project_id}
# ---------------------------------------------------------------------------
@router.api_route(
    "/{project_id}",
    methods=["PUT", "PATCH"],
    response_model=schemas.ProjectResponse,
    summary="Update project",
    description="Update project fields (PATCH/PUT both supported).",
)
async def update_project(
    project_id: UUID,
    body: schemas.ProjectUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update project details."""
    return await service.update_project(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
        user_role=current_user["role"],
        title=body.title,
        description=body.description,
        book_type=body.book_type,
        target_launch_date=body.target_launch_date,
        status=body.status,
        genre=body.genre,
        subgenre=body.subgenre,
        target_audience=body.target_audience,
        keywords=body.keywords,
        target_word_count=body.target_word_count,
        target_date=body.target_date,
        marketplace=body.marketplace,
        template=body.template,
        cover_image_url=body.cover_image_url,
        language=body.language,
        content_rating=body.content_rating,
        has_ai_content=body.has_ai_content,
        is_public_domain=body.is_public_domain,
    )


# ---------------------------------------------------------------------------
# DELETE /projects/{project_id}
# ---------------------------------------------------------------------------
@router.delete(
    "/{project_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete project",
    description="Delete a project and all associated data.",
)
async def delete_project(
    project_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a project."""
    await service.delete_project(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
        user_role=current_user["role"],
    )
    return MessageResponse(message=f"Project {project_id} deleted successfully")
