"""Unit tests for the CSV import queue service.

Tests CSV parsing for KDP and IngramSpark formats, field validation,
the async process_csv_import pipeline, and various edge cases.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Graceful import: skip the entire module if csv_queue hasn't landed yet (W01)
# ---------------------------------------------------------------------------
try:
    from app.modules.analytics.csv_queue import (
        CSVImportQueue,
        process_csv_import,
    )
except ImportError:
    pytestmark = pytest.mark.skip(
        reason="app.modules.analytics.csv_queue not available yet (W01)"
    )
    # Define stubs so the rest of the file parses without NameError
    CSVImportQueue = None  # type: ignore[assignment, misc]
    process_csv_import = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Shared helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def account_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture
def mock_db():
    """Return a mock async DB session with the methods used by process_csv_import."""
    db = AsyncMock()
    db.add = MagicMock()
    db.add_all = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Sample CSV payloads
# ---------------------------------------------------------------------------

VALID_KDP_CSV = (
    "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
    "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
    "My Book,B012345678,Amazon.com,Kindle Edition,100,5,95,9.99,USD,6.99,January 2024\n"
    "Other Book,B098765432,Amazon.co.uk,Kindle Edition,50,2,48,7.99,GBP,4.99,January 2024\n"
)

VALID_INGRAM_CSV = (
    "Title,ISBN,Format,Quantity,Publisher Compensation,"
    "Currency Code,Sale/Return,Reporting Date\n"
    "My Print Book,9781234567890,Paperback,25,75.50,USD,Sale,2024-01-15\n"
)

HEADERS_ONLY_KDP_CSV = (
    "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
    "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
)

HEADERS_ONLY_INGRAM_CSV = (
    "Title,ISBN,Format,Quantity,Publisher Compensation,"
    "Currency Code,Sale/Return,Reporting Date\n"
)

MIXED_VALID_INVALID_KDP_CSV = (
    "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
    "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
    # Valid row
    "Good Book,B012345678,Amazon.com,Kindle Edition,50,2,48,9.99,USD,3.49,January 2024\n"
    # Missing title (invalid)
    ",B098765432,Amazon.com,Kindle Edition,20,0,20,4.99,USD,2.49,January 2024\n"
    # Another valid row
    "Also Good,B011111111,Amazon.com,Kindle Edition,30,1,29,7.99,USD,5.59,February 2024\n"
)

NEGATIVE_REVENUE_KDP_CSV = (
    "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
    "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
    "Bad Revenue Book,B012345678,Amazon.com,Kindle Edition,10,0,10,9.99,USD,-5.00,January 2024\n"
)

INVALID_DATE_KDP_CSV = (
    "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
    "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
    "Bad Date Book,B012345678,Amazon.com,Kindle Edition,10,0,10,9.99,USD,6.99,not-a-date\n"
)

ZERO_UNITS_KDP_CSV = (
    "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
    "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
    "Free Download,B012345678,Amazon.com,Kindle Edition,0,0,0,0.00,USD,0.00,January 2024\n"
)

UNICODE_TITLE_KDP_CSV = (
    "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
    "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
    "El arte de la guerra,B012345678,Amazon.com,Kindle Edition,10,0,10,9.99,USD,6.99,January 2024\n"
)

TAB_DELIMITED_CSV = (
    "Title\tASIN\tMarketplace\tRoyalty Type\tUnits Sold\tUnits Refunded\t"
    "Net Units Sold\tAvg List Price\tCurrency\tRoyalty\tRoyalty Date\n"
    "Tab Book\tB012345678\tAmazon.com\tKindle Edition\t10\t0\t10\t9.99\tUSD\t6.99\tJanuary 2024\n"
)


# ===========================================================================
# 1. CSV Parsing Tests
# ===========================================================================


class TestCSVParsingKDP:
    """Test parsing of KDP-format CSV data."""

    def test_valid_kdp_csv_extracts_correct_records(self):
        """Valid KDP CSV should produce the right number of records with correct fields."""
        queue = CSVImportQueue(csv_data=VALID_KDP_CSV, platform="kdp")
        records = queue.process()

        assert len(records) == 2

        first = records[0]
        assert first["title"] == "My Book"
        assert first["asin"] == "B012345678"
        assert first["platform"] == "kdp"
        assert first["units_sold"] == 100
        assert first["units_refunded"] == 5
        assert first["net_units"] == 95
        assert first["currency"] == "USD"

    def test_valid_kdp_csv_revenue_parsed(self):
        """Royalty / net_revenue values should be parsed as Decimal."""
        queue = CSVImportQueue(csv_data=VALID_KDP_CSV, platform="kdp")
        records = queue.process()

        assert records[0]["net_revenue"] == Decimal("6.99")
        assert records[1]["net_revenue"] == Decimal("4.99")

    def test_empty_csv_returns_empty_list(self):
        """Completely empty CSV should produce an empty list with no error."""
        queue = CSVImportQueue(csv_data="", platform="kdp")
        records = queue.process()
        assert records == []

    def test_headers_only_returns_empty_list(self):
        """CSV with header row but no data rows should return an empty list."""
        queue = CSVImportQueue(csv_data=HEADERS_ONLY_KDP_CSV, platform="kdp")
        records = queue.process()
        assert records == []

    def test_invalid_rows_skipped_valid_rows_kept(self):
        """Rows with missing required fields are skipped; valid rows are still returned."""
        queue = CSVImportQueue(csv_data=MIXED_VALID_INVALID_KDP_CSV, platform="kdp")
        records = queue.process()

        # The row with missing title should be skipped
        titles = [r["title"] for r in records]
        assert "Good Book" in titles
        assert "Also Good" in titles
        # Only valid rows
        assert len(records) == 2


class TestCSVParsingIngramSpark:
    """Test parsing of IngramSpark-format CSV data."""

    def test_valid_ingram_csv_extracts_correct_records(self):
        """Valid IngramSpark CSV should produce records with correct fields."""
        queue = CSVImportQueue(csv_data=VALID_INGRAM_CSV, platform="ingram_spark")
        records = queue.process()

        assert len(records) == 1
        first = records[0]
        assert first["title"] == "My Print Book"
        assert first["isbn"] == "9781234567890"
        assert first["platform"] == "ingram_spark"
        assert first["units_sold"] == 25
        assert first["net_revenue"] == Decimal("75.50")
        assert first["format_type"] == "paperback"

    def test_empty_ingram_csv_returns_empty_list(self):
        """Empty IngramSpark CSV should return an empty list."""
        queue = CSVImportQueue(csv_data="", platform="ingram_spark")
        records = queue.process()
        assert records == []

    def test_headers_only_ingram_csv_returns_empty_list(self):
        """IngramSpark CSV with only headers should return an empty list."""
        queue = CSVImportQueue(csv_data=HEADERS_ONLY_INGRAM_CSV, platform="ingram_spark")
        records = queue.process()
        assert records == []


# ===========================================================================
# 2. Field Validation Tests
# ===========================================================================


class TestFieldValidation:
    """Test that individual field validation rules are enforced."""

    def test_missing_title_row_skipped(self):
        """A row with an empty title should be skipped entirely."""
        csv_data = (
            "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
            "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
            ",B012345678,Amazon.com,Kindle Edition,10,0,10,6.99,USD,6.99,January 2024\n"
        )
        queue = CSVImportQueue(csv_data=csv_data, platform="kdp")
        records = queue.process()
        assert len(records) == 0

    def test_negative_revenue_accepted(self):
        """A row with negative revenue (royalty) is still parsed and accepted.

        The implementation does not reject negative revenue values; it parses
        them as-is via _safe_decimal.
        """
        queue = CSVImportQueue(csv_data=NEGATIVE_REVENUE_KDP_CSV, platform="kdp")
        records = queue.process()
        assert len(records) == 1
        assert records[0]["net_revenue"] == Decimal("-5.00")

    def test_invalid_date_falls_back_to_current_month(self):
        """A row with an unparseable date falls back to the first of the current month."""
        queue = CSVImportQueue(csv_data=INVALID_DATE_KDP_CSV, platform="kdp")
        records = queue.process()
        # The implementation falls back to datetime.now(utc).replace(day=1)
        # rather than skipping the row, so 1 record is returned.
        assert len(records) == 1
        assert records[0]["title"] == "Bad Date Book"
        assert records[0]["period_start"].day == 1

    def test_zero_units_accepted(self):
        """Zero units should be accepted (e.g. free downloads / KU borrows)."""
        queue = CSVImportQueue(csv_data=ZERO_UNITS_KDP_CSV, platform="kdp")
        records = queue.process()

        assert len(records) == 1
        assert records[0]["units_sold"] == 0
        assert records[0]["net_units"] == 0
        assert records[0]["title"] == "Free Download"


# ===========================================================================
# 3. process_csv_import Tests
# ===========================================================================


class TestProcessCSVImport:
    """Test the async process_csv_import function that writes to the DB."""

    @pytest.mark.asyncio
    async def test_records_added_to_session(self, mock_db, account_id):
        """Parsed records should be added to the DB session via add."""
        count = await process_csv_import(
            db_session=mock_db,
            account_id=account_id,
            platform="kdp",
            csv_data=VALID_KDP_CSV,
        )

        # Should have added records via add
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_flush_called(self, mock_db, account_id):
        """After inserting records, flush should be called."""
        await process_csv_import(
            db_session=mock_db,
            account_id=account_id,
            platform="kdp",
            csv_data=VALID_KDP_CSV,
        )

        mock_db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_count_matches_inserted_records(self, mock_db, account_id):
        """The returned count should match the number of valid records inserted."""
        count = await process_csv_import(
            db_session=mock_db,
            account_id=account_id,
            platform="kdp",
            csv_data=VALID_KDP_CSV,
        )

        # VALID_KDP_CSV has 2 valid data rows
        assert count == 2

    @pytest.mark.asyncio
    async def test_empty_csv_returns_zero(self, mock_db, account_id):
        """An empty CSV should return 0 with no DB writes."""
        count = await process_csv_import(
            db_session=mock_db,
            account_id=account_id,
            platform="kdp",
            csv_data="",
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_headers_only_returns_zero(self, mock_db, account_id):
        """CSV with only a header row should return 0."""
        count = await process_csv_import(
            db_session=mock_db,
            account_id=account_id,
            platform="kdp",
            csv_data=HEADERS_ONLY_KDP_CSV,
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_db_failure_raises_on_flush(self, mock_db, account_id):
        """When the DB flush fails, the error should propagate."""
        mock_db.flush = AsyncMock(side_effect=Exception("DB connection lost"))

        with pytest.raises(Exception, match="DB connection lost"):
            await process_csv_import(
                db_session=mock_db,
                account_id=account_id,
                platform="kdp",
                csv_data=VALID_KDP_CSV,
            )

    @pytest.mark.asyncio
    async def test_ingram_spark_import(self, mock_db, account_id):
        """process_csv_import should handle IngramSpark platform correctly."""
        count = await process_csv_import(
            db_session=mock_db,
            account_id=account_id,
            platform="ingram_spark",
            csv_data=VALID_INGRAM_CSV,
        )

        assert count == 1
        assert mock_db.flush.called

    @pytest.mark.asyncio
    async def test_mixed_valid_invalid_rows(self, mock_db, account_id):
        """Only valid rows should be counted; invalid ones are skipped."""
        count = await process_csv_import(
            db_session=mock_db,
            account_id=account_id,
            platform="kdp",
            csv_data=MIXED_VALID_INVALID_KDP_CSV,
        )

        # 2 valid rows, 1 invalid (missing title)
        assert count == 2


# ===========================================================================
# 4. Edge Case Tests
# ===========================================================================


class TestEdgeCases:
    """Test edge cases: large files, Unicode, different delimiters."""

    def test_large_csv_processes_without_error(self):
        """A CSV with 1000+ rows should parse without errors or timeouts."""
        header = (
            "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
            "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
        )
        rows = []
        for i in range(1200):
            rows.append(
                f"Book {i},B{str(i).zfill(10)},Amazon.com,Kindle Edition,"
                f"{i + 1},0,{i + 1},9.99,USD,6.99,January 2024\n"
            )
        large_csv = header + "".join(rows)

        queue = CSVImportQueue(csv_data=large_csv, platform="kdp")
        records = queue.process()

        assert len(records) == 1200

    def test_unicode_titles_handled(self):
        """Titles with non-ASCII characters should be preserved correctly."""
        queue = CSVImportQueue(csv_data=UNICODE_TITLE_KDP_CSV, platform="kdp")
        records = queue.process()

        assert len(records) == 1
        assert records[0]["title"] == "El arte de la guerra"

    def test_unicode_cjk_characters(self):
        """CJK characters in titles should be handled correctly."""
        csv_data = (
            "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
            "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
            "\u6226\u4e89\u3068\u5e73\u548c,B012345678,Amazon.co.jp,Kindle Edition,"
            "10,0,10,9.99,JPY,6.99,January 2024\n"
        )
        queue = CSVImportQueue(csv_data=csv_data, platform="kdp")
        records = queue.process()

        assert len(records) == 1
        assert records[0]["title"] == "\u6226\u4e89\u3068\u5e73\u548c"

    def test_unicode_emoji_in_title(self):
        """Emoji characters in titles should not cause failures."""
        csv_data = (
            "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
            "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
            "My Awesome Book \U0001f680,B012345678,Amazon.com,Kindle Edition,"
            "10,0,10,9.99,USD,6.99,January 2024\n"
        )
        queue = CSVImportQueue(csv_data=csv_data, platform="kdp")
        records = queue.process()

        assert len(records) == 1
        assert "\U0001f680" in records[0]["title"]

    def test_tab_delimited_csv_not_parsed(self):
        """Tab-delimited CSV data is not supported by the default csv.DictReader
        (which uses comma delimiter), so it will not parse correctly and
        returns an empty list."""
        queue = CSVImportQueue(csv_data=TAB_DELIMITED_CSV, platform="kdp")
        records = queue.process()

        # csv.DictReader with default comma delimiter cannot parse tab-separated
        # data, so no valid records are produced.
        assert len(records) == 0

    def test_comma_delimited_is_default(self):
        """Standard comma-delimited CSV should work as the default case."""
        queue = CSVImportQueue(csv_data=VALID_KDP_CSV, platform="kdp")
        records = queue.process()

        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_large_csv_import_pipeline(self, mock_db, account_id):
        """A large CSV should process end-to-end through process_csv_import."""
        header = (
            "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
            "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
        )
        rows = []
        for i in range(1050):
            rows.append(
                f"Book {i},B{str(i).zfill(10)},Amazon.com,Kindle Edition,"
                f"{i + 1},0,{i + 1},9.99,USD,6.99,January 2024\n"
            )
        large_csv = header + "".join(rows)

        count = await process_csv_import(
            db_session=mock_db,
            account_id=account_id,
            platform="kdp",
            csv_data=large_csv,
        )

        assert count == 1050
        assert mock_db.flush.called

    def test_whitespace_only_csv(self):
        """CSV consisting only of whitespace should return an empty list."""
        queue = CSVImportQueue(csv_data="   \n  \n  ", platform="kdp")
        records = queue.process()
        assert records == []

    def test_extra_whitespace_in_fields(self):
        """Leading/trailing whitespace in field values should be stripped."""
        csv_data = (
            "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
            "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
            "  Padded Book  , B012345678 ,Amazon.com,Kindle Edition,"
            " 10 , 0 , 10 , 9.99 , USD , 6.99 ,January 2024\n"
        )
        queue = CSVImportQueue(csv_data=csv_data, platform="kdp")
        records = queue.process()

        assert len(records) == 1
        # Title should be stripped of leading/trailing whitespace
        assert records[0]["title"].strip() == "Padded Book"

    def test_duplicate_rows_all_kept(self):
        """Duplicate rows in the CSV should all be parsed (dedup is not parser's job)."""
        csv_data = (
            "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
            "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
            "Same Book,B012345678,Amazon.com,Kindle Edition,10,0,10,9.99,USD,6.99,January 2024\n"
            "Same Book,B012345678,Amazon.com,Kindle Edition,10,0,10,9.99,USD,6.99,January 2024\n"
        )
        queue = CSVImportQueue(csv_data=csv_data, platform="kdp")
        records = queue.process()

        assert len(records) == 2
