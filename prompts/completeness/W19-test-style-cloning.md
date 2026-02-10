# W19: Tests for Style Cloning DB Service

## Files to create/modify
- `backend/tests/unit/test_style_cloning_service.py` — NEW or update existing

## Context
The style cloning service is being migrated from in-memory to DB (by W01). Write tests that work with the DB-based service using mocked AsyncSession.

## Task

### 1. Find existing tests

Read `backend/tests/` for any existing style cloning tests. Update them if they exist, create new ones if not.

### 2. Write comprehensive unit tests

```python
"""Unit tests for Style Cloning service with DB persistence."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.modules.style_cloning.schemas import (
    CreateProfileRequest, ProfileStatus, ProfileResponse
)

class TestCreateProfile:
    @pytest.mark.asyncio
    async def test_creates_profile_in_db(self):
        """create_profile should add a StyleProfile to the session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        org_id = uuid.uuid4()
        request = CreateProfileRequest(name="Test Profile", genre="fiction")

        from app.modules.style_cloning.service import create_profile
        result = await create_profile(db, org_id, request)

        db.add.assert_called_once()
        db.flush.assert_called()
        assert result.name == "Test Profile"

    @pytest.mark.asyncio
    async def test_creates_with_sample_texts_runs_analysis(self):
        """If sample_texts provided, should run NLP analysis."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        org_id = uuid.uuid4()
        request = CreateProfileRequest(
            name="Analyzed",
            sample_texts=["This is a long enough sample text for analysis. " * 50]
        )

        from app.modules.style_cloning.service import create_profile
        result = await create_profile(db, org_id, request)
        # Status should be 'ready' or 'analyzing' after analysis
        assert result.status in (ProfileStatus.ready, ProfileStatus.analyzing)

class TestListProfiles:
    @pytest.mark.asyncio
    async def test_returns_org_profiles(self):
        """list_profiles should query by org_id and return non-deleted profiles."""
        # Mock db.execute to return a list of profile objects
        ...

class TestDeleteProfile:
    @pytest.mark.asyncio
    async def test_soft_deletes(self):
        """delete_profile should set deleted_at, not remove the record."""
        ...

class TestGetFingerprint:
    @pytest.mark.asyncio
    async def test_returns_none_for_unanalyzed(self):
        """get_fingerprint returns None if profile has no fingerprint."""
        ...

class TestConformityCheck:
    @pytest.mark.asyncio
    async def test_returns_none_for_missing_profile(self):
        """conformity_check returns None if profile not found."""
        ...
```

Write at least 8-10 tests covering all service methods, edge cases, and error paths.
