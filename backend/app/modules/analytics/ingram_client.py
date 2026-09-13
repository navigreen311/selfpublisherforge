"""IngramSpark publisher REST API client.

Provides an async HTTP client for the IngramSpark reporting API, with
HMAC-SHA256 request signing, automatic retry with exponential backoff,
and response normalisation into the internal royalty-record format used
throughout the analytics module.

The factory function ``get_ingram_client()`` reads credentials from
environment variables and returns ``None`` when they are not configured,
allowing callers to gracefully skip IngramSpark integration.

Environment variables:
    INGRAM_SPARK_API_KEY    -- Publisher API key
    INGRAM_SPARK_API_SECRET -- Publisher API secret (used for HMAC signing)
    INGRAM_SPARK_API_URL    -- Optional base URL override
                               (default: ``https://api.ingramspark.com/v1``)
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import time
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, cast

import httpx

logger = logging.getLogger(__name__)

# Default request timeout (seconds) and retry configuration.
_DEFAULT_TIMEOUT: float = 30.0
_MAX_RETRIES: int = 3
_USER_AGENT: str = "SelfPublisherForge/0.1.0"

# HTTP status codes that are safe to retry.
_RETRIABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class IngramSparkError(Exception):
    """Base exception for IngramSpark API errors.

    Attributes:
        status_code: HTTP status code returned by the API, or ``None`` for
            connection-level failures.
        response_body: Truncated response text when available.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class IngramSparkClient:
    """Async HTTP client for the IngramSpark publisher REST API.

    Authentication uses HMAC-SHA256 request signing: the API key and a
    current Unix timestamp are concatenated and signed with the API secret.
    The resulting signature, key, and timestamp are sent as custom headers
    on every request.

    All public methods implement automatic retry with exponential backoff
    (up to ``_MAX_RETRIES`` attempts).

    Args:
        api_key: IngramSpark publisher API key.
        api_secret: IngramSpark publisher API secret.
        base_url: Base URL for the IngramSpark API (without trailing slash).
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.ingramspark.com/v1",
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")

    # -- Authentication helpers --------------------------------------------

    def _build_auth_headers(self) -> dict[str, str]:
        """Build HMAC-SHA256 authentication headers for a request.

        The signing scheme concatenates ``api_key + unix_timestamp`` and
        signs the result with the API secret using HMAC-SHA256.

        Returns:
            A dict of HTTP headers including the Authorization bearer
            token, the API key, the computed signature, and the timestamp.
        """
        timestamp = str(int(time.time()))
        message = f"{self._api_key}{timestamp}"
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return {
            "Authorization": f"Bearer {self._api_key}",
            "X-IngramSpark-Key": self._api_key,
            "X-IngramSpark-Signature": signature,
            "X-IngramSpark-Timestamp": timestamp,
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        }

    # -- Core HTTP caller with retry ---------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Execute an authenticated HTTP request with exponential-backoff retry.

        Retries up to ``_MAX_RETRIES`` times on retriable HTTP status codes
        (429, 5xx) and transient connection errors.

        Args:
            method: HTTP method (``"GET"``, ``"POST"``, etc.).
            path: URL path appended to ``base_url`` (e.g. ``"/compensation/reports"``).
            params: Optional query-string parameters.
            json_body: Optional JSON body for POST/PUT requests.

        Returns:
            Parsed JSON response (dict or list).

        Raises:
            IngramSparkError: On non-retriable HTTP errors or after all
                retry attempts are exhausted.
        """
        url = f"{self._base_url}{path}"
        last_exc: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            headers = self._build_auth_headers()

            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(_DEFAULT_TIMEOUT),
                ) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=headers,
                        params=params,
                        json=json_body,
                    )

                if response.status_code == 200:
                    return response.json()  # type: ignore[no-any-return]

                body_preview = response.text[:500]

                if response.status_code in _RETRIABLE_STATUS_CODES:
                    logger.warning(
                        "IngramSpark API %s %s returned %d on attempt %d/%d: %s",
                        method,
                        path,
                        response.status_code,
                        attempt + 1,
                        _MAX_RETRIES,
                        body_preview,
                    )
                    last_exc = IngramSparkError(
                        f"HTTP {response.status_code}",
                        status_code=response.status_code,
                        response_body=body_preview,
                    )
                else:
                    # Non-retriable client error (400, 401, 403, etc.).
                    logger.error(
                        "IngramSpark API %s %s returned non-retriable status %d: %s",
                        method,
                        path,
                        response.status_code,
                        body_preview,
                    )
                    raise IngramSparkError(
                        f"IngramSpark API returned HTTP {response.status_code}",
                        status_code=response.status_code,
                        response_body=body_preview,
                    )

            except httpx.TimeoutException as exc:
                logger.warning(
                    "IngramSpark API %s %s timed out on attempt %d/%d: %s",
                    method,
                    path,
                    attempt + 1,
                    _MAX_RETRIES,
                    exc,
                )
                last_exc = exc

            except httpx.RequestError as exc:
                logger.warning(
                    "IngramSpark API %s %s connection error on attempt %d/%d: %s",
                    method,
                    path,
                    attempt + 1,
                    _MAX_RETRIES,
                    exc,
                )
                last_exc = exc

            # Exponential backoff: 1s, 2s, 4s ...
            if attempt < _MAX_RETRIES - 1:
                backoff = 2**attempt
                logger.debug("Retrying IngramSpark API request in %ds ...", backoff)
                await asyncio.sleep(backoff)

        # All retries exhausted.
        msg = f"IngramSpark API {method} {path} failed after {_MAX_RETRIES} " f"attempts. Last error: {last_exc}"
        logger.error(msg)
        raise IngramSparkError(msg)

    # -- Response normalisation helpers ------------------------------------

    @staticmethod
    def _normalise_royalty_record(
        entry: dict[str, Any],
        period_start: date,
        period_end: date,
    ) -> dict[str, Any]:
        """Convert a single IngramSpark compensation entry to the internal format.

        The internal royalty-record format matches what ``royalty_records``
        expects for upsert (fields such as ``platform``, ``marketplace``,
        ``title``, ``isbn``, ``units_sold``, ``net_revenue``, etc.).

        Args:
            entry: Raw JSON dict from the IngramSpark API response.
            period_start: Start date of the reporting period.
            period_end: End date of the reporting period.

        Returns:
            A normalised royalty-record dict.

        Raises:
            ValueError: If required numeric fields cannot be parsed.
        """
        title = entry.get("title") or entry.get("bookTitle", "Unknown")
        isbn = entry.get("isbn") or entry.get("isbn13")
        marketplace = entry.get("marketplace", "US")
        currency = entry.get("currency", "USD")

        units = int(entry.get("units", 0) or entry.get("quantitySold", 0))
        units_refunded = int(entry.get("unitsRefunded", 0))

        royalties = Decimal(str(entry.get("royalties", 0) or entry.get("netRevenue", 0)))
        gross = Decimal(str(entry.get("grossRevenue", 0) or entry.get("grossAmount", royalties)))
        list_price = Decimal(str(entry.get("listPrice", 0) or entry.get("retailPrice", 0)))
        royalty_rate = Decimal(str(entry.get("royaltyRate", "0.00")))

        fmt = (entry.get("format", "paperback") or "paperback").lower()
        if fmt not in ("ebook", "paperback", "hardcover", "audiobook"):
            fmt = "paperback"

        return {
            "platform": "ingram_spark",
            "marketplace": marketplace,
            "title": title,
            "isbn": isbn,
            "format_type": fmt,
            "units_sold": max(units, 0),
            "units_refunded": units_refunded,
            "net_units": units - units_refunded,
            "list_price": list_price,
            "royalty_rate": royalty_rate,
            "gross_revenue": gross,
            "net_revenue": royalties,
            "currency": currency,
            "period_start": period_start,
            "period_end": period_end,
            "raw_data": entry,
        }

    @staticmethod
    def _extract_report_items(
        data: dict[str, Any] | list[Any],
    ) -> list[dict[str, Any]]:
        """Extract the list of report entries from the API response.

        The IngramSpark API may return a top-level list or a dict with
        a ``reports`` or ``compensations`` key.

        Args:
            data: Parsed JSON response from the API.

        Returns:
            A list of raw compensation/report entry dicts.
        """
        if isinstance(data, list):
            return data
        return cast("list[dict[str, Any]]", data.get("reports", data.get("compensations", [])))

    # -- Public interface --------------------------------------------------

    async def fetch_royalties(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """Fetch royalty/compensation records for the given date range.

        Makes an authenticated GET request to the IngramSpark compensation
        reports endpoint, parses the response, and returns a list of
        normalised royalty-record dicts ready for database upsert.

        Args:
            start_date: Inclusive start date of the reporting period.
            end_date: Inclusive end date of the reporting period.

        Returns:
            A list of normalised royalty-record dicts. Each dict contains
            keys such as ``platform``, ``title``, ``isbn``, ``units_sold``,
            ``net_revenue``, ``currency``, and ``marketplace``.

        Raises:
            IngramSparkError: On API communication failures.
        """
        params: dict[str, str] = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }

        logger.info(
            "Fetching IngramSpark royalties for period %s to %s",
            params["startDate"],
            params["endDate"],
        )

        data = await self._request("GET", "/compensation/reports", params=params)
        report_items = self._extract_report_items(data)

        if not report_items:
            logger.info("IngramSpark API returned no compensation items.")
            return []

        records: list[dict[str, Any]] = []
        for entry in report_items:
            try:
                record = self._normalise_royalty_record(entry, start_date, end_date)
                records.append(record)
            except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
                logger.warning(
                    "Skipping unparseable IngramSpark compensation entry: %s",
                    exc,
                )

        logger.info(
            "Parsed %d compensation records from IngramSpark API " "(%d raw items).",
            len(records),
            len(report_items),
        )
        return records

    async def fetch_sales_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Fetch aggregated sales data for the given date range.

        Calls the IngramSpark sales summary endpoint and returns a dict
        containing high-level aggregates (total units, total revenue,
        breakdown by marketplace, etc.).

        If the API returns individual report items instead of a pre-
        aggregated summary, the method aggregates them client-side.

        Args:
            start_date: Inclusive start date of the reporting period.
            end_date: Inclusive end date of the reporting period.

        Returns:
            A dict with keys ``total_units``, ``total_revenue``,
            ``currency``, ``period_start``, ``period_end``, and
            ``by_marketplace`` (a dict mapping marketplace codes to
            per-marketplace totals).

        Raises:
            IngramSparkError: On API communication failures.
        """
        params: dict[str, str] = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }

        logger.info(
            "Fetching IngramSpark sales summary for period %s to %s",
            params["startDate"],
            params["endDate"],
        )

        try:
            data = await self._request("GET", "/sales/summary", params=params)
        except IngramSparkError:
            # If the dedicated summary endpoint is unavailable, fall back
            # to aggregating the compensation report data.
            logger.info("Sales summary endpoint unavailable; falling back to " "compensation report aggregation.")
            data = await self._request("GET", "/compensation/reports", params=params)

        # If the response already contains aggregated fields, return them
        # directly after normalisation.
        if isinstance(data, dict) and "totalUnits" in data:
            return {
                "total_units": int(data.get("totalUnits", 0)),
                "total_revenue": str(Decimal(str(data.get("totalRevenue", 0)))),
                "currency": data.get("currency", "USD"),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "by_marketplace": data.get("byMarketplace", {}),
            }

        # Otherwise, aggregate from individual report items.
        report_items = self._extract_report_items(data)
        total_units = 0
        total_revenue = Decimal("0")
        by_marketplace: dict[str, dict[str, Any]] = {}

        for entry in report_items:
            try:
                units = int(entry.get("units", 0) or entry.get("quantitySold", 0))
                revenue = Decimal(str(entry.get("royalties", 0) or entry.get("netRevenue", 0)))
                marketplace = entry.get("marketplace", "US")

                total_units += units
                total_revenue += revenue

                if marketplace not in by_marketplace:
                    by_marketplace[marketplace] = {
                        "units": 0,
                        "revenue": Decimal("0"),
                    }
                by_marketplace[marketplace]["units"] += units
                by_marketplace[marketplace]["revenue"] += revenue
            except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
                logger.warning("Skipping entry during sales summary aggregation: %s", exc)

        # Convert Decimal values to strings for JSON serialisability.
        serialisable_marketplaces: dict[str, dict[str, Any]] = {}
        for mkt, vals in by_marketplace.items():
            serialisable_marketplaces[mkt] = {
                "units": vals["units"],
                "revenue": str(vals["revenue"]),
            }

        return {
            "total_units": total_units,
            "total_revenue": str(total_revenue),
            "currency": "USD",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "by_marketplace": serialisable_marketplaces,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_ingram_client() -> IngramSparkClient | None:
    """Return an ``IngramSparkClient`` if credentials are configured, else ``None``.

    Reads the following environment variables:

    * ``INGRAM_SPARK_API_KEY``    -- Publisher API key (required)
    * ``INGRAM_SPARK_API_SECRET`` -- Publisher API secret (required)
    * ``INGRAM_SPARK_API_URL``    -- Optional base URL override

    Returns:
        An ``IngramSparkClient`` instance ready for use, or ``None`` when
        credentials are missing so callers can gracefully skip IngramSpark
        integration.
    """
    api_key = os.environ.get("INGRAM_SPARK_API_KEY", "")
    api_secret = os.environ.get("INGRAM_SPARK_API_SECRET", "")

    if not api_key or not api_secret:
        logger.info(
            "IngramSpark credentials not configured "
            "(INGRAM_SPARK_API_KEY / INGRAM_SPARK_API_SECRET). "
            "Returning None; IngramSpark integration will be skipped."
        )
        return None

    base_url = os.environ.get(
        "INGRAM_SPARK_API_URL",
        "https://api.ingramspark.com/v1",
    )

    logger.info(
        "IngramSpark credentials found. Creating client (base_url=%s).",
        base_url,
    )
    return IngramSparkClient(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url,
    )
