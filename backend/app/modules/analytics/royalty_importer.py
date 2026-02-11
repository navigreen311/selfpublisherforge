"""Royalty CSV import pipeline.

Parses royalty CSV files from KDP, IngramSpark, and Draft2Digital.
Normalizes data into a common RoyaltyRecord format.
"""

from __future__ import annotations

import base64
import binascii
import csv
import io
import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import RoyaltyRecord
from app.modules.analytics.schemas import Platform, RoyaltyImportResponse


class RoyaltyParseError(Exception):
    """Raised when a royalty CSV cannot be parsed."""

    def __init__(self, message: str, row_number: int | None = None):
        self.row_number = row_number
        super().__init__(message)


def _safe_decimal(value: str | None, default: Decimal = Decimal("0.00")) -> Decimal:
    """Safely convert a string to Decimal."""
    if not value or not value.strip():
        return default
    try:
        cleaned = value.strip().replace(",", "").replace("$", "").replace("£", "").replace("€", "")
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return default


def _safe_int(value: str | None, default: int = 0) -> int:
    """Safely convert a string to int."""
    if not value or not value.strip():
        return default
    try:
        cleaned = value.strip().replace(",", "")
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default


def _parse_date(value: str | None, formats: list[str] | None = None) -> datetime | None:
    """Try multiple date formats to parse a date string."""
    if not value or not value.strip():
        return None
    if formats is None:
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m/%d/%y",
            "%d/%m/%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%B %Y",  # "January 2024"
            "%b %Y",  # "Jan 2024"
        ]
    cleaned = value.strip()
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def decode_file_content(content: str) -> str:
    """Decode base64 file content to string."""
    try:
        decoded = base64.b64decode(content)
        return decoded.decode("utf-8-sig")  # Handle BOM
    except (binascii.Error, UnicodeDecodeError) as exc:
        logger.debug("Base64 decode failed, assuming plain text: %s", exc, exc_info=True)
        # Assume it's already plain text
        return content


def parse_kdp_csv(csv_text: str) -> list[dict[str, Any]]:
    """Parse an Amazon KDP royalty CSV into normalized records.

    Expected columns (may vary by report version):
    - Title, Author Name, ASIN, Marketplace, Royalty Type,
      Transaction Type, Units Sold, Units Refunded, Net Units Sold,
      Avg List Price, Avg Offer Price, Currency, Royalty
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    records = []
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            title = row.get("Title", row.get("title", "")).strip()
            if not title:
                errors.append(f"Row {i}: missing title, skipped")
                continue

            marketplace = row.get("Marketplace", row.get("marketplace", "Amazon.com")).strip()
            units_sold = _safe_int(row.get("Units Sold", row.get("units_sold")))
            units_refunded = _safe_int(row.get("Units Refunded", row.get("units_refunded")))
            net_units = _safe_int(row.get("Net Units Sold", row.get("net_units_sold")))
            if net_units == 0:
                net_units = units_sold - units_refunded

            list_price = _safe_decimal(row.get("Avg List Price", row.get("avg_list_price")))
            royalty = _safe_decimal(row.get("Royalty", row.get("royalty")))
            currency = row.get("Currency", row.get("currency", "USD")).strip() or "USD"

            # KDP reports are typically monthly
            period_str = row.get("Royalty Date", row.get("royalty_date", ""))
            period_date = _parse_date(period_str)
            if period_date is None:
                period_date = datetime.now(UTC).replace(day=1)

            # Approximate period end as last day of month
            if period_date.month == 12:
                period_end = period_date.replace(year=period_date.year + 1, month=1)
            else:
                period_end = period_date.replace(month=period_date.month + 1)

            records.append({
                "platform": Platform.KDP.value,
                "marketplace": marketplace,
                "title": title,
                "asin": (row.get("ASIN", row.get("asin", "")) or "").strip() or None,
                "isbn": (row.get("ISBN", row.get("isbn", "")) or "").strip() or None,
                "format_type": _infer_format(row.get("Royalty Type", row.get("royalty_type", ""))),
                "units_sold": units_sold,
                "units_refunded": units_refunded,
                "net_units": net_units,
                "list_price": list_price,
                "royalty_rate": Decimal("0.70"),
                "gross_revenue": list_price * net_units,
                "net_revenue": royalty,
                "currency": currency,
                "period_start": period_date,
                "period_end": period_end,
                "raw_data": dict(row),
            })
        except (KeyError, ValueError, TypeError, InvalidOperation, AttributeError) as exc:
            logger.warning("KDP CSV row %d parse error: %s", i, exc, exc_info=True)
            errors.append(f"Row {i}: {exc}")

    return records


def parse_ingram_spark_csv(csv_text: str) -> list[dict[str, Any]]:
    """Parse an IngramSpark royalty CSV.

    Expected columns (typical format):
    - Title, ISBN, Format, Quantity, Publisher Compensation,
      Currency Code, Sale/Return, Reporting Date
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    records = []

    for i, row in enumerate(reader, start=2):
        try:
            title = row.get("Title", row.get("title", "")).strip()
            if not title:
                continue

            quantity = _safe_int(row.get("Quantity", row.get("quantity")))
            compensation = _safe_decimal(row.get("Publisher Compensation", row.get("publisher_compensation")))
            currency = row.get("Currency Code", row.get("currency_code", "USD")).strip() or "USD"

            sale_type = row.get("Sale/Return", row.get("sale_return", "Sale")).strip()
            units_sold = quantity if sale_type.lower() == "sale" else 0
            units_refunded = abs(quantity) if sale_type.lower() == "return" else 0
            net_units = units_sold - units_refunded

            period_str = row.get("Reporting Date", row.get("reporting_date", ""))
            period_date = _parse_date(period_str)
            if period_date is None:
                period_date = datetime.now(UTC).replace(day=1)

            if period_date.month == 12:
                period_end = period_date.replace(year=period_date.year + 1, month=1)
            else:
                period_end = period_date.replace(month=period_date.month + 1)

            records.append({
                "platform": Platform.INGRAM_SPARK.value,
                "marketplace": "IngramSpark",
                "title": title,
                "asin": None,
                "isbn": (row.get("ISBN", row.get("isbn", "")) or "").strip() or None,
                "format_type": _infer_format(row.get("Format", row.get("format", ""))),
                "units_sold": units_sold,
                "units_refunded": units_refunded,
                "net_units": net_units,
                "list_price": Decimal("0.00"),
                "royalty_rate": Decimal("0.00"),
                "gross_revenue": compensation,
                "net_revenue": compensation,
                "currency": currency,
                "period_start": period_date,
                "period_end": period_end,
                "raw_data": dict(row),
            })
        except (KeyError, ValueError, TypeError, InvalidOperation, AttributeError) as exc:
            logger.warning("IngramSpark CSV row %d parse error: %s", i, exc, exc_info=True)
            continue

    return records


