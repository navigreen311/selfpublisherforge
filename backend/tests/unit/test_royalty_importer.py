"""Unit tests for the royalty importer module.

Tests CSV parsing for KDP, IngramSpark, and Draft2Digital formats,
data normalization, error handling, and the import pipeline.
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.analytics.royalty_importer import (
    _infer_format,
    _parse_date,
    _safe_decimal,
    _safe_int,
    decode_file_content,
    import_royalties,
    parse_d2d_csv,
    parse_ingram_spark_csv,
    parse_kdp_csv,
)
from app.modules.analytics.schemas import Platform


# ---------- Helper function tests ----------


class TestSafeDecimal:
    def test_valid_decimal(self):
        assert _safe_decimal("10.50") == Decimal("10.50")

    def test_with_dollar_sign(self):
        assert _safe_decimal("$10.50") == Decimal("10.50")

    def test_with_commas(self):
        assert _safe_decimal("1,234.56") == Decimal("1234.56")

    def test_empty_string(self):
        assert _safe_decimal("") == Decimal("0.00")

    def test_none(self):
        assert _safe_decimal(None) == Decimal("0.00")

    def test_whitespace(self):
        assert _safe_decimal("  ") == Decimal("0.00")

    def test_invalid(self):
        assert _safe_decimal("abc") == Decimal("0.00")

    def test_custom_default(self):
        assert _safe_decimal("", Decimal("1.00")) == Decimal("1.00")

    def test_negative(self):
        assert _safe_decimal("-5.25") == Decimal("-5.25")

    def test_euro_sign(self):
        assert _safe_decimal("\u20ac12.34") == Decimal("12.34")

    def test_pound_sign(self):
        assert _safe_decimal("\u00a312.34") == Decimal("12.34")


class TestSafeInt:
    def test_valid_int(self):
        assert _safe_int("42") == 42

    def test_with_commas(self):
        assert _safe_int("1,234") == 1234

    def test_float_string(self):
        assert _safe_int("42.7") == 42

    def test_empty_string(self):
        assert _safe_int("") == 0

    def test_none(self):
        assert _safe_int(None) == 0

    def test_invalid(self):
        assert _safe_int("abc") == 0

    def test_negative(self):
        assert _safe_int("-5") == -5


class TestParseDate:
    def test_iso_format(self):
        result = _parse_date("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_us_format(self):
        result = _parse_date("01/15/2024")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1

    def test_month_year_format(self):
        result = _parse_date("January 2024")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1

    def test_abbreviated_month(self):
        result = _parse_date("Jan 2024")
        assert result is not None
        assert result.year == 2024

    def test_empty_string(self):
        assert _parse_date("") is None

    def test_none(self):
        assert _parse_date(None) is None

    def test_invalid_date(self):
        assert _parse_date("not-a-date") is None

    def test_whitespace(self):
        assert _parse_date("  ") is None

    def test_with_whitespace_padding(self):
        result = _parse_date("  2024-01-15  ")
        assert result is not None
        assert result.year == 2024


class TestInferFormat:
    def test_kindle(self):
        assert _infer_format("Kindle Edition") == "ebook"

    def test_ebook(self):
        assert _infer_format("eBook") == "ebook"

    def test_paperback(self):
        assert _infer_format("Paperback") == "paperback"

    def test_print(self):
        assert _infer_format("Print on Demand") == "paperback"

    def test_hardcover(self):
        assert _infer_format("Hardcover") == "hardcover"

    def test_audiobook(self):
        assert _infer_format("Audiobook") == "audiobook"

    def test_empty(self):
        assert _infer_format("") == "ebook"

    def test_none(self):
        assert _infer_format(None) == "ebook"

    def test_unknown(self):
        assert _infer_format("xyz") == "ebook"

    def test_digital(self):
        assert _infer_format("Digital") == "ebook"


class TestDecodeFileContent:
    def test_base64_content(self):
        original = "Title,Revenue\nBook A,100.00"
        encoded = base64.b64encode(original.encode()).decode()
        decoded = decode_file_content(encoded)
        assert decoded == original

    def test_plain_text_fallback(self):
        plain = "Title,Revenue\nBook A,100.00"
        decoded = decode_file_content(plain)
        assert decoded == plain

    def test_utf8_bom(self):
        original = "Title,Revenue\nBook A,100.00"
        with_bom = b"\xef\xbb\xbf" + original.encode()
        encoded = base64.b64encode(with_bom).decode()
        decoded = decode_file_content(encoded)
        assert decoded == original


# ---------- CSV Parser tests ----------


class TestParseKdpCsv:
    def test_valid_kdp_csv(self):
        csv_text = (
            "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
            "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date\n"
            "My Book,B012345678,Amazon.com,Kindle Edition,100,5,95,9.99,USD,6.99,January 2024\n"
            "Other Book,B098765432,Amazon.co.uk,Kindle Edition,50,2,48,7.99,GBP,4.99,January 2024\n"
        )
        records = parse_kdp_csv(csv_text)

        assert len(records) == 2

        first = records[0]
        assert first["title"] == "My Book"
        assert first["asin"] == "B012345678"
        assert first["platform"] == "kdp"
        assert first["units_sold"] == 100
        assert first["units_refunded"] == 5
        assert first["net_units"] == 95
        assert first["net_revenue"] == Decimal("6.99")
        assert first["currency"] == "USD"

    def test_empty_csv(self):
        csv_text = "Title,ASIN,Marketplace\n"
        records = parse_kdp_csv(csv_text)
        assert len(records) == 0

    def test_missing_title_skipped(self):
        csv_text = (
            "Title,ASIN,Units Sold,Royalty\n"
            ",B012345678,100,6.99\n"
            "Valid Book,B098765432,50,4.99\n"
        )
        records = parse_kdp_csv(csv_text)
        assert len(records) == 1
        assert records[0]["title"] == "Valid Book"

    def test_computes_net_units_from_sold_and_refunded(self):
        csv_text = (
            "Title,ASIN,Units Sold,Units Refunded,Net Units Sold,Avg List Price,Royalty,Currency\n"
            "My Book,B012345678,100,10,0,9.99,6.99,USD\n"
        )
        records = parse_kdp_csv(csv_text)
        assert len(records) == 1
        assert records[0]["net_units"] == 90  # 100 - 10

    def test_format_inference(self):
        csv_text = (
            "Title,ASIN,Royalty Type,Units Sold,Royalty,Currency\n"
            "My Book,B012345678,Kindle Edition,100,6.99,USD\n"
        )
        records = parse_kdp_csv(csv_text)
        assert records[0]["format_type"] == "ebook"


class TestParseIngramSparkCsv:
    def test_valid_ingram_csv(self):
        csv_text = (
            "Title,ISBN,Format,Quantity,Publisher Compensation,"
            "Currency Code,Sale/Return,Reporting Date\n"
            "My Print Book,9781234567890,Paperback,25,75.50,USD,Sale,2024-01-15\n"
        )
        records = parse_ingram_spark_csv(csv_text)

        assert len(records) == 1
        first = records[0]
        assert first["title"] == "My Print Book"
        assert first["isbn"] == "9781234567890"
        assert first["platform"] == "ingram_spark"
        assert first["units_sold"] == 25
        assert first["net_revenue"] == Decimal("75.50")
        assert first["format_type"] == "paperback"

    def test_return_handling(self):
        csv_text = (
            "Title,ISBN,Format,Quantity,Publisher Compensation,"
            "Currency Code,Sale/Return,Reporting Date\n"
            "My Book,9781234567890,Paperback,3,9.00,USD,Return,2024-01-15\n"
        )
        records = parse_ingram_spark_csv(csv_text)
        assert len(records) == 1
        assert records[0]["units_sold"] == 0
        assert records[0]["units_refunded"] == 3
        assert records[0]["net_units"] == -3

    def test_empty_csv(self):
        csv_text = "Title,ISBN,Format\n"
        records = parse_ingram_spark_csv(csv_text)
        assert len(records) == 0


class TestParseD2DCsv:
    def test_valid_d2d_csv(self):
        csv_text = (
            "Title,ISBN,Channel,Payout,Currency,Period,Units\n"
            "My eBook,9781234567890,Apple Books,45.00,USD,January 2024,30\n"
        )
        records = parse_d2d_csv(csv_text)

        assert len(records) == 1
        first = records[0]
        assert first["title"] == "My eBook"
        assert first["platform"] == "draft2digital"
        assert first["marketplace"] == "Apple Books"
        assert first["net_revenue"] == Decimal("45.00")
        assert first["net_units"] == 30
        assert first["format_type"] == "ebook"

    def test_empty_csv(self):
        csv_text = "Title,ISBN,Channel\n"
        records = parse_d2d_csv(csv_text)
        assert len(records) == 0


# ---------- Import pipeline tests ----------


class TestImportRoyalties:
    @pytest.fixture
    def org_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_import_kdp_csv(self, mock_db, org_id):
        csv_text = (
            "Title,ASIN,Marketplace,Units Sold,Royalty,Currency\n"
            "Book One,B012345678,Amazon.com,50,3.49,USD\n"
            "Book Two,B098765432,Amazon.com,25,1.74,USD\n"
        )
        encoded = base64.b64encode(csv_text.encode()).decode()

        result = await import_royalties(mock_db, org_id, Platform.KDP, encoded)

        assert result.records_imported == 2
        assert result.records_skipped == 0
        assert result.platform == "kdp"
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_import_empty_content(self, mock_db, org_id):
        csv_text = "Title,ASIN\n"
        encoded = base64.b64encode(csv_text.encode()).decode()

        result = await import_royalties(mock_db, org_id, Platform.KDP, encoded)

        assert result.records_imported == 0
        assert "No valid records" in result.errors[0]

    @pytest.mark.asyncio
    async def test_import_unsupported_platform(self, mock_db, org_id):
        result = await import_royalties(mock_db, org_id, Platform.OTHER, "data")

        assert result.records_imported == 0
        assert "Unsupported platform" in result.errors[0]

    @pytest.mark.asyncio
    async def test_import_plain_text_csv(self, mock_db, org_id):
        """Test that non-base64 text is handled gracefully."""
        csv_text = (
            "Title,ASIN,Units Sold,Royalty,Currency\n"
            "My Book,B012345678,10,6.99,USD\n"
        )
        result = await import_royalties(mock_db, org_id, Platform.KDP, csv_text)

        assert result.records_imported == 1
        assert result.records_skipped == 0

    @pytest.mark.asyncio
    async def test_import_sets_batch_id(self, mock_db, org_id):
        csv_text = (
            "Title,ASIN,Units Sold,Royalty,Currency\n"
            "Book A,B012345678,10,6.99,USD\n"
        )
        encoded = base64.b64encode(csv_text.encode()).decode()

        result = await import_royalties(mock_db, org_id, Platform.KDP, encoded)

        assert result.import_batch_id is not None
        # Verify db.add was called
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_import_ingram_spark(self, mock_db, org_id):
        csv_text = (
            "Title,ISBN,Format,Quantity,Publisher Compensation,"
            "Currency Code,Sale/Return,Reporting Date\n"
            "Print Book,9781234567890,Paperback,10,30.00,USD,Sale,2024-01-15\n"
        )
        encoded = base64.b64encode(csv_text.encode()).decode()

        result = await import_royalties(mock_db, org_id, Platform.INGRAM_SPARK, encoded)

        assert result.records_imported == 1
        assert result.platform == "ingram_spark"

    @pytest.mark.asyncio
    async def test_import_d2d(self, mock_db, org_id):
        csv_text = (
            "Title,ISBN,Channel,Payout,Currency,Period,Units\n"
            "eBook Title,9781234567890,Apple Books,15.00,USD,January 2024,10\n"
        )
        encoded = base64.b64encode(csv_text.encode()).decode()

        result = await import_royalties(mock_db, org_id, Platform.DRAFT2DIGITAL, encoded)

        assert result.records_imported == 1
        assert result.platform == "draft2digital"
