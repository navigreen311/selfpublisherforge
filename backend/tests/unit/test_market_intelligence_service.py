"""Unit tests for the Market Intelligence service (DB-backed operations).

Tests cover the database-backed methods of MarketIntelligenceService:
  - list_competitors: querying CompetitorBook rows by org/marketplace
  - track_competitor: creating a new CompetitorBook from Amazon client data
  - get_competitor: fetching a single competitor by ID
  - get_snapshots: querying MarketSnapshot rows, with and without category filter
  - Edge cases: duplicate tracking, missing products, empty results

All tests use mocked AsyncSession and mocked Amazon client -- no real DB or API.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AppException
from app.modules.market_intelligence.schemas import (
    CompetitorDetail,
    CompetitorListItem,
    CompetitorTrackRequest,
    MarketSnapshot,
)
from app.modules.market_intelligence.service import MarketIntelligenceService

# ---------------------------------------------------------------------------
# Helpers / Factories
# ---------------------------------------------------------------------------


def _make_competitor_book(**overrides) -> MagicMock:
    """Create a MagicMock resembling a CompetitorBook ORM row."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid.uuid4(),
        "org_id": uuid.uuid4(),
        "asin": "B000000001",
        "title": "Test Book",
        "author": "Author Smith",
        "bsr_current": 5000,
        "bsr_history": [
            {"date": "2025-01-01T00:00:00+00:00", "bsr": 5200, "price": 9.99},
            {"date": "2025-01-15T00:00:00+00:00", "bsr": 4800, "price": 9.99},
        ],
        "price": 9.99,
        "reviews_count": 150,
        "rating": 4.3,
        "category": "Self-Help",
        "category_ids": None,
        "cover_url": "https://example.com/cover.jpg",
        "metadata_json": {"marketplace": "US"},
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    defaults.update(overrides)

    book = MagicMock()
    for k, v in defaults.items():
        setattr(book, k, v)
    return book


