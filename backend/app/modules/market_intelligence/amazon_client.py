"""Amazon Product API client with a mock/development fallback.

In production, this would integrate with the Amazon Product Advertising API
(PA-API 5.0). For development and testing, the ``MockAmazonClient`` is used
which returns realistic-looking synthetic data so the rest of the module
can be developed and tested end-to-end without live API credentials.
"""

from __future__ import annotations

import hashlib
import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

from app.modules.market_intelligence.schemas import (
    BSRHistoryPoint,
    CompetitorSummary,
    KeywordData,
    TrendDirection,
)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class AmazonClientBase(ABC):
    """Interface that every Amazon API adapter must implement."""

    @abstractmethod
    async def search_products(
        self,
        keywords: str,
        category_id: Optional[str] = None,
        marketplace: str = "US",
        max_results: int = 20,
    ) -> list[CompetitorSummary]:
        ...

    @abstractmethod
    async def get_product_detail(
        self, asin: str, marketplace: str = "US"
    ) -> Optional[CompetitorSummary]:
        ...

    @abstractmethod
    async def get_keyword_data(
        self, keywords: list[str], marketplace: str = "US"
    ) -> list[KeywordData]:
        ...

    @abstractmethod
    async def get_bsr_history(
        self, asin: str, days: int = 90, marketplace: str = "US"
    ) -> list[BSRHistoryPoint]:
        ...

    @abstractmethod
    async def get_category_tree(
        self, root_id: Optional[str] = None, marketplace: str = "US"
    ) -> list[dict]:
        ...


# ---------------------------------------------------------------------------
# Deterministic seed helper
# ---------------------------------------------------------------------------

def _seed_from(text: str) -> int:
    """Return a stable integer seed from an arbitrary string."""
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)


# ---------------------------------------------------------------------------
# Mock client (dev / test)
# ---------------------------------------------------------------------------

_SAMPLE_CATEGORIES = [
    {"id": "154606011", "name": "Self-Help", "parent_id": None, "children": [
        {"id": "11076", "name": "Motivational", "parent_id": "154606011", "children": [], "book_count": 4500},
        {"id": "11077", "name": "Personal Transformation", "parent_id": "154606011", "children": [], "book_count": 3200},
    ], "book_count": 18000},
    {"id": "18574", "name": "Romance", "parent_id": None, "children": [
        {"id": "18575", "name": "Contemporary Romance", "parent_id": "18574", "children": [], "book_count": 25000},
        {"id": "18576", "name": "Historical Romance", "parent_id": "18574", "children": [], "book_count": 12000},
    ], "book_count": 60000},
    {"id": "10399", "name": "Mystery, Thriller & Suspense", "parent_id": None, "children": [
        {"id": "10400", "name": "Mystery", "parent_id": "10399", "children": [], "book_count": 30000},
        {"id": "10401", "name": "Thriller", "parent_id": "10399", "children": [], "book_count": 22000},
    ], "book_count": 75000},
    {"id": "4736", "name": "Science Fiction & Fantasy", "parent_id": None, "children": [
        {"id": "4737", "name": "Science Fiction", "parent_id": "4736", "children": [], "book_count": 20000},
        {"id": "4738", "name": "Fantasy", "parent_id": "4736", "children": [], "book_count": 28000},
    ], "book_count": 55000},
    {"id": "2549", "name": "Business & Money", "parent_id": None, "children": [
        {"id": "2550", "name": "Entrepreneurship", "parent_id": "2549", "children": [], "book_count": 8000},
        {"id": "2551", "name": "Investing", "parent_id": "2549", "children": [], "book_count": 6000},
    ], "book_count": 35000},
]