def parse_d2d_csv(csv_text: str) -> list[dict[str, Any]]:
    """Parse a Draft2Digital royalty CSV.

    Expected columns:
    - Title, ISBN, Channel, Payout, Currency, Period, Units
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    records = []

    for i, row in enumerate(reader, start=2):
        try:
            title = row.get("Title", row.get("title", "")).strip()
            if not title:
                continue

            units = _safe_int(row.get("Units", row.get("units")))
            payout = _safe_decimal(row.get("Payout", row.get("payout")))
            currency = row.get("Currency", row.get("currency", "USD")).strip() or "USD"

            period_str = row.get("Period", row.get("period", ""))
            period_date = _parse_date(period_str)
            if period_date is None:
                period_date = datetime.now(UTC).replace(day=1)

            if period_date.month == 12:
                period_end = period_date.replace(year=period_date.year + 1, month=1)
            else:
                period_end = period_date.replace(month=period_date.month + 1)

            records.append({
                "platform": Platform.DRAFT2DIGITAL.value,
                "marketplace": row.get("Channel", row.get("channel", "D2D")).strip() or "D2D",
                "title": title,
                "asin": None,
                "isbn": (row.get("ISBN", row.get("isbn", "")) or "").strip() or None,
                "format_type": "ebook",
                "units_sold": units,
                "units_refunded": 0,
                "net_units": units,
                "list_price": Decimal("0.00"),
                "royalty_rate": Decimal("0.60"),
                "gross_revenue": payout,
                "net_revenue": payout,
                "currency": currency,
                "period_start": period_date,
                "period_end": period_end,
                "raw_data": dict(row),
            })
        except (KeyError, ValueError, TypeError, InvalidOperation, AttributeError) as exc:
            logger.warning("D2D CSV row %d parse error: %s", i, exc, exc_info=True)
            continue

    return records


def _infer_format(format_str: str) -> str:
    """Infer book format from a string."""
    lower = (format_str or "").lower().strip()
    if "kindle" in lower or "ebook" in lower or "digital" in lower:
        return "ebook"
    if "paperback" in lower or "print" in lower or "pod" in lower:
        return "paperback"
    if "hardcover" in lower or "hard" in lower:
        return "hardcover"
    if "audio" in lower:
        return "audiobook"
    return "ebook"


PLATFORM_PARSERS = {
    Platform.KDP: parse_kdp_csv,
    Platform.INGRAM_SPARK: parse_ingram_spark_csv,
    Platform.DRAFT2DIGITAL: parse_d2d_csv,
}


async def import_royalties(
    db: AsyncSession,
    org_id: uuid.UUID,
    platform: Platform,
    csv_content: str,
) -> RoyaltyImportResponse:
    """Import royalty records from CSV content for a given platform.

    Returns an import summary with counts and any errors encountered.
    """
    parser = PLATFORM_PARSERS.get(platform)
    if parser is None:
        return RoyaltyImportResponse(
            import_batch_id=uuid.uuid4(),
            records_imported=0,
            records_skipped=0,
            errors=[f"Unsupported platform: {platform}"],
            platform=platform.value,
        )

    text_content = decode_file_content(csv_content)
    parsed_records = parser(text_content)

    if not parsed_records:
        return RoyaltyImportResponse(
            import_batch_id=uuid.uuid4(),
            records_imported=0,
            records_skipped=0,
            errors=["No valid records found in file"],
            platform=platform.value,
        )

    batch_id = uuid.uuid4()
    imported = 0
    skipped = 0
    errors: list[str] = []

    for i, record_data in enumerate(parsed_records):
        try:
            record = RoyaltyRecord(
                org_id=org_id,
                import_batch_id=batch_id,
                **record_data,
            )
            db.add(record)
            imported += 1
        except (TypeError, ValueError, KeyError) as exc:
            logger.warning("Failed to create RoyaltyRecord for record %d: %s", i + 1, exc, exc_info=True)
            skipped += 1
            errors.append(f"Record {i + 1}: {exc}")

    if imported > 0:
        await db.flush()

    return RoyaltyImportResponse(
        import_batch_id=batch_id,
        records_imported=imported,
        records_skipped=skipped,
        errors=errors,
        platform=platform.value,
    )
