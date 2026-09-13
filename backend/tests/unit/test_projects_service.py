"""Unit tests for the projects service layer.

Tests project CRUD operations including create, read, update, delete,
and listing with filters using mocked database calls.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AppException
from app.modules.projects import service
from app.modules.projects.schemas import ProjectListRequest
from tests.conftest import populate_server_defaults

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project_row(
    project_id: uuid.UUID | None = None,
    title: str = "Test Project",
    description: str | None = None,
    project_type: str = "book",
    status: str = "draft",
    org_id: uuid.UUID | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> dict:
    """Build a dict that mimics a row from the projects table."""
    now = datetime.now(UTC)
    return {
        "id": project_id or uuid.uuid4(),
        "title": title,
        "description": description,
        "type": project_type,
        "status": status,
        "org_id": org_id or uuid.uuid4(),
        "created_at": created_at or now,
        "updated_at": updated_at or now,
        "deleted_at": deleted_at,
    }


def _mock_project_orm(row: dict) -> SimpleNamespace:
    """Create a stand-in Project ORM object from a row dict."""
    defaults = {
        "book_type": None,
        "target_launch_date": None,
        "genre": None,
        "subgenre": None,
        "target_audience": None,
        "keywords": None,
        "target_word_count": None,
        "target_date": None,
        "marketplace": None,
        "template": None,
        "cover_image_url": None,
        "language": None,
        "content_rating": None,
        "has_ai_content": False,
        "is_public_domain": False,
    }
    defaults.update(row)
    return SimpleNamespace(**defaults)


def _mock_db_for_create() -> AsyncMock:
    """Return a mock db session for project creation."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock(side_effect=populate_server_defaults)
    return mock_db


