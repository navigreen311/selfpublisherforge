"""Projects service -- CRUD for book/series/course projects."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.project import Project
from app.modules.projects.schemas import (
    ProjectListItem,
    ProjectListRequest,
    ProjectListResponse,
    ProjectResponse,
)

logger = logging.getLogger(__name__)


async def create_project(
    db: AsyncSession,
    organization_id: UUID,
    title: str,
    description: str | None = None,
    project_type: str = "book",
) -> ProjectResponse:
    """Create a new project.

    Args:
        db: Database session
        organization_id: Organization ID
        title: Project title
        description: Project description (optional)
        project_type: Type of project (book, series, course)

    Returns:
        ProjectResponse with created project details
    """
    project = Project(
        title=title,
        description=description,
        project_type=project_type,
        status="planning",
        organization_id=organization_id,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"Created project {project.id} for organization {organization_id}")

    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        organization_id=project.organization_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def get_project(db: AsyncSession, project_id: UUID) -> ProjectResponse:
    """Get project by ID.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        ProjectResponse with project details

    Raises:
        AppException: If project not found
    """
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise AppException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        organization_id=project.organization_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def update_project(
    db: AsyncSession,
    project_id: UUID,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
) -> ProjectResponse:
    """Update project details.

    Args:
        db: Database session
        project_id: Project ID
        title: New title (optional)
        description: New description (optional)
        status: New status (optional)

    Returns:
        Updated ProjectResponse

    Raises:
        AppException: If project not found
    """
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise AppException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    if title is not None:
        project.title = title
    if description is not None:
        project.description = description
    if status is not None:
        project.status = status

    project.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        organization_id=project.organization_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def list_projects(
    db: AsyncSession,
    organization_id: UUID,
    request: ProjectListRequest,
) -> ProjectListResponse:
    """List all projects for an organization.

    Args:
        db: Database session
        organization_id: Organization ID
        request: Filter and pagination parameters

    Returns:
        ProjectListResponse containing projects and total count
    """
    query = select(Project).where(Project.organization_id == organization_id)

    if request.project_type:
        query = query.where(Project.project_type == request.project_type)

    if request.status:
        query = query.where(Project.status == request.status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.limit(request.limit).offset(request.offset).order_by(Project.created_at.desc())

    result = await db.execute(query)
    projects = result.scalars().all()

    project_items = [
        ProjectListItem(
            id=p.id,
            title=p.title,
            project_type=p.project_type,
            status=p.status,
            created_at=p.created_at,
        )
        for p in projects
    ]

    return ProjectListResponse(projects=project_items, total=total)


async def delete_project(db: AsyncSession, project_id: UUID) -> None:
    """Delete a project.

    Args:
        db: Database session
        project_id: Project ID

    Raises:
        AppException: If project not found
    """
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise AppException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    await db.delete(project)
    await db.commit()
    logger.info(f"Deleted project {project_id}")
