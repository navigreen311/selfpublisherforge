# FIX28: Unit Tests for Audiobook CRUD Service

## Task
Create unit tests for the audiobook project CRUD service functions.

## File to Create: `backend/tests/voiceforge/test_audiobook_crud.py`

### Tests for service_crud.py
These test the service functions created by FIX02. If the service file doesn't exist yet, create tests that will work once it does.

1. `test_create_project` — Creates a project linked to a book
2. `test_create_project_invalid_book` — Fails for non-existent book
3. `test_list_projects` — Returns paginated list for org
4. `test_list_projects_filter_status` — Filters by status
5. `test_list_projects_tenant_isolation` — Org A can't see Org B's projects
6. `test_get_project` — Returns project with chapters
7. `test_get_project_not_found` — Returns None for missing project
8. `test_update_project` — Updates specified fields only
9. `test_update_project_partial` — Leaves unspecified fields unchanged
10. `test_delete_project` — Soft deletes (sets deleted_at)
11. `test_delete_project_not_found` — Returns False for missing project
12. `test_deleted_project_not_in_list` — Soft-deleted projects don't appear in list

### Mock Setup
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db

@pytest.fixture
def org_id():
    return uuid4()

@pytest.fixture
def sample_project(org_id):
    return MagicMock(
        id=uuid4(),
        org_id=org_id,
        book_id=uuid4(),
        title="Test Audiobook",
        status="draft",
        total_chapters=10,
        completed_chapters=0,
    )
```

## Conventions
- Use pytest, pytest-asyncio
- Mock AsyncSession
- Test both happy path and error cases
