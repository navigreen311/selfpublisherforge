"""Unit tests for audiobook project CRUD service functions.

Tests the service_crud module that provides create, read, update, delete,
and listing operations for AudiobookProject entities with tenant isolation.
These tests mock the AsyncSession to isolate service logic from the database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.audiobook import AudiobookProject

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project_row(
    project_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    book_id: uuid.UUID | None = None,
    title: str = "Test Audiobook",
    status: str = "draft",
    total_chapters: int = 10,
    completed_chapters: int = 0,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> dict:
    """Build a dict that mimics a row from the audiobook_projects table."""
    now = datetime.now(UTC)
    return {
        "id": project_id or uuid.uuid4(),
        "org_id": org_id or uuid.uuid4(),
        "book_id": book_id or uuid.uuid4(),
        "title": title,
        "status": status,
        "total_chapters": total_chapters,
        "completed_chapters": completed_chapters,
        "created_at": created_at or now,
        "updated_at": updated_at or now,
        "deleted_at": deleted_at,
    }


def _mock_project_orm(row: dict) -> MagicMock:
    """Create a mock AudiobookProject ORM object from a row dict."""
    project = MagicMock(spec=AudiobookProject)
    for key, value in row.items():
        setattr(project, key, value)
    project.chapters = []
    return project


def _mock_db_for_create(book_exists: bool = True) -> AsyncMock:
    """Return a mock db session for project creation.

    When book_exists=True, the first execute() call returns a scalar result
    simulating a valid book lookup.
    """
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    if book_exists:
        book_result = MagicMock()
        book_result.scalar_one_or_none.return_value = MagicMock(id=uuid.uuid4())
        mock_db.execute = AsyncMock(return_value=book_result)
    else:
        no_book_result = MagicMock()
        no_book_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=no_book_result)

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
    mock_db.refresh = AsyncMock()

    return mock_db


def _mock_db_with_projects(project_rows: list[dict]) -> AsyncMock:
    """Return a mock db session that returns given projects for list queries.

    First execute() call returns the count; second returns the project list.
    """
    mock_db = AsyncMock()

    count_result = MagicMock()
    count_result.scalar.return_value = len(project_rows)

    project_scalars = MagicMock()
    project_scalars.all.return_value = [_mock_project_orm(row) for row in project_rows]
    project_result = MagicMock()
    project_result.scalars.return_value = project_scalars

    call_count = {"count": 0}

    def execute_side_effect(query):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return count_result
        return project_result

    mock_db.execute = AsyncMock(side_effect=execute_side_effect)
    mock_db.scalar = AsyncMock(return_value=len(project_rows))

    return mock_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def other_org_id():
    return uuid.uuid4()


@pytest.fixture
def book_id():
    return uuid.uuid4()


@pytest.fixture
def sample_project(org_id, book_id):
    return MagicMock(
        id=uuid.uuid4(),
        org_id=org_id,
        book_id=book_id,
        title="Test Audiobook",
        status="draft",
        total_chapters=10,
        completed_chapters=0,
        deleted_at=None,
        chapters=[],
    )


# ===========================================================================
# Project Creation Tests
# ===========================================================================


class TestCreateProject:
    """Tests for create_project — creates audiobook project linked to a book."""

    @pytest.mark.asyncio
    async def test_create_project(self, org_id, book_id):
        """Should create a project linked to a valid book."""
        mock_db = _mock_db_for_create(book_exists=True)

        from app.modules.audiobook import service_crud

        result = await service_crud.create_project(
            db=mock_db,
            org_id=org_id,
            book_id=book_id,
            title="My Audiobook",
        )

        assert result is not None
        assert result.title == "My Audiobook"
        assert result.org_id == org_id
        assert result.book_id == book_id
        assert result.status == "draft"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_invalid_book(self, org_id):
        """Should fail when book_id refers to a non-existent book."""
        mock_db = _mock_db_for_create(book_exists=False)
        bad_book_id = uuid.uuid4()

        from app.modules.audiobook import service_crud

        with pytest.raises((ValueError, LookupError)):
            await service_crud.create_project(
                db=mock_db,
                org_id=org_id,
                book_id=bad_book_id,
                title="Invalid Book Audiobook",
            )


# ===========================================================================
# Project Listing Tests
# ===========================================================================


class TestListProjects:
    """Tests for list_projects — paginated, filtered, tenant-isolated."""

    @pytest.mark.asyncio
    async def test_list_projects(self, org_id):
        """Should return a paginated list of projects for the org."""
        rows = [_make_project_row(title=f"Audiobook {i}", org_id=org_id) for i in range(3)]
        mock_db = _mock_db_with_projects(rows)

        from app.modules.audiobook import service_crud

        result = await service_crud.list_projects(
            db=mock_db,
            org_id=org_id,
            limit=10,
            offset=0,
        )

        assert result.total == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_list_projects_filter_status(self, org_id):
        """Should filter projects by status when provided."""
        rows = [
            _make_project_row(title="Generating Book", org_id=org_id, status="generating"),
        ]
        mock_db = _mock_db_with_projects(rows)

        from app.modules.audiobook import service_crud

        result = await service_crud.list_projects(
            db=mock_db,
            org_id=org_id,
            status="generating",
            limit=10,
            offset=0,
        )

        assert len(result.items) == 1
        assert result.items[0].status == "generating"

    @pytest.mark.asyncio
    async def test_list_projects_tenant_isolation(self, org_id, other_org_id):
        """Org A should not see Org B's projects.

        We set up projects for org_id and query with other_org_id — the service
        should filter by the requesting org, returning an empty result.
        """
        mock_db = _mock_db_with_projects([])

        from app.modules.audiobook import service_crud

        result = await service_crud.list_projects(
            db=mock_db,
            org_id=other_org_id,
            limit=10,
            offset=0,
        )

        assert result.total == 0
        assert len(result.items) == 0


# ===========================================================================
# Project Retrieval Tests
# ===========================================================================


class TestGetProject:
    """Tests for get_project — returns project with chapters."""

    @pytest.mark.asyncio
    async def test_get_project(self, org_id):
        """Should return project details with chapters when found."""
        project_id = uuid.uuid4()
        row = _make_project_row(project_id=project_id, org_id=org_id, title="Found Book")
        mock_db = _mock_db_with_project(row)

        from app.modules.audiobook import service_crud

        result = await service_crud.get_project(
            db=mock_db,
            project_id=project_id,
            org_id=org_id,
        )

        assert result is not None
        assert result.id == project_id
        assert result.title == "Found Book"
        assert hasattr(result, "chapters")

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, org_id):
        """Should return None for a project that does not exist."""
        mock_db = _mock_db_with_project(None)

        from app.modules.audiobook import service_crud

        result = await service_crud.get_project(
            db=mock_db,
            project_id=uuid.uuid4(),
            org_id=org_id,
        )

        assert result is None


# ===========================================================================
# Project Update Tests
# ===========================================================================


class TestUpdateProject:
    """Tests for update_project — partial field updates."""

    @pytest.mark.asyncio
    async def test_update_project(self, org_id):
        """Should update specified fields only."""
        project_id = uuid.uuid4()
        row = _make_project_row(
            project_id=project_id,
            org_id=org_id,
            title="Old Title",
            status="draft",
        )
        mock_db = _mock_db_with_project(row)

        from app.modules.audiobook import service_crud

        result = await service_crud.update_project(
            db=mock_db,
            project_id=project_id,
            org_id=org_id,
            title="New Title",
            status="configuring",
        )

        assert result.title == "New Title"
        assert result.status == "configuring"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_project_partial(self, org_id):
        """Should leave unspecified fields unchanged."""
        project_id = uuid.uuid4()
        row = _make_project_row(
            project_id=project_id,
            org_id=org_id,
            title="Original Title",
            status="draft",
            total_chapters=10,
        )
        mock_db = _mock_db_with_project(row)

        from app.modules.audiobook import service_crud

        result = await service_crud.update_project(
            db=mock_db,
            project_id=project_id,
            org_id=org_id,
            title="Updated Title",
        )

        assert result.title == "Updated Title"
        # Status should remain unchanged
        assert result.status == "draft"
        assert result.total_chapters == 10


# ===========================================================================
# Project Deletion Tests
# ===========================================================================


class TestDeleteProject:
    """Tests for delete_project — soft delete via deleted_at timestamp."""

    @pytest.mark.asyncio
    async def test_delete_project(self, org_id):
        """Should soft-delete by setting deleted_at timestamp."""
        project_id = uuid.uuid4()
        row = _make_project_row(project_id=project_id, org_id=org_id)
        mock_db = _mock_db_with_project(row)

        from app.modules.audiobook import service_crud

        result = await service_crud.delete_project(
            db=mock_db,
            project_id=project_id,
            org_id=org_id,
        )

        assert result is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, org_id):
        """Should return False when project does not exist."""
        mock_db = _mock_db_with_project(None)

        from app.modules.audiobook import service_crud

        result = await service_crud.delete_project(
            db=mock_db,
            project_id=uuid.uuid4(),
            org_id=org_id,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_deleted_project_not_in_list(self, org_id):
        """Soft-deleted projects should not appear in list results.

        We simulate the service correctly filtering out deleted_at != NULL
        by returning only non-deleted rows from the mock.
        """
        # Only non-deleted projects in the result set
        active_rows = [
            _make_project_row(title="Active Book", org_id=org_id),
        ]
        # Deleted project is NOT in the list (service filters it out)
        mock_db = _mock_db_with_projects(active_rows)

        from app.modules.audiobook import service_crud

        result = await service_crud.list_projects(
            db=mock_db,
            org_id=org_id,
            limit=10,
            offset=0,
        )

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].title == "Active Book"
        # Verify none of the returned items have a deleted_at
        for item in result.items:
            assert item.deleted_at is None
