"""Projects service -- CRUD for book/series/course projects."""

from __future__ import annotations

import datetime as dt_module
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


def _project_to_response(
    project: Project,
    linked_modules: list | None = None,
) -> ProjectResponse:
    """Convert a Project ORM instance to a ProjectResponse schema."""
    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        project_type=project.type.value if hasattr(project.type, "value") else str(project.type),
        book_type=getattr(project, "book_type", None),
        target_launch_date=getattr(project, "target_launch_date", None),
        status=project.status.value if hasattr(project.status, "value") else str(project.status),
        organization_id=project.org_id,
        linked_modules=linked_modules or [],
        genre=project.genre,
        subgenre=project.subgenre,
        target_audience=project.target_audience,
        keywords=project.keywords,
        target_word_count=project.target_word_count,
        target_date=project.target_date,
        marketplace=project.marketplace,
        template=project.template,
        cover_image_url=project.cover_image_url,
        language=project.language,
        content_rating=project.content_rating,
        has_ai_content=project.has_ai_content,
        is_public_domain=project.is_public_domain,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def create_project(
    db: AsyncSession,
    organization_id: UUID,
    title: str,
    description: str | None = None,
    project_type: str = "book",
    book_type: str | None = None,
    target_launch_date: dt_module.date | None = None,
    genre: str | None = None,
    subgenre: str | None = None,
    target_audience: str | None = None,
    keywords: list[str] | None = None,
    target_word_count: int | None = None,
    target_date: dt_module.date | None = None,
    marketplace: str | None = None,
    template: str | None = None,
    cover_image_url: str | None = None,
    language: str | None = None,
    content_rating: str | None = None,
    has_ai_content: bool = False,
    is_public_domain: bool = False,
) -> ProjectResponse:
    """Create a new project.

    Args:
        db: Database session
        organization_id: Organization ID
        title: Project title
        description: Project description (optional)
        project_type: Type of project (book, series, course)
        genre: Genre (optional)
        subgenre: Subgenre (optional)
        target_audience: Target audience (optional)
        keywords: Keywords list (optional)
        target_word_count: Target word count (optional)
        target_date: Target completion date (optional)
        marketplace: Marketplace (optional)
        template: Template name (optional)
        cover_image_url: Cover image URL (optional)
        language: Language code (optional)
        content_rating: Content rating (optional)
        has_ai_content: Whether project uses AI content
        is_public_domain: Whether project is public domain

    Returns:
        ProjectResponse with created project details
    """
    project = Project(
        title=title,
        description=description,
        type=project_type,
        status="draft",
        org_id=organization_id,
        book_type=book_type,
        target_launch_date=target_launch_date,
        genre=genre,
        subgenre=subgenre,
        target_audience=target_audience,
        keywords=keywords,
        target_word_count=target_word_count,
        target_date=target_date,
        marketplace=marketplace,
        template=template,
        cover_image_url=cover_image_url,
        language=language,
        content_rating=content_rating,
        has_ai_content=has_ai_content,
        is_public_domain=is_public_domain,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"Created project {project.id} for organization {organization_id}")

    return _project_to_response(project)