def _make_snapshot(**overrides) -> MagicMock:
    """Create a MagicMock resembling a MarketSnapshot ORM row."""
    now = datetime.now(UTC)
    cat_mock = MagicMock()
    cat_mock.amazon_node_id = "154606011"
    cat_mock.name = "Self-Help"

    defaults = {
        "id": uuid.uuid4(),
        "category_id": uuid.uuid4(),
        "snapshot_date": date(2025, 3, 15),
        "top_100_asins": ["B000000001", "B000000002"],
        "metrics": {
            "avg_bsr": 12500.0,
            "avg_price": 11.99,
            "book_count": 200,
            "avg_reviews": 85.0,
            "competition_score": 62.5,
        },
        "category": cat_mock,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    defaults.update(overrides)

    snap = MagicMock()
    for k, v in defaults.items():
        setattr(snap, k, v)
    return snap


def _make_category(**overrides) -> MagicMock:
    """Create a MagicMock resembling a MarketCategory ORM row."""
    defaults = {
        "id": uuid.uuid4(),
        "amazon_node_id": "154606011",
        "name": "Self-Help",
        "deleted_at": None,
    }
    defaults.update(overrides)

    cat = MagicMock()
    for k, v in defaults.items():
        setattr(cat, k, v)
    return cat


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Return an AsyncMock simulating an AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_client():
    """Return an AsyncMock simulating an AmazonClientBase."""
    client = AsyncMock()
    client.get_product_detail = AsyncMock()
    client.get_bsr_history = AsyncMock(return_value=[])
    client.search_products = AsyncMock(return_value=[])
    client.get_keyword_data = AsyncMock(return_value=[])
    client.get_category_tree = AsyncMock(return_value=[])
    return client


@pytest.fixture
def service(mock_client):
    """Return a MarketIntelligenceService wired to the mock client."""
    return MarketIntelligenceService(client=mock_client)


@pytest.fixture
def org_id():
    return uuid.uuid4()


# ===========================================================================
# Tests: list_competitors
# ===========================================================================


class TestListCompetitors:
    """Tests for MarketIntelligenceService.list_competitors."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_competitors(self, service, mock_db):
        """list_competitors should return [] when the DB has no matching rows."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.list_competitors(db=mock_db, marketplace="US")

        assert result == []
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_mapped_competitor_list_items(self, service, mock_db, org_id):
        """list_competitors should map DB rows to CompetitorListItem schemas."""
        book1 = _make_competitor_book(asin="B000000001", title="Book One", org_id=org_id)
        book2 = _make_competitor_book(asin="B000000002", title="Book Two", org_id=org_id)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [book1, book2]
        mock_db.execute.return_value = mock_result

        result = await service.list_competitors(db=mock_db, org_id=org_id, marketplace="US")

        assert len(result) == 2
        assert isinstance(result[0], CompetitorListItem)
        assert result[0].asin == "B000000001"
        assert result[0].title == "Book One"
        assert result[1].asin == "B000000002"

    @pytest.mark.asyncio
    async def test_queries_db_with_org_id_filter(self, service, mock_db, org_id):
        """list_competitors should apply org_id filter when provided."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await service.list_competitors(db=mock_db, org_id=org_id, marketplace="US")

        # Verify execute was called (query is built with org_id filter)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_marketplace_from_metadata_json(self, service, mock_db):
        """list_competitors should extract marketplace from metadata_json."""
        book = _make_competitor_book(metadata_json={"marketplace": "UK"})
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [book]
        mock_db.execute.return_value = mock_result

        result = await service.list_competitors(db=mock_db, marketplace="US")

        assert len(result) == 1
        # The mapper reads marketplace from metadata_json, so it should be "UK"
        assert result[0].marketplace == "UK"


# ===========================================================================
# Tests: track_competitor
# ===========================================================================


class TestTrackCompetitor:
    """Tests for MarketIntelligenceService.track_competitor."""

    @pytest.mark.asyncio
    async def test_creates_competitor_in_db(self, service, mock_db, mock_client, org_id):
        """track_competitor should create a CompetitorBook record in the DB."""
        # No existing competitor
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Mock Amazon product detail response
        mock_client.get_product_detail.return_value = MagicMock(
            asin="B001234567",
            title="New Book",
            author="Jane Author",
            bsr=3000,
            price=12.99,
            reviews_count=200,
            rating=4.5,
            image_url="https://example.com/cover.jpg",
        )
        mock_client.get_bsr_history.return_value = []

        # After db.refresh, simulate the ORM populating fields
        def _refresh_side_effect(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)
            obj.deleted_at = None
            obj.metadata_json = {"marketplace": "US"}
            obj.bsr_history = []

        mock_db.refresh = AsyncMock(side_effect=_refresh_side_effect)

        request = CompetitorTrackRequest(asin="B001234567", marketplace="US")
        result = await service.track_competitor(db=mock_db, request=request, org_id=org_id)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()
        assert isinstance(result, CompetitorDetail)
        mock_client.get_product_detail.assert_awaited_once_with("B001234567", marketplace="US")

    @pytest.mark.asyncio
    async def test_returns_existing_competitor_without_duplicate(self, service, mock_db, mock_client, org_id):
        """track_competitor should return the existing record if ASIN is already tracked."""
        existing_book = _make_competitor_book(asin="B001234567", org_id=org_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_book
        mock_db.execute.return_value = mock_result

        request = CompetitorTrackRequest(asin="B001234567", marketplace="US")
        result = await service.track_competitor(db=mock_db, request=request, org_id=org_id)

        # Should NOT call add or the Amazon client
        mock_db.add.assert_not_called()
        mock_client.get_product_detail.assert_not_awaited()
        assert isinstance(result, CompetitorDetail)
        assert result.asin == "B001234567"

    @pytest.mark.asyncio
    async def test_raises_value_error_when_product_not_found(self, service, mock_db, mock_client, org_id):
        """track_competitor should raise AppException when Amazon returns no product."""
        # No existing competitor
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Amazon client returns None (product not found)
        mock_client.get_product_detail.return_value = None

        request = CompetitorTrackRequest(asin="B999999999", marketplace="US")
        with pytest.raises(AppException) as exc_info:
            await service.track_competitor(db=mock_db, request=request, org_id=org_id)
        assert exc_info.value.status_code == 404
        assert "B999999999" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_stores_bsr_history_as_json(self, service, mock_db, mock_client, org_id):
        """track_competitor should serialize BSR history points into JSONB format."""
        # No existing competitor
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mock_client.get_product_detail.return_value = MagicMock(
            asin="B001234567",
            title="BSR History Book",
            author="Author",
            bsr=2000,
            price=14.99,
            reviews_count=50,
            rating=4.0,
            image_url=None,
        )

        # Return BSR history data points
        bsr_point1 = MagicMock()
        bsr_point1.date.isoformat.return_value = "2025-01-01T00:00:00+00:00"
        bsr_point1.bsr = 2100
        bsr_point1.price = 14.99
        bsr_point2 = MagicMock()
        bsr_point2.date.isoformat.return_value = "2025-01-15T00:00:00+00:00"
        bsr_point2.bsr = 1900
        bsr_point2.price = 14.99
        mock_client.get_bsr_history.return_value = [bsr_point1, bsr_point2]

        # Capture the object passed to db.add
        added_objects = []
        mock_db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        def _refresh_side_effect(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)
            obj.deleted_at = None
            obj.metadata_json = {"marketplace": "US"}

        mock_db.refresh = AsyncMock(side_effect=_refresh_side_effect)

        request = CompetitorTrackRequest(asin="B001234567", marketplace="US")
        await service.track_competitor(db=mock_db, request=request, org_id=org_id)

        # Verify the object added to DB has serialized BSR history
        assert len(added_objects) == 1
        book = added_objects[0]
        assert isinstance(book.bsr_history, list)
        assert len(book.bsr_history) == 2
        assert book.bsr_history[0]["bsr"] == 2100
        assert book.bsr_history[1]["bsr"] == 1900


# ===========================================================================
# Tests: get_competitor
# ===========================================================================


class TestGetCompetitor:
    """Tests for MarketIntelligenceService.get_competitor."""

    @pytest.mark.asyncio
    async def test_returns_competitor_detail_when_found(self, service, mock_db):
        """get_competitor should return a CompetitorDetail when the row exists."""
        comp_id = uuid.uuid4()
        book = _make_competitor_book(id=comp_id, asin="B000000001")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = book
        mock_db.execute.return_value = mock_result

        result = await service.get_competitor(db=mock_db, competitor_id=comp_id)

        assert result is not None
        assert isinstance(result, CompetitorDetail)
        assert result.id == comp_id
        assert result.asin == "B000000001"
        assert result.bsr_history is not None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, service, mock_db):
        """get_competitor should raise AppException when the ID doesn't match any row."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        comp_id = uuid.uuid4()
        with pytest.raises(AppException) as exc_info:
            await service.get_competitor(db=mock_db, competitor_id=comp_id)
        assert exc_info.value.status_code == 404
        assert str(comp_id) in exc_info.value.message

    @pytest.mark.asyncio
    async def test_deserializes_bsr_history_from_jsonb(self, service, mock_db):
        """get_competitor should deserialize BSR history from the JSONB column."""
        comp_id = uuid.uuid4()
        book = _make_competitor_book(
            id=comp_id,
            bsr_history=[
                {"date": "2025-01-01T00:00:00+00:00", "bsr": 5000, "price": 9.99},
                {"date": "2025-02-01T00:00:00+00:00", "bsr": 4500, "price": 10.99},
                {"date": "2025-03-01T00:00:00+00:00", "bsr": 4000},
            ],
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = book
        mock_db.execute.return_value = mock_result

        result = await service.get_competitor(db=mock_db, competitor_id=comp_id)

        assert result is not None
        assert len(result.bsr_history) == 3
        assert result.bsr_history[0].bsr == 5000
        assert result.bsr_history[1].price == 10.99
        # Third point has no price key -- should default to None
        assert result.bsr_history[2].price is None


# ===========================================================================
# Tests: get_snapshots
# ===========================================================================


class TestGetSnapshots:
    """Tests for MarketIntelligenceService.get_snapshots."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_snapshots(self, service, mock_db):
        """get_snapshots should return [] when no snapshots exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_snapshots(db=mock_db, limit=10)

        assert result == []
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_mapped_market_snapshots(self, service, mock_db):
        """get_snapshots should map DB rows to MarketSnapshot schemas."""
        snap1 = _make_snapshot()
        snap2 = _make_snapshot(
            snapshot_date=date(2025, 3, 16),
            metrics={
                "avg_bsr": 15000.0,
                "avg_price": 13.99,
                "book_count": 180,
                "avg_reviews": 90.0,
                "competition_score": 55.0,
            },
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snap1, snap2]
        mock_db.execute.return_value = mock_result

        result = await service.get_snapshots(db=mock_db, limit=30)

        assert len(result) == 2
        assert isinstance(result[0], MarketSnapshot)
        assert result[0].avg_bsr == 12500.0
        assert result[0].category_name == "Self-Help"
        assert result[0].category_id == "154606011"
        assert result[1].avg_price == 13.99

    @pytest.mark.asyncio
    async def test_returns_empty_when_category_not_found_in_db(self, service, mock_db):
        """get_snapshots with category_id should return [] if category doesn't exist in DB."""
        # First call: category lookup returns None
        cat_result = MagicMock()
        cat_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = cat_result

        result = await service.get_snapshots(db=mock_db, category_id="nonexistent_node", limit=10)

        assert result == []

    @pytest.mark.asyncio
    async def test_filters_snapshots_by_category(self, service, mock_db):
        """get_snapshots with category_id should filter by the MarketCategory FK."""
        cat = _make_category(amazon_node_id="154606011")

        # First execute: category lookup
        cat_result = MagicMock()
        cat_result.scalar_one_or_none.return_value = cat

        # Second execute: snapshot query
        snap = _make_snapshot()
        snap_result = MagicMock()
        snap_result.scalars.return_value.all.return_value = [snap]

        mock_db.execute = AsyncMock(side_effect=[cat_result, snap_result])

        result = await service.get_snapshots(db=mock_db, category_id="154606011", limit=10)

        assert len(result) == 1
        assert isinstance(result[0], MarketSnapshot)
        # Verify db.execute was called twice: once for category, once for snapshots
        assert mock_db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_snapshot_metrics_default_to_zero_when_missing(self, service, mock_db):
        """get_snapshots should default metric values to 0 if metrics dict is empty."""
        snap = _make_snapshot(metrics={})
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snap]
        mock_db.execute.return_value = mock_result

        result = await service.get_snapshots(db=mock_db, limit=10)

        assert len(result) == 1
        assert result[0].avg_bsr == 0.0
        assert result[0].avg_price == 0.0
        assert result[0].book_count == 0
        assert result[0].avg_reviews == 0.0
        assert result[0].competition_score == 0.0

    @pytest.mark.asyncio
    async def test_snapshot_handles_none_metrics(self, service, mock_db):
        """get_snapshots should handle None metrics gracefully."""
        snap = _make_snapshot(metrics=None)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snap]
        mock_db.execute.return_value = mock_result

        result = await service.get_snapshots(db=mock_db, limit=10)

        assert len(result) == 1
        # When metrics is None, the service does `snap.metrics or {}`
        assert result[0].avg_bsr == 0.0
        assert result[0].book_count == 0


