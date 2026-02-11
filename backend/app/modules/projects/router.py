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
    """Create a new project.

    TODO: Get organization_id from current_user.
    """
    # Placeholder: use current_user.organization_id
    org_id = current_user.organization_id

    return await service.create_project(
        db,
        organization_id=org_id,
        title=body.title,
        description=body.description,
        project_type=body.project_type,
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
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the current organization."""
    org_id = current_user.organization_id

    request = schemas.ProjectListRequest(
        limit=limit,
        offset=offset,
        project_type=project_type,
        status=status,
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
    """Get project by ID.

    TODO: Add permission check to ensure user belongs to the project's org.
    """
    return await service.get_project(db, project_id)


# ---------------------------------------------------------------------------
# PUT /projects/{project_id}
# ---------------------------------------------------------------------------
@router.put(
    "/{project_id}",
    response_model=schemas.ProjectResponse,
    summary="Update project",
    description="Update project title, description, or status.",
)
async def update_project(
    project_id: UUID,
    body: schemas.ProjectUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update project details.

    TODO: Add permission check.
    """
    return await service.update_project(
        db,
        project_id=project_id,
        title=body.title,
        description=body.description,
        status=body.status,
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
    """Delete a project.

    TODO: Add permission check.
    TODO: Consider soft delete instead of hard delete.
    """
    await service.delete_project(db, project_id)
    return MessageResponse(message=f"Project {project_id} deleted successfully")