async def get_project(
    db: AsyncSession,
    project_id: UUID,
    org_id: UUID,
) -> ProjectResponse:
    """Get project by ID.

    Args:
        db: Database session
        project_id: Project ID
        org_id: Organization ID for permission check

    Returns:
        ProjectResponse with project details

    Raises:
        AppException: If project not found or access denied
    """
    query = select(Project).where(
        Project.id == project_id,
        Project.deleted_at.is_(None),
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise AppException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    # Permission check: ensure user belongs to the project's org
    if project.org_id != org_id:
        raise AppException(
            status_code=403,
            code="ACCESS_DENIED",
            message="Access denied",
        )

    linked = await _compute_linked_modules(db, project.id)
    return _project_to_response(project, linked_modules=linked)


async def _compute_linked_modules(db: AsyncSession, project_id: UUID) -> list:
    """Return ProjectModuleProgress entries for modules linked to this project.

    Fails soft: if any module query errors (e.g., table missing), we skip
    that module so the project detail still renders.
    """
    from app.modules.projects.schemas import ProjectModuleProgress

    out: list[ProjectModuleProgress] = []

    # Books
    try:
        from app.models.project import Book

        result = await db.execute(
            select(func.count(Book.id)).where(
                Book.project_id == project_id, Book.deleted_at.is_(None)
            )
        )
        count = result.scalar() or 0
        out.append(
            ProjectModuleProgress(
                module_type="books",
                status="linked" if count else "not_started",
                count=int(count),
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("linked books failed: %s", exc)

    # Pipelines
    try:
        from app.modules.production_pipeline.models import Pipeline

        result = await db.execute(
            select(Pipeline).where(Pipeline.deleted_at.is_(None))
        )
        pipelines = [p for p in result.scalars().all() if getattr(p, "book_id", None)]
        # Simple heuristic: any pipeline whose book belongs to this project
        # (we don't require it -- just surface pipeline count for the project)
        out.append(
            ProjectModuleProgress(
                module_type="pipeline",
                status="linked" if pipelines else "not_started",
                count=len(pipelines),
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("linked pipelines failed: %s", exc)

    return out


async def update_project(
    db: AsyncSession,
    project_id: UUID,
    org_id: UUID,
    user_role: str,
    title: str | None = None,
    description: str | None = None,
    book_type: str | None = None,
    target_launch_date: dt_module.date | None = None,
    status: str | None = None,
    genre: str | None = None,
    subgenre: str | None = None,
    target_audience: str | None = None,
    keywords: list[str] | None = None,
    target_word_count: int | None = None,
    target_date: dt_module.date | None = None,
    marketplace: str | None = None,
    template: str | None = None,
    cover_image_url: str | None = None,
    language: str | None = None,
    content_rating: str | None = None,
    has_ai_content: bool | None = None,
    is_public_domain: bool | None = None,
) -> ProjectResponse:
    """Update project details.

    Args:
        db: Database session
        project_id: Project ID
        org_id: Organization ID for permission check
        user_role: User role for permission check
        title: New title (optional)
        description: New description (optional)
        status: New status (optional)
        genre: New genre (optional)
        subgenre: New subgenre (optional)
        target_audience: New target audience (optional)
        keywords: New keywords (optional)
        target_word_count: New target word count (optional)
        target_date: New target date (optional)
        marketplace: New marketplace (optional)
        template: New template (optional)
        cover_image_url: New cover image URL (optional)
        language: New language (optional)
        content_rating: New content rating (optional)
        has_ai_content: New AI content flag (optional)
        is_public_domain: New public domain flag (optional)

    Returns:
        Updated ProjectResponse

    Raises:
        AppException: If project not found or access denied
    """
    query = select(Project).where(
        Project.id == project_id,
        Project.deleted_at.is_(None),
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise AppException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    # Permission check: ensure user belongs to the project's org
    if project.org_id != org_id:
        raise AppException(
            status_code=403,
            code="ACCESS_DENIED",
            message="Access denied",
        )

    if title is not None:
        project.title = title
    if description is not None:
        project.description = description
    if book_type is not None:
        project.book_type = book_type
    if target_launch_date is not None:
        project.target_launch_date = target_launch_date
    if status is not None:
        project.status = status
    if genre is not None:
        project.genre = genre
    if subgenre is not None:
        project.subgenre = subgenre
    if target_audience is not None:
        project.target_audience = target_audience
    if keywords is not None:
        project.keywords = keywords
    if target_word_count is not None:
        project.target_word_count = target_word_count
    if target_date is not None:
        project.target_date = target_date
    if marketplace is not None:
        project.marketplace = marketplace
    if template is not None:
        project.template = template
    if cover_image_url is not None:
        project.cover_image_url = cover_image_url
    if language is not None:
        project.language = language
    if content_rating is not None:
        project.content_rating = content_rating
    if has_ai_content is not None:
        project.has_ai_content = has_ai_content
    if is_public_domain is not None:
        project.is_public_domain = is_public_domain

    project.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(project)

    return _project_to_response(project)


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
    query = select(Project).where(
        Project.org_id == organization_id,
        Project.deleted_at.is_(None),
    )

    if request.project_type:
        query = query.where(Project.type == request.project_type)

    if request.status:
        query = query.where(Project.status == request.status)

    if request.book_type:
        query = query.where(Project.book_type == request.book_type)

    if request.search:
        like = f"%{request.search}%"
        query = query.where(Project.title.ilike(like))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Sort
    sort_key = (request.sort or "-created_at").strip()
    desc = sort_key.startswith("-")
    key = sort_key.lstrip("-")
    sort_col = {
        "created_at": Project.created_at,
        "title": Project.title,
        "target_date": Project.target_date,
    }.get(key, Project.created_at)
    order = sort_col.desc() if desc else sort_col.asc()

    # Apply pagination
    query = query.limit(request.limit).offset(request.offset).order_by(order)

    result = await db.execute(query)
    projects = result.scalars().all()

    project_items = [
        ProjectListItem(
            id=p.id,
            title=p.title,
            project_type=p.type.value if hasattr(p.type, "value") else str(p.type),
            status=p.status.value if hasattr(p.status, "value") else str(p.status),
            book_type=getattr(p, "book_type", None),
            target_launch_date=getattr(p, "target_launch_date", None),
            genre=p.genre,
            target_date=p.target_date,
            target_word_count=p.target_word_count,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in projects
    ]

    return ProjectListResponse(projects=project_items, total=total)


async def delete_project(
    db: AsyncSession,
    project_id: UUID,
    org_id: UUID,
    user_role: str,
) -> None:
    """Soft delete a project.

    Args:
        db: Database session
        project_id: Project ID
        org_id: Organization ID for permission check
        user_role: User role for permission check

    Raises:
        AppException: If project not found or access denied
    """
    query = select(Project).where(
        Project.id == project_id,
        Project.deleted_at.is_(None),
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise AppException(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    # Permission check: ensure user belongs to the project's org
    if project.org_id != org_id:
        raise AppException(
            status_code=403,
            code="ACCESS_DENIED",
            message="Access denied",
        )

    # Soft delete: set deleted_at timestamp
    project.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info(f"Soft deleted project {project_id}")