# ===========================================================================
# Tests: Mapping helpers (edge cases)
# ===========================================================================


class TestMappingHelpers:
    """Tests for private mapping methods exposed through the public API."""

    @pytest.mark.asyncio
    async def test_competitor_list_item_with_null_price(self, service, mock_db):
        """CompetitorListItem mapping should handle None price."""
        book = _make_competitor_book(price=None)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [book]
        mock_db.execute.return_value = mock_result

        result = await service.list_competitors(db=mock_db, marketplace="US")

        assert len(result) == 1
        assert result[0].price is None

    @pytest.mark.asyncio
    async def test_competitor_detail_with_empty_bsr_history(self, service, mock_db):
        """CompetitorDetail mapping should handle empty bsr_history list."""
        comp_id = uuid.uuid4()
        book = _make_competitor_book(id=comp_id, bsr_history=[])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = book
        mock_db.execute.return_value = mock_result

        result = await service.get_competitor(db=mock_db, competitor_id=comp_id)

        assert result is not None
        assert result.bsr_history == []

    @pytest.mark.asyncio
    async def test_competitor_detail_with_none_metadata_json(self, service, mock_db):
        """CompetitorDetail mapping should default marketplace when metadata_json is None."""
        comp_id = uuid.uuid4()
        book = _make_competitor_book(id=comp_id, metadata_json=None)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = book
        mock_db.execute.return_value = mock_result

        result = await service.get_competitor(db=mock_db, competitor_id=comp_id)

        assert result is not None
        # With None metadata_json, the mapper defaults to the marketplace parameter ("US")
        assert result.marketplace == "US"

    @pytest.mark.asyncio
    async def test_snapshot_category_fallback_when_no_relation(self, service, mock_db):
        """Snapshot mapping should fall back to category_id string when relation is None."""
        cat_id = uuid.uuid4()
        snap = _make_snapshot(category=None, category_id=cat_id)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snap]
        mock_db.execute.return_value = mock_result

        result = await service.get_snapshots(db=mock_db, limit=10)

        assert len(result) == 1
        assert result[0].category_id == str(cat_id)
        assert result[0].category_name == "Unknown"
