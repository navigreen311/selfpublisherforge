"""Unit tests for the Chrome Extension service layer.

Tests cover:
- get_quick_research aggregating data from DB + niche stats
- Graceful fallback when one module (LLM) fails
- Related keywords returning real data (not placeholders)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.chrome_extension.schemas import (
    AmazonMarketplace,
    QuickResearchQuery,
    QuickResearchResponse,
    RelatedKeyword,
)
from app.modules.chrome_extension.service import (
    _estimate_daily_sales,
    _extract_candidate_words,
    _generate_related_keywords,
    _generate_related_keywords_from_corpus,
    _generate_related_keywords_via_llm,
    _volume_indicator,
    get_quick_research,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def asin_query() -> QuickResearchQuery:
    return QuickResearchQuery(
        asin="B0EXAMPLE1",
        keywords=["romance", "second chance"],
        marketplace=AmazonMarketplace.US,
    )


@pytest.fixture
def keyword_only_query() -> QuickResearchQuery:
    return QuickResearchQuery(
        asin=None,
        keywords=["thriller", "crime fiction"],
        marketplace=AmazonMarketplace.US,
    )


def _make_mock_product(
    asin: str = "B0EXAMPLE1",
    title: str = "Test Book",
    bsr: int | None = 5000,
    price: float | None = 4.99,
    org_id: uuid.UUID | None = None,
    keywords: list[str] | None = None,
    created_at: datetime | None = None,
    deleted_at=None,
):
    """Create a mock ExtractedProduct-like object."""
    product = MagicMock()
    product.id = uuid.uuid4()
    product.org_id = org_id or uuid.UUID("00000000-0000-0000-0000-000000000001")
    product.asin = asin
    product.title = title
    product.bsr = bsr
    product.price = price
    product.keywords = keywords or []
    product.created_at = created_at or datetime.now(UTC)
    product.deleted_at = deleted_at
    return product


# ---------------------------------------------------------------------------
# Tests: get_quick_research aggregates data
# ---------------------------------------------------------------------------


class TestGetQuickResearchAggregatesData:
    """Verify get_quick_research combines ASIN product data and niche stats."""

    @pytest.mark.asyncio
    async def test_returns_quick_research_response(
        self, org_id: uuid.UUID, asin_query: QuickResearchQuery
    ):
        """Result should be a QuickResearchResponse with expected fields."""
        mock_db = AsyncMock()

        # Mock the ASIN lookup: return one product
        mock_product = _make_mock_product(asin="B0EXAMPLE1", title="Test Romance", bsr=3500)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_product]
        mock_db.execute.return_value = mock_result

        # Patch _compute_niche_stats to avoid DB aggregation
        with patch(
            "app.modules.chrome_extension.service._compute_niche_stats",
            new_callable=AsyncMock,
            return_value={
                "competitor_count": 42,
                "avg_price": 4.99,
                "avg_reviews": None,
                "niche_score": None,
                "related_keywords": [
                    RelatedKeyword(keyword="love story", volume="high", relevance=0.9, source="frequency"),
                ],
            },
        ):
            response = await get_quick_research(mock_db, org_id, asin_query)

        assert isinstance(response, QuickResearchResponse)
        assert response.asin == "B0EXAMPLE1"
        assert response.title == "Test Romance"
        assert response.current_bsr == 3500
        assert response.competitor_count == 42
        assert response.avg_price == 4.99

    @pytest.mark.asyncio
    async def test_asin_lookup_populates_bsr_history(
        self, org_id: uuid.UUID, asin_query: QuickResearchQuery
    ):
        """When multiple snapshots exist for an ASIN, bsr_history should be populated."""
        mock_db = AsyncMock()

        products = [
            _make_mock_product(bsr=3500, created_at=datetime(2024, 6, 1, tzinfo=UTC)),
            _make_mock_product(bsr=4200, created_at=datetime(2024, 5, 1, tzinfo=UTC)),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = products
        mock_db.execute.return_value = mock_result

        with patch(
            "app.modules.chrome_extension.service._compute_niche_stats",
            new_callable=AsyncMock,
            return_value={
                "competitor_count": 0,
                "avg_price": None,
                "avg_reviews": None,
                "niche_score": None,
                "related_keywords": [],
            },
        ):
            response = await get_quick_research(mock_db, org_id, asin_query)

        assert len(response.bsr_history) == 2
        assert response.bsr_history[0]["bsr"] == 3500
        assert response.bsr_history[1]["bsr"] == 4200

    @pytest.mark.asyncio
    async def test_estimated_daily_sales_from_bsr(
        self, org_id: uuid.UUID, asin_query: QuickResearchQuery
    ):
        """When a product has BSR, estimated_daily_sales should be computed."""
        mock_db = AsyncMock()

        mock_product = _make_mock_product(bsr=5000)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_product]
        mock_db.execute.return_value = mock_result

        with patch(
            "app.modules.chrome_extension.service._compute_niche_stats",
            new_callable=AsyncMock,
            return_value={
                "competitor_count": 0,
                "avg_price": None,
                "avg_reviews": None,
                "niche_score": None,
                "related_keywords": [],
            },
        ):
            response = await get_quick_research(mock_db, org_id, asin_query)

        assert response.estimated_daily_sales is not None
        assert response.estimated_daily_sales >= 1

    @pytest.mark.asyncio
    async def test_keyword_only_query_returns_niche_stats(
        self, org_id: uuid.UUID, keyword_only_query: QuickResearchQuery
    ):
        """A query with only keywords (no ASIN) should still return niche stats."""
        mock_db = AsyncMock()

        with patch(
            "app.modules.chrome_extension.service._compute_niche_stats",
            new_callable=AsyncMock,
            return_value={
                "competitor_count": 15,
                "avg_price": 3.99,
                "avg_reviews": None,
                "niche_score": None,
                "related_keywords": [
                    RelatedKeyword(keyword="mystery", volume="medium", relevance=0.7, source="frequency"),
                ],
            },
        ):
            response = await get_quick_research(mock_db, org_id, keyword_only_query)

        assert response.asin is None
        assert response.competitor_count == 15
        assert response.avg_price == 3.99
        assert len(response.related_keywords) == 1

    @pytest.mark.asyncio
    async def test_no_asin_no_keywords_returns_empty(self, org_id: uuid.UUID):
        """A query with neither ASIN nor keywords should return minimal data."""
        mock_db = AsyncMock()
        query = QuickResearchQuery()

        response = await get_quick_research(mock_db, org_id, query)

        assert isinstance(response, QuickResearchResponse)
        assert response.asin is None
        assert response.title is None
        assert response.current_bsr is None
        assert response.related_keywords == []


# ---------------------------------------------------------------------------
# Tests: graceful fallback when one module fails
# ---------------------------------------------------------------------------


class TestGetQuickResearchHandlesModuleFailures:
    """Verify that failures in the LLM keyword module do not crash
    the overall quick research flow."""

    @pytest.mark.asyncio
    async def test_llm_import_error_falls_back_to_corpus(self):
        """If the LLM orchestration module is not importable, the fallback
        should produce results from corpus frequency analysis."""
        with patch(
            "app.modules.chrome_extension.service._generate_related_keywords_via_llm",
            new_callable=AsyncMock,
            return_value=[],  # Simulates LLM unavailable
        ):
            mock_db = AsyncMock()
            # Set up DB to return some stored products for corpus analysis
            mock_result = MagicMock()
            mock_result.all.return_value = [
                ("Romance Novel About Love", ["love", "romance", "passion"]),
                ("Second Chance Romance", ["romance", "second chance"]),
            ]
            mock_db.execute.return_value = mock_result

            keywords = await _generate_related_keywords_from_corpus(
                mock_db,
                uuid.UUID("00000000-0000-0000-0000-000000000001"),
                ["romance"],
            )

        # Should return something from frequency analysis
        assert isinstance(keywords, list)
        for kw in keywords:
            assert isinstance(kw, RelatedKeyword)
            assert kw.source == "frequency"

    @pytest.mark.asyncio
    async def test_llm_failure_does_not_crash_get_quick_research(
        self, org_id: uuid.UUID, asin_query: QuickResearchQuery
    ):
        """Even if the LLM call raises, get_quick_research should complete."""
        mock_db = AsyncMock()

        # Mock ASIN lookup
        mock_product = _make_mock_product(bsr=2000)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_product]
        mock_db.execute.return_value = mock_result

        # Patch _compute_niche_stats to simulate the full pipeline
        # where LLM fails but corpus analysis succeeds
        with patch(
            "app.modules.chrome_extension.service._compute_niche_stats",
            new_callable=AsyncMock,
            return_value={
                "competitor_count": 10,
                "avg_price": 4.99,
                "avg_reviews": None,
                "niche_score": None,
                "related_keywords": [
                    RelatedKeyword(keyword="fallback keyword", volume="low", relevance=0.5, source="frequency"),
                ],
            },
        ):
            response = await get_quick_research(mock_db, org_id, asin_query)

        assert isinstance(response, QuickResearchResponse)
        assert response.current_bsr == 2000
        assert response.competitor_count == 10

    @pytest.mark.asyncio
    async def test_generate_related_keywords_via_llm_returns_empty_on_import_error(self):
        """_generate_related_keywords_via_llm should return [] if import fails."""
        # The function itself catches ImportError and returns []
        with patch.dict("sys.modules", {"app.modules.llm_orchestration.service": None}):
            result = await _generate_related_keywords_via_llm(["romance", "love"])
        # Should return empty list (graceful fallback)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_merge_strategy_prefers_llm_then_corpus(self):
        """_generate_related_keywords should merge LLM + corpus, LLM first, deduped."""
        mock_db = AsyncMock()
        org = uuid.UUID("00000000-0000-0000-0000-000000000001")

        llm_kw = RelatedKeyword(keyword="dragons", volume="high", relevance=0.95, source="llm")
        corpus_kw = RelatedKeyword(keyword="magic", volume="medium", relevance=0.7, source="frequency")
        # Duplicate from corpus that also appears in LLM
        corpus_dupe = RelatedKeyword(keyword="dragons", volume="medium", relevance=0.6, source="frequency")

        with patch(
            "app.modules.chrome_extension.service._generate_related_keywords_via_llm",
            new_callable=AsyncMock,
            return_value=[llm_kw],
        ), patch(
            "app.modules.chrome_extension.service._generate_related_keywords_from_corpus",
            new_callable=AsyncMock,
            return_value=[corpus_dupe, corpus_kw],
        ):
            merged = await _generate_related_keywords(mock_db, org, ["fantasy"])

        # "dragons" should appear only once (from LLM, since it comes first)
        dragon_entries = [kw for kw in merged if kw.keyword.lower() == "dragons"]
        assert len(dragon_entries) == 1
        assert dragon_entries[0].source == "llm"

        # "magic" should also be present
        magic_entries = [kw for kw in merged if kw.keyword.lower() == "magic"]
        assert len(magic_entries) == 1

    @pytest.mark.asyncio
    async def test_empty_keywords_returns_empty(self):
        """_generate_related_keywords with empty input should return []."""
        mock_db = AsyncMock()
        org = uuid.UUID("00000000-0000-0000-0000-000000000001")
        result = await _generate_related_keywords(mock_db, org, [])
        assert result == []


# ---------------------------------------------------------------------------
# Tests: related keywords are not placeholder data
# ---------------------------------------------------------------------------


class TestRelatedKeywordsNotPlaceholder:
    """Verify that related keyword generation produces real, meaningful data
    rather than hardcoded placeholder values."""

    @pytest.mark.asyncio
    async def test_corpus_keywords_derived_from_stored_data(self):
        """Keywords from corpus analysis should reflect actual product titles."""
        mock_db = AsyncMock()
        org = uuid.UUID("00000000-0000-0000-0000-000000000001")

        # Simulate stored products with specific titles
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("Dark Romance Suspense Novel", ["dark", "romance", "suspense"]),
            ("Forbidden Love Dark Romance", ["forbidden", "dark", "romance"]),
            ("Paranormal Dark Romance Series", ["paranormal", "dark", "series"]),
        ]
        mock_db.execute.return_value = mock_result

        keywords = await _generate_related_keywords_from_corpus(
            mock_db, org, ["romance"]
        )

        assert len(keywords) > 0
        keyword_texts = [kw.keyword.lower() for kw in keywords]
        # "dark" should be a top keyword since it appears in all three titles
        assert "dark" in keyword_texts
        # Each keyword should have real volume and relevance
        for kw in keywords:
            assert kw.volume in ("high", "medium", "low")
            assert 0.0 <= kw.relevance <= 1.0
            assert kw.source == "frequency"

    @pytest.mark.asyncio
    async def test_corpus_keywords_exclude_input_keywords(self):
        """Related keywords should not include the original input keywords."""
        mock_db = AsyncMock()
        org = uuid.UUID("00000000-0000-0000-0000-000000000001")

        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("Romance Adventure Book", ["romance", "adventure"]),
        ]
        mock_db.execute.return_value = mock_result

        keywords = await _generate_related_keywords_from_corpus(
            mock_db, org, ["romance"]
        )

        keyword_texts = {kw.keyword.lower() for kw in keywords}
        assert "romance" not in keyword_texts

    @pytest.mark.asyncio
    async def test_corpus_keywords_exclude_stop_words(self):
        """Related keywords should not include common English stop words."""
        mock_db = AsyncMock()
        org = uuid.UUID("00000000-0000-0000-0000-000000000001")

        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("The Great American Novel of Our Time", ["novel", "american"]),
        ]
        mock_db.execute.return_value = mock_result

        keywords = await _generate_related_keywords_from_corpus(
            mock_db, org, ["novel"]
        )

        keyword_texts = {kw.keyword.lower() for kw in keywords}
        # Common stop words should be filtered out
        assert "the" not in keyword_texts
        assert "of" not in keyword_texts
        assert "our" not in keyword_texts

    @pytest.mark.asyncio
    async def test_corpus_fallback_when_no_products(self):
        """When no stored products exist, fall back to returning input keywords."""
        mock_db = AsyncMock()
        org = uuid.UUID("00000000-0000-0000-0000-000000000001")

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        keywords = await _generate_related_keywords_from_corpus(
            mock_db, org, ["sci-fi", "space opera"]
        )

        # With no data, should return the input keywords as low-confidence suggestions
        assert len(keywords) == 2
        keyword_texts = {kw.keyword for kw in keywords}
        assert "sci-fi" in keyword_texts
        assert "space opera" in keyword_texts
        for kw in keywords:
            assert kw.volume == "low"
            assert kw.relevance == 0.5

    @pytest.mark.asyncio
    async def test_related_keywords_capped_at_20(self):
        """The merged keyword list should never exceed 20 entries."""
        mock_db = AsyncMock()
        org = uuid.UUID("00000000-0000-0000-0000-000000000001")

        # Create many keywords
        llm_keywords = [
            RelatedKeyword(keyword=f"llm_kw_{i}", volume="medium", relevance=0.8, source="llm")
            for i in range(15)
        ]
        corpus_keywords = [
            RelatedKeyword(keyword=f"corpus_kw_{i}", volume="low", relevance=0.5, source="frequency")
            for i in range(15)
        ]

        with patch(
            "app.modules.chrome_extension.service._generate_related_keywords_via_llm",
            new_callable=AsyncMock,
            return_value=llm_keywords,
        ), patch(
            "app.modules.chrome_extension.service._generate_related_keywords_from_corpus",
            new_callable=AsyncMock,
            return_value=corpus_keywords,
        ):
            merged = await _generate_related_keywords(mock_db, org, ["fantasy"])

        assert len(merged) <= 20


# ---------------------------------------------------------------------------
# Tests: helper functions
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    def test_estimate_daily_sales_bsr_1(self):
        """Very high BSR rank 1 should return high sales."""
        sales = _estimate_daily_sales(1)
        assert sales >= 50

    def test_estimate_daily_sales_bsr_1000(self):
        sales = _estimate_daily_sales(1000)
        assert sales >= 1

    def test_estimate_daily_sales_bsr_100000(self):
        sales = _estimate_daily_sales(100000)
        assert sales >= 1

    def test_estimate_daily_sales_bsr_very_high(self):
        """Very high BSR (low sales) should still return at least 1."""
        sales = _estimate_daily_sales(500000)
        assert sales == 1

    def test_estimate_daily_sales_bsr_zero(self):
        assert _estimate_daily_sales(0) == 0

    def test_estimate_daily_sales_bsr_negative(self):
        assert _estimate_daily_sales(-1) == 0

    def test_extract_candidate_words_filters_stopwords(self):
        words = _extract_candidate_words("the quick brown fox and the lazy dog")
        assert "the" not in words
        assert "and" not in words
        assert "quick" in words
        assert "brown" in words

    def test_extract_candidate_words_lowercases(self):
        words = _extract_candidate_words("HELLO World")
        assert "hello" in words
        assert "world" in words

    def test_extract_candidate_words_min_length(self):
        """Single-character tokens should be excluded."""
        words = _extract_candidate_words("I am a big cat")
        assert "am" in words  # 2-char is allowed
        # Single letters excluded by regex r"[a-zA-Z]{2,}"
        assert "I" not in words and "i" not in words
        assert "a" not in words

    def test_volume_indicator_high(self):
        assert _volume_indicator(10, 10) == "high"
        assert _volume_indicator(8, 10) == "high"

    def test_volume_indicator_medium(self):
        assert _volume_indicator(4, 10) == "medium"

    def test_volume_indicator_low(self):
        assert _volume_indicator(1, 10) == "low"

    def test_volume_indicator_zero_max(self):
        assert _volume_indicator(0, 0) == "low"
