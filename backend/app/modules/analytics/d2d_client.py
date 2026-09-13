"""Draft2Digital API client for royalty and catalog data.

Provides a structured ``D2DClient`` that communicates with the Draft2Digital
partner API using Bearer-token authentication and async HTTP via ``httpx``.

The factory function ``get_d2d_client()`` inspects application settings and
returns a configured client instance, or ``None`` when credentials are absent.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class D2DError(Exception):
    """Raised when a Draft2Digital API request fails in a non-recoverable way.

    Attributes:
        status_code: HTTP status code returned by the API, if available.
        detail: Human-readable description of what went wrong.
    """

    def __init__(
        self,
        detail: str = "Draft2Digital API error",
        *,
        status_code: int | None = None,
    ) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Retailer-slug to marketplace code mapping
# ---------------------------------------------------------------------------

_D2D_RETAILER_MAP: dict[str, str] = {
    "amazon": "US",
    "amazon_uk": "UK",
    "amazon_de": "DE",
    "amazon_fr": "FR",
    "amazon_au": "AU",
    "amazon_ca": "CA",
    "apple": "US",
    "apple_books": "US",
    "barnes_and_noble": "US",
    "nook": "US",
    "kobo": "US",
    "tolino": "DE",
    "scribd": "US",
    "overdrive": "US",
    "libraries": "US",
    "hoopla": "US",
    "vivlio": "FR",
    "palace_marketplace": "US",
}

# HTTP status codes eligible for automatic retry.
_RETRIABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


# ---------------------------------------------------------------------------
# D2D API Client
# ---------------------------------------------------------------------------


class D2DClient:
    """Async client for the Draft2Digital partner API.

    Authenticates with a Bearer token and provides methods to retrieve
    royalty reports and the published book catalog.  Transient failures
    (server errors, rate-limiting, timeouts) are retried automatically
    with exponential backoff.

    Args:
        api_key: Draft2Digital API key used as a Bearer token.
        base_url: Root URL for the D2D API (default: production endpoint).
    """

    _USER_AGENT = "SelfPublisherForge/0.1.0"
    _MAX_RETRIES = 3
    _REQUEST_TIMEOUT = 30.0  # seconds

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.draft2digital.com/v1",
    ) -> None:
        if not api_key:
            raise ValueError("api_key must be a non-empty string")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    # -- Internal helpers ---------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        """Return default headers for every D2D API request."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": self._USER_AGENT,
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Execute an HTTP request against the D2D API with retry.

        Retries up to ``_MAX_RETRIES`` times on retriable status codes and
        network errors, using exponential backoff (1 s, 2 s, 4 s).

        Args:
            method: HTTP method (``"GET"``, ``"POST"``, etc.).
            path: URL path relative to ``base_url`` (e.g. ``"/payouts/reports"``).
            params: Optional query-string parameters.

        Returns:
            Parsed JSON response body (dict or list).

        Raises:
            D2DError: On non-retriable client errors (4xx excluding 429) or
                after all retry attempts are exhausted.
        """
        url = f"{self._base_url}{path}"
        headers = self._build_headers()
        last_exc: Exception | None = None

        for attempt in range(self._MAX_RETRIES):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self._REQUEST_TIMEOUT),
                ) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=headers,
                        params=params,
                    )

                if response.status_code == 200:
                    return response.json()  # type: ignore[no-any-return]

                # Retriable server / rate-limit errors
                if response.status_code in _RETRIABLE_STATUS_CODES:
                    logger.warning(
                        "D2D API %s %s returned %d on attempt %d/%d: %s",
                        method,
                        path,
                        response.status_code,
                        attempt + 1,
                        self._MAX_RETRIES,
                        response.text[:500],
                    )
                    last_exc = D2DError(
                        f"D2D API error: HTTP {response.status_code}",
                        status_code=response.status_code,
                    )
                else:
                    # Non-retriable client errors (400, 401, 403, etc.)
                    logger.error(
                        "D2D API %s %s returned non-retriable status %d: %s",
                        method,
                        path,
                        response.status_code,
                        response.text[:500],
                    )
                    raise D2DError(
                        f"D2D API error: HTTP {response.status_code}",
                        status_code=response.status_code,
                    )

            except httpx.TimeoutException as exc:
                logger.warning(
                    "D2D API request %s %s timed out on attempt %d/%d: %s",
                    method,
                    path,
                    attempt + 1,
                    self._MAX_RETRIES,
                    exc,
                )
                last_exc = exc

            except httpx.RequestError as exc:
                logger.warning(
                    "D2D API request %s %s failed on attempt %d/%d: %s",
                    method,
                    path,
                    attempt + 1,
                    self._MAX_RETRIES,
                    exc,
                )
                last_exc = exc

            # Exponential backoff: 1 s, 2 s, 4 s
            if attempt < self._MAX_RETRIES - 1:
                backoff = 2**attempt
                logger.debug("Retrying D2D API request in %ds ...", backoff)
                await asyncio.sleep(backoff)

        raise D2DError(
            f"D2D API request failed after {self._MAX_RETRIES} attempts: {last_exc}",
        )

    # -- Response normalisation ---------------------------------------------

    @staticmethod
    def _normalise_royalty_entry(entry: dict[str, Any]) -> dict[str, Any]:
        """Convert a single raw D2D payout entry to the internal format.

        The internal format uses the following keys:
            title, isbn, units, revenue, currency, channel

        This mirrors the field names expected by downstream consumers such as
        the royalty importer and analytics aggregator.
        """
        title = entry.get("title") or entry.get("bookTitle", "Unknown")
        units_sold = int(entry.get("unitsSold", 0) or entry.get("units", 0))
        units_refunded = int(entry.get("unitsRefunded", 0))
        units = max(units_sold - units_refunded, 0)

        revenue = float(entry.get("royaltyAmount", 0) or entry.get("royalties", 0) or entry.get("netRevenue", 0))
        currency = entry.get("currency", "USD")

        isbn = entry.get("isbn") or entry.get("isbn13") or ""

        # Determine channel from retailer / marketplace
        marketplace = entry.get("marketplace", "")
        if not marketplace:
            retailer = (entry.get("retailer", "") or "").lower()
            marketplace = _D2D_RETAILER_MAP.get(retailer, "US")

        channel = entry.get("retailer", marketplace) or "draft2digital"

        return {
            "title": title,
            "isbn": isbn,
            "units": units,
            "revenue": revenue,
            "currency": currency,
            "channel": channel,
        }

    @staticmethod
    def _normalise_book_entry(entry: dict[str, Any]) -> dict[str, Any]:
        """Convert a single raw D2D book/catalog entry to the internal format.

        Returns a dict with keys: title, isbn, author, format, status, channels.
        """
        return {
            "title": entry.get("title") or entry.get("bookTitle", "Unknown"),
            "isbn": entry.get("isbn") or entry.get("isbn13") or "",
            "author": entry.get("author") or entry.get("authorName", ""),
            "format": (entry.get("format", "ebook") or "ebook").lower(),
            "status": entry.get("status", "unknown"),
            "channels": entry.get("channels") or entry.get("retailers") or [],
        }

    # -- Public interface ---------------------------------------------------

    async def fetch_royalties(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Fetch royalty / payout reports from the D2D API.

        Requests payout data for the date range ``[start_date, end_date]``
        and normalises each entry into the internal record format with keys:
        ``title``, ``isbn``, ``units``, ``revenue``, ``currency``, ``channel``.

        Args:
            start_date: Inclusive start of the reporting period.
            end_date: Inclusive end of the reporting period.

        Returns:
            A list of normalised royalty-record dicts, possibly empty if the
            API returns no data for the requested period.

        Raises:
            D2DError: On non-retriable HTTP errors or exhausted retries.
        """
        params: dict[str, str] = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }

        logger.info(
            "Fetching D2D royalties for period %s to %s",
            params["startDate"],
            params["endDate"],
        )

        data = await self._request("GET", "/payouts/reports", params=params)

        # The API may return a top-level list or a dict with a key.
        if isinstance(data, list):
            payout_items = data
        else:
            payout_items = data.get("payouts") or data.get("reports") or data.get("sales") or []

        if not payout_items:
            logger.info("D2D API returned no payout items for the requested period.")
            return []

        records: list[dict] = []
        for entry in payout_items:
            try:
                records.append(self._normalise_royalty_entry(entry))
            except (KeyError, ValueError, TypeError) as exc:
                logger.warning("Skipping unparseable D2D payout entry: %s", exc)

        logger.info(
            "Normalised %d royalty records from %d raw D2D payout items.",
            len(records),
            len(payout_items),
        )
        return records

    async def fetch_book_list(self) -> list[dict]:
        """Fetch the published book catalog from the D2D API.

        Returns a list of normalised book dicts with keys:
        ``title``, ``isbn``, ``author``, ``format``, ``status``, ``channels``.

        Raises:
            D2DError: On non-retriable HTTP errors or exhausted retries.
        """
        logger.info("Fetching D2D book catalog.")

        data = await self._request("GET", "/books")

        if isinstance(data, list):
            book_items = data
        else:
            book_items = data.get("books") or data.get("titles") or data.get("catalog") or []

        if not book_items:
            logger.info("D2D API returned an empty book catalog.")
            return []

        books: list[dict] = []
        for entry in book_items:
            try:
                books.append(self._normalise_book_entry(entry))
            except (KeyError, ValueError, TypeError) as exc:
                logger.warning("Skipping unparseable D2D book entry: %s", exc)

        logger.info(
            "Normalised %d books from %d raw D2D catalog items.",
            len(books),
            len(book_items),
        )
        return books


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_d2d_client() -> D2DClient | None:
    """Return a configured ``D2DClient`` if credentials are available.

    Reads the ``D2D_API_KEY`` and ``D2D_API_URL`` values from the environment
    (via ``app.config.get_settings`` is not used here because these values are
    read directly from ``os.environ``, matching the existing pattern in
    ``analytics.py``).  When the API key is missing or empty, ``None`` is
    returned and a warning is logged.

    Returns:
        A ready-to-use ``D2DClient``, or ``None`` if credentials are not set.
    """
    import os

    api_key = os.environ.get("D2D_API_KEY", "")
    if not api_key:
        logger.warning("D2D API key (D2D_API_KEY) not configured; " "D2DClient will not be available.")
        return None

    base_url = os.environ.get(
        "D2D_API_URL",
        "https://api.draft2digital.com/v1",
    )

    logger.info(
        "D2D API key found. Creating D2DClient (base_url=%s).",
        base_url,
    )
    return D2DClient(api_key=api_key, base_url=base_url)