def _mock_db_with_project(project_row: dict | None) -> AsyncMock:
    """Return a mock db session that returns the given project."""
    mock_db = AsyncMock()

    if project_row:
        project_mock = _mock_project_orm(project_row)
        result = MagicMock()
        result.scalar_one_or_none.return_value = project_mock
    else:
        result = MagicMock()
        result.scalar_one_or_none.return_value = None

    mock_db.execute = AsyncMock(return_value=result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock(side_effect=populate_server_defaults)

    return mock_db


def _mock_db_with_projects(project_rows: list[dict]) -> AsyncMock:
    """Return a mock db session that returns given projects."""
    mock_db = AsyncMock()

    # For projects query
    project_scalars = MagicMock()
    project_scalars.all.return_value = [_mock_project_orm(row) for row in project_rows]
    project_result = MagicMock()
    project_result.scalars.return_value = project_scalars

    # list_projects takes its total from db.scalar(count_query) and only ever
    # calls execute() for the rows, so execute must not hand back the count.
    mock_db.execute = AsyncMock(return_value=project_result)
    mock_db.scalar = AsyncMock(return_value=len(project_rows))

    return mock_db


# ===========================================================================
# Project Creation Tests
# ===========================================================================


class TestCreateProject:
    """Tests for create_project service function."""

    @pytest.mark.asyncio
    async def test_creates_project_with_all_fields(self):
        """Should create a project with all provided fields."""
        mock_db = _mock_db_for_create()
        org_id = uuid.uuid4()

        result = await service.create_project(
            mock_db, organization_id=org_id, title="My Book Project", description="A great book", project_type="book"
        )

        assert result.title == "My Book Project"
        assert result.description == "A great book"
        assert result.project_type == "book"
        assert result.status == "draft"
        assert result.organization_id == org_id
        assert result.id is not None

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_project_without_description(self):
        """Should create a project without description."""
        mock_db = _mock_db_for_create()
        org_id = uuid.uuid4()

        result = await service.create_project(mock_db, organization_id=org_id, title="Simple Project")

        assert result.title == "Simple Project"
        assert result.description is None
        assert result.project_type == "book"  # default

    @pytest.mark.asyncio
    async def test_creates_series_project(self):
        """Should create a series project."""
        mock_db = _mock_db_for_create()
        org_id = uuid.uuid4()

        result = await service.create_project(
            mock_db, organization_id=org_id, title="Book Series", project_type="series"
        )

        assert result.project_type == "series"

    @pytest.mark.asyncio
    async def test_creates_course_project(self):
        """Should create a course project."""
        mock_db = _mock_db_for_create()
        org_id = uuid.uuid4()

        result = await service.create_project(
            mock_db, organization_id=org_id, title="Online Course", project_type="course"
        )

        assert result.project_type == "course"


# ===========================================================================
# Project Retrieval Tests
# ===========================================================================


class TestGetProject:
    """Tests for get_project service function."""

    @pytest.mark.asyncio
    async def test_returns_project(self):
        """Should return project details when found."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        project_row = _make_project_row(project_id=project_id, title="Found Project", org_id=org_id)
        mock_db = _mock_db_with_project(project_row)

        result = await service.get_project(mock_db, project_id, org_id)

        assert result.id == project_id
        assert result.title == "Found Project"
        assert result.organization_id == org_id

    @pytest.mark.asyncio
    async def test_project_not_found_raises_404(self):
        """Should raise PROJECT_NOT_FOUND when project doesn't exist."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        mock_db = _mock_db_with_project(None)

        with pytest.raises(AppException) as exc_info:
            await service.get_project(mock_db, project_id, org_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_deleted_project_not_found(self):
        """Should not return soft-deleted projects."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        # Project exists but is soft-deleted (deleted_at is set)
        # The query filters for deleted_at.is_(None), so it won't be returned
        mock_db = _mock_db_with_project(None)

        with pytest.raises(AppException) as exc_info:
            await service.get_project(mock_db, project_id, org_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_access_denied_for_different_org(self):
        """Should raise ACCESS_DENIED when user's org doesn't match project's org."""
        project_id = uuid.uuid4()
        project_org_id = uuid.uuid4()
        user_org_id = uuid.uuid4()

        project_row = _make_project_row(project_id=project_id, org_id=project_org_id)
        mock_db = _mock_db_with_project(project_row)

        with pytest.raises(AppException) as exc_info:
            await service.get_project(mock_db, project_id, user_org_id)

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "ACCESS_DENIED"


# ===========================================================================
# Project Update Tests
# ===========================================================================


class TestUpdateProject:
    """Tests for update_project service function."""

    @pytest.mark.asyncio
    async def test_updates_all_fields(self):
        """Should update title, description, and status."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        project_row = _make_project_row(
            project_id=project_id, title="Old Title", description="Old Desc", status="draft", org_id=org_id
        )
        mock_db = _mock_db_with_project(project_row)

        result = await service.update_project(
            mock_db,
            project_id,
            org_id,
            user_role="admin",
            title="New Title",
            description="New Description",
            status="active",
        )

        assert result.title == "New Title"
        assert result.description == "New Description"
        assert result.status == "active"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_only_title(self):
        """Should update only title when other fields are None."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        project_row = _make_project_row(project_id=project_id, org_id=org_id)
        mock_db = _mock_db_with_project(project_row)

        result = await service.update_project(mock_db, project_id, org_id, user_role="editor", title="Updated Title")

        assert result.title == "Updated Title"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_status_only(self):
        """Should update only status."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        project_row = _make_project_row(project_id=project_id, org_id=org_id, status="draft")
        mock_db = _mock_db_with_project(project_row)

        result = await service.update_project(mock_db, project_id, org_id, user_role="owner", status="active")

        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_project_not_found_raises_404(self):
        """Should raise PROJECT_NOT_FOUND when project doesn't exist."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        mock_db = _mock_db_with_project(None)

        with pytest.raises(AppException) as exc_info:
            await service.update_project(mock_db, project_id, org_id, user_role="admin", title="New Title")

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_access_denied_for_different_org(self):
        """Should raise ACCESS_DENIED when user's org doesn't match."""
        project_id = uuid.uuid4()
        project_org_id = uuid.uuid4()
        user_org_id = uuid.uuid4()

        project_row = _make_project_row(project_id=project_id, org_id=project_org_id)
        mock_db = _mock_db_with_project(project_row)

        with pytest.raises(AppException) as exc_info:
            await service.update_project(mock_db, project_id, user_org_id, user_role="admin", title="New Title")

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "ACCESS_DENIED"


# ===========================================================================
# Project Listing Tests
# ===========================================================================


class TestListProjects:
    """Tests for list_projects service function."""

    @pytest.mark.asyncio
    async def test_returns_all_projects(self):
        """Should return all projects for an organization."""
        org_id = uuid.uuid4()
        project_rows = [
            _make_project_row(title="Project 1", org_id=org_id),
            _make_project_row(title="Project 2", org_id=org_id, project_type="series"),
            _make_project_row(title="Project 3", org_id=org_id, status="active"),
        ]
        mock_db = _mock_db_with_projects(project_rows)

        request = ProjectListRequest(limit=10, offset=0)
        result = await service.list_projects(mock_db, org_id, request)

        assert result.total == 3
        assert len(result.projects) == 3
        assert result.projects[0].title == "Project 1"
        assert result.projects[1].title == "Project 2"
        assert result.projects[2].title == "Project 3"

    @pytest.mark.asyncio
    async def test_filters_by_project_type(self):
        """Should filter projects by type."""
        org_id = uuid.uuid4()
        project_rows = [
            _make_project_row(title="Book Project", org_id=org_id, project_type="book"),
        ]
        mock_db = _mock_db_with_projects(project_rows)

        request = ProjectListRequest(project_type="book", limit=10, offset=0)
        result = await service.list_projects(mock_db, org_id, request)

        assert len(result.projects) == 1
        assert result.projects[0].project_type == "book"

    @pytest.mark.asyncio
    async def test_filters_by_status(self):
        """Should filter projects by status."""
        org_id = uuid.uuid4()
        project_rows = [
            _make_project_row(title="Draft Project", org_id=org_id, status="draft"),
        ]
        mock_db = _mock_db_with_projects(project_rows)

        request = ProjectListRequest(status="draft", limit=10, offset=0)
        result = await service.list_projects(mock_db, org_id, request)

        assert len(result.projects) == 1
        assert result.projects[0].status == "draft"

    @pytest.mark.asyncio
    async def test_pagination(self):
        """Should apply limit and offset."""
        org_id = uuid.uuid4()
        project_rows = [_make_project_row(title=f"Project {i}", org_id=org_id) for i in range(5)]
        mock_db = _mock_db_with_projects(project_rows)

        request = ProjectListRequest(limit=2, offset=1)
        result = await service.list_projects(mock_db, org_id, request)

        # Total is still 5, but we only get 2 items
        assert result.total == 5

    @pytest.mark.asyncio
    async def test_empty_organization(self):
        """Should return empty list when org has no projects."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_with_projects([])

        request = ProjectListRequest(limit=10, offset=0)
        result = await service.list_projects(mock_db, org_id, request)

        assert result.total == 0
        assert len(result.projects) == 0


# ===========================================================================
# Project Deletion Tests
# ===========================================================================


class TestDeleteProject:
    """Tests for delete_project service function (soft delete)."""

    @pytest.mark.asyncio
    async def test_soft_deletes_project(self):
        """Should set deleted_at timestamp on project."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        project_row = _make_project_row(project_id=project_id, org_id=org_id)
        mock_db = _mock_db_with_project(project_row)

        await service.delete_project(mock_db, project_id, org_id, user_role="owner")

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_project_not_found_raises_404(self):
        """Should raise PROJECT_NOT_FOUND when project doesn't exist."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        mock_db = _mock_db_with_project(None)

        with pytest.raises(AppException) as exc_info:
            await service.delete_project(mock_db, project_id, org_id, user_role="admin")

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_access_denied_for_different_org(self):
        """Should raise ACCESS_DENIED when user's org doesn't match."""
        project_id = uuid.uuid4()
        project_org_id = uuid.uuid4()
        user_org_id = uuid.uuid4()

        project_row = _make_project_row(project_id=project_id, org_id=project_org_id)
        mock_db = _mock_db_with_project(project_row)

        with pytest.raises(AppException) as exc_info:
            await service.delete_project(mock_db, project_id, user_org_id, user_role="admin")

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "ACCESS_DENIED"

    @pytest.mark.asyncio
    async def test_already_deleted_project_not_found(self):
        """Should not find already deleted projects."""
        project_id = uuid.uuid4()
        org_id = uuid.uuid4()
        # Query filters for deleted_at.is_(None), so deleted projects won't be found
        mock_db = _mock_db_with_project(None)

        with pytest.raises(AppException) as exc_info:
            await service.delete_project(mock_db, project_id, org_id, user_role="owner")

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "PROJECT_NOT_FOUND"
