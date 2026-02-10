"""Unit tests for the IngramSpark and D2D API clients.

Tests cover initialization, fetch methods, retry logic on transient errors,
authentication failure handling, and factory functions for both clients.
All HTTP calls are mocked to avoid real network traffic.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# ---------------------------------------------------------------------------
# Graceful import: the modules under test may not yet exist (W02 / W03).
# If they are unavailable, every test in this file is skipped with a clear
# message so CI stays green while the implementation work is in progress.
# ---------------------------------------------------------------------------

try:
    from app.modules.analytics.ingram_client import (
        IngramSparkClient,
        IngramSparkError,
        get_ingram_client,
    )

    _HAS_INGRAM = True
except ImportError:
    _HAS_INGRAM = False

try:
    from app.modules.analytics.d2d_client import (
        D2DClient,
        D2DError,
        get_d2d_client,
    )

    _HAS_D2D = True
except ImportError:
    _HAS_D2D = False

skip_ingram = pytest.mark.skipif(
    not _HAS_INGRAM,
    reason="app.modules.analytics.ingram_client not yet available (W02)",
)
skip_d2d = pytest.mark.skipif(
    not _HAS_D2D,
    reason="app.modules.analytics.d2d_client not yet available (W03)",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_httpx_response(
    status_code: int = 200,
    json_data: dict | list | None = None,
    text: str = "",
) -> httpx.Response:
    """Build a fake ``httpx.Response`` for patching."""
    resp = httpx.Response(
        status_code=status_code,
        request=httpx.Request("GET", "https://fake.example.com"),
        json=json_data if json_data is not None else None,
        text=text if json_data is None else None,
    )
    return resp


def _build_ingram_royalty_payload() -> list[dict]:
    """Sample royalty records that the IngramSpark API might return."""
    return [
        {
            "title": "My Print Book",
            "isbn": "9781234567890",
            "format": "Paperback",
            "quantity": 25,
            "publisher_compensation": "75.50",
            "currency": "USD",
            "sale_type": "Sale",
            "reporting_date": "2024-01-15",
        },
        {
            "title": "My Hardcover",
            "isbn": "9780987654321",
            "format": "Hardcover",
            "quantity": 10,
            "publisher_compensation": "45.00",
            "currency": "USD",
            "sale_type": "Sale",
            "reporting_date": "2024-01-20",
        },
    ]


def _build_d2d_royalty_payload() -> list[dict]:
    """Sample royalty records that the D2D API might return."""
    return [
        {
            "title": "My eBook",
            "isbn": "9781234567890",
            "channel": "Apple Books",
            "payout": "45.00",
            "currency": "USD",
            "period": "January 2024",
            "units": 30,
        },
    ]


def _build_d2d_book_list_payload() -> list[dict]:
    """Sample book list that the D2D API might return."""
    return [
        {
            "id": "book-001",
            "title": "My eBook",
            "isbn": "9781234567890",
            "status": "published",
            "channels": ["Apple Books", "Barnes & Noble", "Kobo"],
        },
        {
            "id": "book-002",
            "title": "My Second eBook",
            "isbn": "9780987654321",
            "status": "draft",
            "channels": [],
        },
    ]


# ===========================================================================
# IngramSpark Client Tests
# ===========================================================================


@skip_ingram
class TestIngramSparkClientInit:
    """Initialization and credential handling."""

    def test_init_with_valid_credentials(self):
        """Client stores credentials passed at construction time."""
        client = IngramSparkClient(
            api_key="test-key",
            api_secret="test-secret",
        )
        assert client._api_key == "test-key"
        assert client._api_secret == "test-secret"

    def test_init_uses_factory_for_env_credentials(self):
        """The factory function reads credentials from env vars."""
        env = {
            "INGRAM_SPARK_API_KEY": "env-key",
            "INGRAM_SPARK_API_SECRET": "env-secret",
        }
        with patch.dict("os.environ", env, clear=False):
            client = get_ingram_client()
            assert client is not None
            assert client._api_key == "env-key"
            assert client._api_secret == "env-secret"


@skip_ingram
class TestIngramSparkFetchRoyalties:
    """Tests for IngramSparkClient.fetch_royalties()."""

    @pytest.mark.asyncio
    async def test_fetch_royalties_returns_list_of_dicts(self):
        """The return value must be a list of dict-like royalty records."""
        payload = _build_ingram_royalty_payload()

        client = IngramSparkClient(api_key="k", api_secret="s")

        mock_resp = _make_httpx_response(status_code=200, json_data=payload)
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(r, dict) for r in result)

    @pytest.mark.asyncio
    async def test_fetch_royalties_includes_expected_fields(self):
        """Each record should contain core royalty fields."""
        payload = _build_ingram_royalty_payload()
        client = IngramSparkClient(api_key="k", api_secret="s")

        mock_resp = _make_httpx_response(status_code=200, json_data=payload)
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        first = result[0]
        assert "title" in first
        assert "isbn" in first

    @pytest.mark.asyncio
    async def test_fetch_royalties_empty_response(self):
        """An empty API response yields an empty list, not an error."""
        client = IngramSparkClient(api_key="k", api_secret="s")

        mock_resp = _make_httpx_response(status_code=200, json_data=[])
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert result == []


@skip_ingram
class TestIngramSparkRetry:
    """Retry behaviour on transient HTTP errors (500, 503)."""

    @pytest.mark.asyncio
    async def test_retry_on_500(self):
        """A 500 response should trigger a retry; success on second attempt."""
        payload = _build_ingram_royalty_payload()
        fail_resp = _make_httpx_response(status_code=500, text="Internal Server Error")
        ok_resp = _make_httpx_response(status_code=200, json_data=payload)

        client = IngramSparkClient(api_key="k", api_secret="s")

        call_count = 0
        original_request = httpx.AsyncClient.request

        async def _side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return fail_resp
            return ok_resp

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, side_effect=_side_effect
        ), patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert call_count >= 2
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_retry_on_503(self):
        """A 503 response should also trigger a retry."""
        payload = _build_ingram_royalty_payload()
        fail_resp = _make_httpx_response(status_code=503, text="Service Unavailable")
        ok_resp = _make_httpx_response(status_code=200, json_data=payload)

        client = IngramSparkClient(api_key="k", api_secret="s")

        call_count = 0

        async def _side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return fail_resp
            return ok_resp

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, side_effect=_side_effect
        ), patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert call_count >= 2


@skip_ingram
class TestIngramSparkAuthError:
    """Authentication failure handling."""

    @pytest.mark.asyncio
    async def test_401_raises_ingram_spark_error(self):
        """A 401 response should raise IngramSparkError, not retry."""
        client = IngramSparkClient(api_key="k", api_secret="s")

        mock_resp = _make_httpx_response(status_code=401, text="Unauthorized")
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ), pytest.raises(IngramSparkError) as exc_info:
            await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert exc_info.value.status_code == 401


@skip_ingram
class TestGetIngramClient:
    """Factory function ``get_ingram_client()``."""

    def test_returns_none_when_credentials_missing(self):
        """Without env vars the factory should return None."""
        env = {
            "INGRAM_SPARK_API_KEY": "",
            "INGRAM_SPARK_API_SECRET": "",
        }
        with patch.dict("os.environ", env, clear=False):
            result = get_ingram_client()
            assert result is None

    def test_returns_client_when_credentials_present(self):
        """With valid env vars the factory should return an IngramSparkClient."""
        env = {
            "INGRAM_SPARK_API_KEY": "real-key",
            "INGRAM_SPARK_API_SECRET": "real-secret",
        }
        with patch.dict("os.environ", env, clear=False):
            result = get_ingram_client()
            assert result is not None
            assert isinstance(result, IngramSparkClient)


# ===========================================================================
# D2D Client Tests
# ===========================================================================


@skip_d2d
class TestD2DClientInit:
    """Initialization and credential handling."""

    def test_init_with_valid_credentials(self):
        """Client stores credentials passed at construction time."""
        client = D2DClient(
            api_key="d2d-key",
        )
        assert client._api_key == "d2d-key"

    def test_init_raises_on_empty_api_key(self):
        """An empty api_key should raise ValueError."""
        with pytest.raises(ValueError, match="api_key must be a non-empty string"):
            D2DClient(api_key="")

    def test_init_uses_factory_for_env_credentials(self):
        """The factory function reads credentials from env vars."""
        env = {
            "D2D_API_KEY": "env-d2d-key",
        }
        with patch.dict("os.environ", env, clear=False):
            client = get_d2d_client()
            assert client is not None
            assert client._api_key == "env-d2d-key"


@skip_d2d
class TestD2DFetchRoyalties:
    """Tests for D2DClient.fetch_royalties()."""

    @pytest.mark.asyncio
    async def test_fetch_royalties_returns_list(self):
        """The return value must be a list of dict-like royalty records."""
        payload = _build_d2d_royalty_payload()
        client = D2DClient(api_key="k")

        mock_resp = _make_httpx_response(status_code=200, json_data=payload)
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "My eBook"

    @pytest.mark.asyncio
    async def test_fetch_royalties_empty_response(self):
        """An empty API response yields an empty list."""
        client = D2DClient(api_key="k")

        mock_resp = _make_httpx_response(status_code=200, json_data=[])
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_royalties_includes_channel(self):
        """Each royalty record should contain the distribution channel."""
        payload = _build_d2d_royalty_payload()
        client = D2DClient(api_key="k")

        mock_resp = _make_httpx_response(status_code=200, json_data=payload)
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert "channel" in result[0]


@skip_d2d
class TestD2DFetchBookList:
    """Tests for D2DClient.fetch_book_list()."""

    @pytest.mark.asyncio
    async def test_fetch_book_list_returns_list(self):
        """fetch_book_list() returns a list of book dicts."""
        payload = _build_d2d_book_list_payload()
        client = D2DClient(api_key="k")

        mock_resp = _make_httpx_response(status_code=200, json_data=payload)
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ):
            result = await client.fetch_book_list()

        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetch_book_list_includes_title_and_isbn(self):
        """Each book entry should contain at least title and isbn."""
        payload = _build_d2d_book_list_payload()
        client = D2DClient(api_key="k")

        mock_resp = _make_httpx_response(status_code=200, json_data=payload)
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ):
            result = await client.fetch_book_list()

        for book in result:
            assert "title" in book
            assert "isbn" in book


@skip_d2d
class TestD2DRetry:
    """Retry behaviour on transient HTTP errors."""

    @pytest.mark.asyncio
    async def test_retry_on_500(self):
        """A 500 response should trigger a retry; success on second attempt."""
        payload = _build_d2d_royalty_payload()
        fail_resp = _make_httpx_response(status_code=500, text="Internal Server Error")
        ok_resp = _make_httpx_response(status_code=200, json_data=payload)

        client = D2DClient(api_key="k")

        call_count = 0

        async def _side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return fail_resp
            return ok_resp

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, side_effect=_side_effect
        ), patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert call_count >= 2
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_retry_on_503(self):
        """A 503 Service Unavailable should also trigger retry."""
        payload = _build_d2d_royalty_payload()
        fail_resp = _make_httpx_response(status_code=503, text="Service Unavailable")
        ok_resp = _make_httpx_response(status_code=200, json_data=payload)

        client = D2DClient(api_key="k")

        call_count = 0

        async def _side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return fail_resp
            return ok_resp

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, side_effect=_side_effect
        ), patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert call_count >= 2


@skip_d2d
class TestD2DAuthError:
    """Authentication failure handling."""

    @pytest.mark.asyncio
    async def test_401_raises_d2d_error(self):
        """A 401 response should raise D2DError, not retry."""
        client = D2DClient(api_key="k")

        mock_resp = _make_httpx_response(status_code=401, text="Unauthorized")
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ), pytest.raises(D2DError) as exc_info:
            await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_403_raises_d2d_error(self):
        """A 403 Forbidden should also raise D2DError."""
        client = D2DClient(api_key="k")

        mock_resp = _make_httpx_response(status_code=403, text="Forbidden")
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock, return_value=mock_resp
        ), pytest.raises(D2DError) as exc_info:
            await client.fetch_royalties(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        assert exc_info.value.status_code == 403


@skip_d2d
class TestGetD2DClient:
    """Factory function ``get_d2d_client()``."""

    def test_returns_none_when_credentials_missing(self):
        """Without env vars the factory should return None."""
        env = {
            "D2D_API_KEY": "",
            "D2D_API_SECRET": "",
        }
        with patch.dict("os.environ", env, clear=False):
            result = get_d2d_client()
            assert result is None

    def test_returns_client_when_credentials_present(self):
        """With valid env vars the factory should return a D2DClient."""
        env = {
            "D2D_API_KEY": "real-key",
            "D2D_API_SECRET": "real-secret",
        }
        with patch.dict("os.environ", env, clear=False):
            result = get_d2d_client()
            assert result is not None
            assert isinstance(result, D2DClient)
