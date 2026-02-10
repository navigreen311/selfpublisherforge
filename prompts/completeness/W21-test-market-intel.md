# W21: Tests for Market Intelligence DB Service

## Files to create/modify
- `backend/tests/unit/test_market_intelligence_service.py` — NEW or update

## Context
Market intelligence competitor tracking and snapshots are being migrated to DB (by W03). Write tests using mocked AsyncSession and mocked Amazon client.

## Task

### 1. Find existing tests

Check `backend/tests/` for any market intelligence tests. Read current test patterns.

### 2. Write unit tests

Test the service methods that are being changed to use DB:

```python
"""Unit tests for Market Intelligence service."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.modules.market_intelligence.service import MarketIntelligenceService
from app.modules.market_intelligence.schemas import CompetitorTrackRequest

class TestListCompetitors:
    @pytest.mark.asyncio
    async def test_queries_db_by_org(self):
        """list_competitors should query CompetitorBook by marketplace."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        svc = MarketIntelligenceService()
        result = await svc.list_competitors(db=db, marketplace="US")
        assert result == []
        db.execute.assert_called_once()

class TestTrackCompetitor:
    @pytest.mark.asyncio
    async def test_creates_competitor_in_db(self):
        """track_competitor should create a CompetitorBook record."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        # Mock that no existing competitor found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        svc = MarketIntelligenceService()
        # Mock the amazon client
        with patch.object(svc, '_client') as mock_client:
            mock_client.get_product_detail = AsyncMock(return_value=MagicMock(
                asin="B001", title="Test Book", author="Author",
                bsr=1000, price=9.99, reviews_count=100, rating=4.5,
                image_url=None
            ))
            mock_client.get_bsr_history = AsyncMock(return_value=[])

            request = CompetitorTrackRequest(asin="B001", marketplace="US")
            result = await svc.track_competitor(db=db, org_id=uuid.uuid4(), request=request)

            db.add.assert_called_once()

class TestGetSnapshots:
    @pytest.mark.asyncio
    async def test_returns_db_snapshots(self):
        """get_snapshots should query MarketSnapshot table, not generate synthetic data."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        svc = MarketIntelligenceService()
        result = await svc.get_snapshots(db=db, limit=10)
        assert result == []
        # Should NOT contain random/synthetic data
```

Write at least 8 tests covering DB-based competitor and snapshot operations.
