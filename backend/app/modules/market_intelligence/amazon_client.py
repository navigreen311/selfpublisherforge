"""Amazon Product API client with a mock/development fallback.

In production, the ``LiveAmazonClient`` integrates with the Amazon Product
Advertising API (PA-API 5.0) using HMAC-SHA256 signed requests over HTTPS.
For development and testing, the ``MockAmazonClient`` returns realistic
synthetic data so the rest of the module can run without live credentials.

The factory function ``get_amazon_client()`` inspects environment variables
and returns the appropriate implementation automatically.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

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
        category_id: str | None = None,
        marketplace: str = "US",
        max_results: int = 20,
    ) -> list[CompetitorSummary]:
        ...

    @abstractmethod
    async def get_product_detail(
        self, asin: str, marketplace: str = "US"
    ) -> CompetitorSummary | None:
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
        self, root_id: str | None = None, marketplace: str = "US"
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
        category_id: str | None = None,
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
    ) -> CompetitorSummary | None:
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
        now = datetime.now(tz=UTC)
        points: list[BSRHistoryPoint] = []
        for d in range(days):
            date = now - timedelta(days=days - d)
            bsr = max(1, base_bsr + rng.randint(-base_bsr // 10, base_bsr // 10))
            price = round(rng.uniform(2.99, 24.99), 2)
            points.append(BSRHistoryPoint(date=date, bsr=bsr, price=price))
        return points

    async def get_category_tree(
        self, root_id: str | None = None, marketplace: str = "US"
    ) -> list[dict]:
        if root_id:
            for cat in _SAMPLE_CATEGORIES:
                if cat["id"] == root_id:
                    return [cat]
                children = cat.get("children", [])
                if isinstance(children, list):
                    for child in children:
                        if isinstance(child, dict) and child.get("id") == root_id:
                            return [child]
            return []
        return _SAMPLE_CATEGORIES


# ---------------------------------------------------------------------------
# PA-API 5.0 marketplace host mapping
# ---------------------------------------------------------------------------

_MARKETPLACE_HOSTS: dict[str, str] = {
    "US": "webservices.amazon.com",
    "CA": "webservices.amazon.ca",
    "UK": "webservices.amazon.co.uk",
    "GB": "webservices.amazon.co.uk",
    "DE": "webservices.amazon.de",
    "FR": "webservices.amazon.fr",
    "ES": "webservices.amazon.es",
    "IT": "webservices.amazon.it",
    "JP": "webservices.amazon.co.jp",
    "IN": "webservices.amazon.in",
    "BR": "webservices.amazon.com.br",
    "MX": "webservices.amazon.com.mx",
    "AU": "webservices.amazon.com.au",
}

_MARKETPLACE_REGIONS: dict[str, str] = {
    "US": "us-east-1",
    "CA": "us-east-1",
    "UK": "eu-west-1",
    "GB": "eu-west-1",
    "DE": "eu-west-1",
    "FR": "eu-west-1",
    "ES": "eu-west-1",
    "IT": "eu-west-1",
    "JP": "us-west-2",
    "IN": "eu-west-1",
    "BR": "us-east-1",
    "MX": "us-east-1",
    "AU": "us-west-2",
}


# ---------------------------------------------------------------------------
# Live PA-API 5.0 client
# ---------------------------------------------------------------------------

class LiveAmazonClient(AmazonClientBase):
    """Calls the Amazon Product Advertising API 5.0 over HTTPS.

    Requests are authenticated with AWS Signature Version 4 (HMAC-SHA256).
    A simple rate-limiter enforces the 1 request/second PA-API throttle.
    All public methods return the same schema types as ``MockAmazonClient``
    so callers are fully interchangeable.
    """

    _SERVICE = "ProductAdvertisingAPI"
    _PA_API_PATH = "/paapi5"

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        partner_tag: str,
        *,
        request_timeout: float = 15.0,
        min_request_interval: float = 1.0,
    ) -> None:
        self._access_key = access_key
        self._secret_key = secret_key
        self._partner_tag = partner_tag
        self._timeout = request_timeout
        self._min_interval = min_request_interval
        self._last_request_ts: float = 0.0
        self._rate_lock = asyncio.Lock()
        self._client = httpx.AsyncClient(timeout=request_timeout)

    # -- AWS Signature V4 helpers -------------------------------------------

    @staticmethod
    def _sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _hmac_sha256(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _get_signing_key(self, date_stamp: str, region: str) -> bytes:
        """Derive the AWS V4 signing key for the given date/region."""
        k_date = self._hmac_sha256(
            f"AWS4{self._secret_key}".encode(), date_stamp
        )
        k_region = self._hmac_sha256(k_date, region)
        k_service = self._hmac_sha256(k_region, self._SERVICE)
        k_signing = self._hmac_sha256(k_service, "aws4_request")
        return k_signing

    def _sign_request(
        self,
        *,
        host: str,
        region: str,
        path: str,
        payload: bytes,
        amz_target: str,
    ) -> dict[str, str]:
        """Build signed headers for a PA-API POST request.

        Returns a dict of HTTP headers to include in the request.
        """
        now = datetime.now(tz=UTC)
        date_stamp = now.strftime("%Y%m%d")
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")

        content_type = "application/json; charset=UTF-8"
        payload_hash = self._sha256(payload)

        # Canonical request
        canonical_headers = (
            f"content-encoding:amz-1.0\n"
            f"content-type:{content_type}\n"
            f"host:{host}\n"
            f"x-amz-date:{amz_date}\n"
            f"x-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{amz_target}\n"
        )
        signed_headers = "content-encoding;content-type;host;x-amz-date;x-amz-target"

        canonical_request = (
            f"POST\n"
            f"{path}\n"
            f"\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )

        # String to sign
        credential_scope = f"{date_stamp}/{region}/{self._SERVICE}/aws4_request"
        string_to_sign = (
            f"AWS4-HMAC-SHA256\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{self._sha256(canonical_request.encode('utf-8'))}"
        )

        # Signature
        signing_key = self._get_signing_key(date_stamp, region)
        signature = hmac.new(
            signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        authorization = (
            f"AWS4-HMAC-SHA256 "
            f"Credential={self._access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        return {
            "Authorization": authorization,
            "Content-Encoding": "amz-1.0",
            "Content-Type": content_type,
            "Host": host,
            "X-Amz-Date": amz_date,
            "X-Amz-Target": f"com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{amz_target}",
        }

    # -- Rate limiter -------------------------------------------------------

    async def _throttle(self) -> None:
        """Ensure at least ``_min_interval`` seconds between requests."""
        async with self._rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_ts
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request_ts = time.monotonic()

    # -- Core HTTP caller ---------------------------------------------------

    async def _call_paapi(
        self,
        operation: str,
        payload: dict[str, Any],
        marketplace: str = "US",
    ) -> dict[str, Any]:
        """Send a signed POST to PA-API and return the JSON response body.

        Returns an empty dict on any transport or API-level error so callers
        never have to worry about exceptions from network failures.
        """
        marketplace = marketplace.upper()
        host = _MARKETPLACE_HOSTS.get(marketplace, _MARKETPLACE_HOSTS["US"])
        region = _MARKETPLACE_REGIONS.get(marketplace, _MARKETPLACE_REGIONS["US"])
        path = f"{self._PA_API_PATH}/{operation}"
        url = f"https://{host}{path}"

        body = json.dumps(payload).encode("utf-8")
        headers = self._sign_request(
            host=host,
            region=region,
            path=path,
            payload=body,
            amz_target=operation,
        )

        await self._throttle()

        try:
            response = await self._client.post(url, content=body, headers=headers)
            if response.status_code == 429:
                logger.warning("PA-API rate limit hit (429). Backing off 2 seconds.")
                await asyncio.sleep(2.0)
                response = await self._client.post(url, content=body, headers=headers)

            if response.status_code != 200:
                logger.error(
                    "PA-API %s returned HTTP %d: %s",
                    operation,
                    response.status_code,
                    response.text[:500],
                )
                return {}

            return response.json()  # type: ignore[no-any-return]

        except httpx.TimeoutException:
            logger.error("PA-API %s request timed out after %.1fs", operation, self._timeout)
            return {}
        except httpx.HTTPError as exc:
            logger.error("PA-API %s HTTP error: %s", operation, exc)
            return {}
        except (ConnectionError, TimeoutError, ValueError):
            logger.error("Unexpected error calling PA-API %s", operation, exc_info=True)
            return {}

    # -- Response parsers ---------------------------------------------------

    def _parse_item(self, item: dict[str, Any]) -> CompetitorSummary:
        """Convert a PA-API SearchResult/ItemResult item to CompetitorSummary."""
        info = item.get("ItemInfo", {})
        title_info = info.get("Title", {})
        by_line = info.get("ByLineInfo", {})
        authors = by_line.get("Contributors", [])
        author_name = ""
        for contributor in authors:
            if contributor.get("RoleType") == "author":
                author_name = contributor.get("Name", "")
                break
        if not author_name and authors:
            author_name = authors[0].get("Name", "")

        offers = item.get("Offers", {})
        listings = offers.get("Listings", [])
        price: float | None = None
        if listings:
            price_info = listings[0].get("Price", {})
            price = price_info.get("Amount")

        browse_info = item.get("BrowseNodeInfo", {})
        sales_rank = browse_info.get("WebsiteSalesRank", {})
        bsr: int | None = None
        if sales_rank:
            bsr = sales_rank.get("SalesRank")

        images = item.get("Images", {})
        primary = images.get("Primary", {})
        medium_img = primary.get("Medium", {})
        image_url = medium_img.get("URL")

        reviews_count = 0
        rating: float | None = None

        return CompetitorSummary(
            asin=item.get("ASIN", ""),
            title=title_info.get("DisplayValue", "Unknown Title"),
            author=author_name,
            bsr=bsr,
            price=price,
            reviews_count=reviews_count,
            rating=rating,
            image_url=image_url,
        )

    def _parse_browse_node(self, node: dict[str, Any]) -> dict[str, Any]:
        """Convert a PA-API BrowseNode to a dict matching mock format."""
        children: list[dict[str, Any]] = []
        for child in node.get("Children", []):
            children.append(self._parse_browse_node(child))

        return {
            "id": node.get("Id", ""),
            "name": node.get("DisplayName", node.get("ContextFreeName", "")),
            "parent_id": node.get("Ancestor", {}).get("Id"),
            "children": children,
            "book_count": None,
        }

    # -- Public interface (matches AmazonClientBase) ------------------------

    async def search_products(
        self,
        keywords: str,
        category_id: str | None = None,
        marketplace: str = "US",
        max_results: int = 20,
    ) -> list[CompetitorSummary]:
        """Search for products on Amazon using PA-API SearchItems.

        Args:
            keywords: Search query string.
            category_id: Optional Amazon browse-node ID to narrow results.
            marketplace: Two-letter marketplace code (default ``"US"``).
            max_results: Maximum items to return (PA-API caps at 10 per request).

        Returns:
            A list of ``CompetitorSummary`` items, or an empty list on error.
        """
        # PA-API allows max 10 results per SearchItems call.
        items_per_page = min(max_results, 10)

        payload: dict[str, Any] = {
            "Keywords": keywords,
            "ItemCount": items_per_page,
            "PartnerTag": self._partner_tag,
            "PartnerType": "Associates",
            "Resources": [
                "ItemInfo.Title",
                "ItemInfo.ByLineInfo",
                "Offers.Listings.Price",
                "Images.Primary.Medium",
                "BrowseNodeInfo.WebsiteSalesRank",
            ],
        }
        if category_id:
            payload["BrowseNodeId"] = category_id

        all_items: list[CompetitorSummary] = []
        # Collect results, paginating if more than 10 are requested.
        pages_needed = (max_results + 9) // 10
        for page in range(1, pages_needed + 1):
            payload["ItemPage"] = page
            data = await self._call_paapi("SearchItems", payload, marketplace)
            search_result = data.get("SearchResult", {})
            raw_items = search_result.get("Items", [])
            if not raw_items:
                break
            for item in raw_items:
                all_items.append(self._parse_item(item))
            if len(all_items) >= max_results:
                break

        return all_items[:max_results]

    async def get_product_detail(
        self, asin: str, marketplace: str = "US"
    ) -> CompetitorSummary | None:
        """Retrieve details for a single ASIN via PA-API GetItems.

        Args:
            asin: The Amazon Standard Identification Number.
            marketplace: Two-letter marketplace code.

        Returns:
            A ``CompetitorSummary`` or ``None`` if the item was not found.
        """
        payload: dict[str, Any] = {
            "ItemIds": [asin],
            "PartnerTag": self._partner_tag,
            "PartnerType": "Associates",
            "Resources": [
                "ItemInfo.Title",
                "ItemInfo.ByLineInfo",
                "Offers.Listings.Price",
                "Images.Primary.Medium",
                "BrowseNodeInfo.WebsiteSalesRank",
            ],
        }
        data = await self._call_paapi("GetItems", payload, marketplace)
        items_result = data.get("ItemsResult", {})
        raw_items = items_result.get("Items", [])
        if not raw_items:
            logger.debug("PA-API GetItems returned no results for ASIN %s", asin)
            return None
        return self._parse_item(raw_items[0])

    async def get_keyword_data(
        self, keywords: list[str], marketplace: str = "US"
    ) -> list[KeywordData]:
        """Estimate keyword metrics by issuing PA-API SearchItems for each keyword.

        PA-API does not expose search volume or CPC directly, so this method
        uses the total number of search results and average BSR as rough
        proxies.  For production-grade keyword data, consider supplementing
        with a dedicated keyword-research provider.

        Args:
            keywords: List of keyword strings to analyse.
            marketplace: Two-letter marketplace code.

        Returns:
            A list of ``KeywordData`` items (one per keyword).
        """
        results: list[KeywordData] = []

        for kw in keywords:
            payload: dict[str, Any] = {
                "Keywords": kw,
                "ItemCount": 10,
                "PartnerTag": self._partner_tag,
                "PartnerType": "Associates",
                "Resources": [
                    "BrowseNodeInfo.WebsiteSalesRank",
                    "Offers.Listings.Price",
                ],
            }
            data = await self._call_paapi("SearchItems", payload, marketplace)
            search_result = data.get("SearchResult", {})
            total = search_result.get("TotalResultCount", 0)
            raw_items = search_result.get("Items", [])

            # Estimate search volume from total result count (rough proxy).
            search_volume = total if isinstance(total, int) else 0

            # Derive competition score from the number of results.
            competition = min(1.0, search_volume / 100_000) if search_volume else 0.5

            # Average BSR of returned items can hint at demand.
            bsr_values = []
            for item in raw_items:
                sr = (
                    item.get("BrowseNodeInfo", {})
                    .get("WebsiteSalesRank", {})
                    .get("SalesRank")
                )
                if sr is not None:
                    bsr_values.append(sr)
            avg_bsr = sum(bsr_values) / len(bsr_values) if bsr_values else 0

            # CPC is not available from PA-API; set to 0.
            results.append(
                KeywordData(
                    keyword=kw,
                    search_volume=search_volume,
                    competition=round(competition, 2),
                    cpc=0.0,
                    trend=TrendDirection.STABLE,
                    trend_data=[],
                    relevance_score=round(
                        max(0.0, min(100.0, 100.0 - (avg_bsr / 2000.0)))
                        if avg_bsr
                        else 50.0,
                        1,
                    ),
                )
            )

        return results

    async def get_bsr_history(
        self, asin: str, days: int = 90, marketplace: str = "US"
    ) -> list[BSRHistoryPoint]:
        """Return BSR history for an ASIN.

        PA-API 5.0 does not provide historical BSR data.  This method
        fetches the *current* BSR and price via ``GetItems`` and returns
        a single-point list representing today's snapshot.  Consumers that
        need a full time series should persist these snapshots in a local
        database and build the history over successive polling cycles.

        Args:
            asin: The ASIN to look up.
            days: Ignored (PA-API has no historical endpoint).
            marketplace: Two-letter marketplace code.

        Returns:
            A list with at most one ``BSRHistoryPoint`` (today's snapshot),
            or an empty list on error.
        """
        detail = await self.get_product_detail(asin, marketplace)
        if detail is None or detail.bsr is None:
            return []
        return [
            BSRHistoryPoint(
                date=datetime.now(tz=UTC),
                bsr=detail.bsr,
                price=detail.price,
            )
        ]

    async def get_category_tree(
        self, root_id: str | None = None, marketplace: str = "US"
    ) -> list[dict]:
        """Retrieve the browse-node tree via PA-API GetBrowseNodes.

        Args:
            root_id: A browse-node ID to start from. If ``None`` the Kindle
                     Store root (``154606011``) is used by default.
            marketplace: Two-letter marketplace code.

        Returns:
            A list of category dicts, or an empty list on error.
        """
        node_id = root_id or "154606011"  # Kindle Store root

        payload: dict[str, Any] = {
            "BrowseNodeIds": [node_id],
            "PartnerTag": self._partner_tag,
            "PartnerType": "Associates",
            "Resources": [
                "BrowseNodes.Ancestor",
                "BrowseNodes.Children",
            ],
        }
        data = await self._call_paapi("GetBrowseNodes", payload, marketplace)
        browse_result = data.get("BrowseNodesResult", {})
        raw_nodes = browse_result.get("BrowseNodes", [])
        if not raw_nodes:
            return []

        return [self._parse_browse_node(node) for node in raw_nodes]

    async def close(self) -> None:
        """Close the underlying HTTP client. Safe to call multiple times."""
        await self._client.aclose()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_amazon_client() -> AmazonClientBase:
    """Return the appropriate Amazon client based on environment configuration.

    When the three PA-API credential environment variables are all set and
    non-empty, a ``LiveAmazonClient`` that makes real HTTPS requests to
    Amazon PA-API 5.0 is returned.  Otherwise falls back to the
    ``MockAmazonClient`` which provides synthetic data for development
    and testing.

    Environment variables:
        AMAZON_PAAPI_ACCESS_KEY  -- AWS access-key for PA-API
        AMAZON_PAAPI_SECRET_KEY  -- AWS secret-key for PA-API
        AMAZON_PAAPI_PARTNER_TAG -- Amazon Associates partner/tracking tag
    """
    import os

    access_key = os.environ.get("AMAZON_PAAPI_ACCESS_KEY", "")
    secret_key = os.environ.get("AMAZON_PAAPI_SECRET_KEY", "")
    partner_tag = os.environ.get("AMAZON_PAAPI_PARTNER_TAG", "")

    if access_key and secret_key and partner_tag:
        logger.info(
            "PA-API credentials found. Using LiveAmazonClient (partner_tag=%s)",
            partner_tag,
        )
        return LiveAmazonClient(
            access_key=access_key,
            secret_key=secret_key,
            partner_tag=partner_tag,
        )

    logger.info(
        "PA-API credentials not configured. Using MockAmazonClient for market "
        "intelligence data. Set AMAZON_PAAPI_ACCESS_KEY, AMAZON_PAAPI_SECRET_KEY, "
        "and AMAZON_PAAPI_PARTNER_TAG to enable live data."
    )
    return MockAmazonClient()