class MockAmazonClient(AmazonClientBase):
    """Returns deterministic but realistic-looking synthetic data."""

    async def search_products(
        self,
        keywords: str,
        category_id: Optional[str] = None,
        marketplace: str = "US",
        max_results: int = 20,
    ) -> list[CompetitorSummary]:
        rng = random.Random(_seed_from(keywords))
        results: list[CompetitorSummary] = []
        for i in range(min(max_results, 20)):
            asin = f"B{rng.randint(0, 10**9 - 1):09d}"
            results.append(
                CompetitorSummary(
                    asin=asin,
                    title=f"{keywords.title()} Book #{i + 1}",
                    author=f"Author {rng.choice(['Smith', 'Johnson', 'Brown', 'Garcia', 'Lee'])}",
                    bsr=rng.randint(500, 200000),
                    price=round(rng.uniform(2.99, 24.99), 2),
                    reviews_count=rng.randint(0, 5000),
                    rating=round(rng.uniform(3.0, 5.0), 1),
                    image_url=f"https://placehold.co/200x300?text={asin}",
                )
            )
        return results

    async def get_product_detail(
        self, asin: str, marketplace: str = "US"
    ) -> Optional[CompetitorSummary]:
        rng = random.Random(_seed_from(asin))
        return CompetitorSummary(
            asin=asin,
            title=f"Book {asin[-4:]}",
            author=f"Author {rng.choice(['Smith', 'Johnson', 'Brown', 'Garcia', 'Lee'])}",
            bsr=rng.randint(500, 200000),
            price=round(rng.uniform(2.99, 24.99), 2),
            reviews_count=rng.randint(10, 5000),
            rating=round(rng.uniform(3.0, 5.0), 1),
            image_url=f"https://placehold.co/200x300?text={asin}",
        )

    async def get_keyword_data(
        self, keywords: list[str], marketplace: str = "US"
    ) -> list[KeywordData]:
        results: list[KeywordData] = []
        for kw in keywords:
            rng = random.Random(_seed_from(kw))
            sv = rng.randint(100, 50000)
            trend_data = [max(0, sv + rng.randint(-sv // 5, sv // 5)) for _ in range(12)]
            slope = (trend_data[-1] - trend_data[0]) / max(trend_data[0], 1)
            if slope > 0.05:
                direction = TrendDirection.UP
            elif slope < -0.05:
                direction = TrendDirection.DOWN
            else:
                direction = TrendDirection.STABLE
            results.append(
                KeywordData(
                    keyword=kw,
                    search_volume=sv,
                    competition=round(rng.uniform(0.05, 0.95), 2),
                    cpc=round(rng.uniform(0.10, 3.50), 2),
                    trend=direction,
                    trend_data=[float(v) for v in trend_data],
                    relevance_score=round(rng.uniform(40, 99), 1),
                )
            )
        return results

    async def get_bsr_history(
        self, asin: str, days: int = 90, marketplace: str = "US"
    ) -> list[BSRHistoryPoint]:
        rng = random.Random(_seed_from(asin))
        base_bsr = rng.randint(1000, 100000)
        now = datetime.now(tz=timezone.utc)
        points: list[BSRHistoryPoint] = []
        for d in range(days):
            date = now - timedelta(days=days - d)
            bsr = max(1, base_bsr + rng.randint(-base_bsr // 10, base_bsr // 10))
            price = round(rng.uniform(2.99, 24.99), 2)
            points.append(BSRHistoryPoint(date=date, bsr=bsr, price=price))
        return points

    async def get_category_tree(
        self, root_id: Optional[str] = None, marketplace: str = "US"
    ) -> list[dict]:
        if root_id:
            for cat in _SAMPLE_CATEGORIES:
                if cat["id"] == root_id:
                    return [cat]
                for child in cat.get("children", []):
                    if child["id"] == root_id:
                        return [child]
            return []
        return _SAMPLE_CATEGORIES


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_amazon_client() -> AmazonClientBase:
    """Return the Amazon client.

    When PA-API credentials are configured via environment variables,
    a live client would be returned. Until PA-API integration is implemented,
    falls back to the mock client for development and testing.
    """
    import os

    access_key = os.environ.get("AMAZON_PAAPI_ACCESS_KEY", "")
    secret_key = os.environ.get("AMAZON_PAAPI_SECRET_KEY", "")
    partner_tag = os.environ.get("AMAZON_PAAPI_PARTNER_TAG", "")

    if access_key and secret_key and partner_tag:
        logger.warning(
            "PA-API credentials provided but LiveAmazonClient is not yet implemented. "
            "Falling back to MockAmazonClient. Implement LiveAmazonClient to use real data."
        )

    logger.info("Using MockAmazonClient for market intelligence data")
    return MockAmazonClient()
