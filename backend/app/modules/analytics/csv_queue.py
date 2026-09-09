"""CSV import queue service for royalty batch processing.

Provides a ``CSVImportQueue`` class that accepts raw CSV data from any
supported publishing platform (KDP, IngramSpark, Draft2Digital), parses
and validates the rows, and returns a list of normalised royalty record
dicts ready for database insertion.

Also exposes a high-level ``process_csv_import`` async function that
orchestrates end-to-end CSV import: parse, validate, insert, and return
the count of successfully imported records.

Usage from the royalty_sync Celery task::

    from app.modules.analytics.csv_queue import process_csv_import

    count = await process_csv_import(
        db_session=db,
        account_id=account_id,
        platform="kdp",
        csv_data=raw_csv_string_or_bytes,
    )
"""

from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import RoyaltyRecord
from app.modules.analytics.schemas import Platform

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Platform identifier mapping
# ---------------------------------------------------------------------------
# The publishing module uses short keys ("kdp", "ingramspark", "d2d") while
# the analytics module uses the ``Platform`` enum values ("kdp",
# "ingram_spark", "draft2digital").  This mapping normalises both
# conventions into the canonical ``Platform`` enum member.

_PLATFORM_ALIASES: dict[str, Platform] = {
    # Analytics-module canonical keys
    "kdp": Platform.KDP,
    "ingram_spark": Platform.INGRAM_SPARK,
    "draft2digital": Platform.DRAFT2DIGITAL,
    # Publishing-module short keys
    "ingramspark": Platform.INGRAM_SPARK,
    "d2d": Platform.DRAFT2DIGITAL,
    # Common alternatives / display names
    "amazon_kdp": Platform.KDP,
    "kindle": Platform.KDP,
    "ingram": Platform.INGRAM_SPARK,
    "draft2digital": Platform.DRAFT2DIGITAL,
    "other": Platform.KDP,  # fallback: treat as KDP format
}

# Required fields that every validated royalty dict must contain.
_REQUIRED_FIELDS = {"title", "units_sold", "net_revenue", "period_start"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_decimal(value: str | None, default: Decimal = Decimal("0.00")) -> Decimal:
    """Safely convert a string to ``Decimal``, stripping currency symbols."""
    if not value or not value.strip():
        return default
    try:
        cleaned = (
            value.strip()
            .replace(",", "")
            .replace("$", "")
            .replace("\u00a3", "")  # pound sign
            .replace("\u20ac", "")  # euro sign
        )
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return default


def _safe_int(value: str | None, default: int = 0) -> int:
    """Safely convert a string to ``int``."""
    if not value or not value.strip():
        return default
    try:
        cleaned = value.strip().replace(",", "")
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default


def _parse_date(value: str | None) -> datetime | None:
    """Try several common date formats and return a timezone-aware datetime."""
    if not value or not value.strip():
        return None
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


def _compute_period_end(period_start: datetime) -> datetime:
    """Return the first instant of the following month (used as period_end)."""
    if period_start.month == 12:
        return period_start.replace(year=period_start.year + 1, month=1, day=1)
    return period_start.replace(month=period_start.month + 1, day=1)


def _infer_format(raw: str) -> str:
    """Map a free-text format string to one of the canonical format types."""
    lower = (raw or "").lower().strip()
    if "kindle" in lower or "ebook" in lower or "digital" in lower:
        return "ebook"
    if "paperback" in lower or "print" in lower or "pod" in lower:
        return "paperback"
    if "hardcover" in lower or "hard" in lower:
        return "hardcover"
    if "audio" in lower:
        return "audiobook"
    return "ebook"


def _resolve_platform(platform: str) -> Platform:
    """Resolve a platform identifier string to a ``Platform`` enum member.

    Raises ``ValueError`` if the identifier is not recognised.
    """
    key = platform.strip().lower().replace("-", "_").replace(" ", "_")
    resolved = _PLATFORM_ALIASES.get(key)
    if resolved is not None:
        return resolved
    # Try direct enum construction as a last resort.
    try:
        return Platform(key)
    except ValueError:
        raise ValueError(
            f"Unrecognised platform identifier: {platform!r}. " f"Supported values: {sorted(_PLATFORM_ALIASES.keys())}"
        )


# ---------------------------------------------------------------------------
# Per-platform CSV row parsers
# ---------------------------------------------------------------------------
# Each function accepts a single ``csv.DictReader`` row (dict) and the
# row number (for error reporting) and returns a normalised royalty dict
# or ``None`` if the row should be skipped.


def _parse_kdp_row(row: dict[str, str], row_num: int) -> dict[str, Any] | None:
    """Parse one KDP CSV row into a normalised royalty dict.

    Expected KDP columns (header names may vary slightly):
        Title, Author Name, ASIN, ISBN, Marketplace, Royalty Type,
        Transaction Type, Units Sold, Units Refunded, Net Units Sold,
        Avg List Price, Avg Offer Price, Currency, Royalty, Royalty Date
    """
    title = (row.get("Title") or row.get("title") or "").strip()
    if not title:
        logger.debug("KDP row %d: missing title, skipping", row_num)
        return None

    marketplace = (row.get("Marketplace") or row.get("marketplace") or "Amazon.com").strip()
    units_sold = _safe_int(row.get("Units Sold") or row.get("units_sold"))
    units_refunded = _safe_int(row.get("Units Refunded") or row.get("units_refunded"))
    net_units = _safe_int(row.get("Net Units Sold") or row.get("net_units_sold"))
    if net_units == 0 and (units_sold or units_refunded):
        net_units = units_sold - units_refunded

    list_price = _safe_decimal(row.get("Avg List Price") or row.get("avg_list_price"))
    royalty = _safe_decimal(row.get("Royalty") or row.get("royalty"))
    currency = (row.get("Currency") or row.get("currency") or "USD").strip() or "USD"

    period_str = row.get("Royalty Date") or row.get("royalty_date") or ""
    period_start = _parse_date(period_str)
    if period_start is None:
        period_start = datetime.now(UTC).replace(day=1)

    period_end = _compute_period_end(period_start)

    return {
        "platform": Platform.KDP.value,
        "marketplace": marketplace,
        "title": title,
        "asin": (row.get("ASIN") or row.get("asin") or "").strip() or None,
        "isbn": (row.get("ISBN") or row.get("isbn") or "").strip() or None,
        "format_type": _infer_format(row.get("Royalty Type") or row.get("royalty_type") or ""),
        "units_sold": units_sold,
        "units_refunded": units_refunded,
        "net_units": net_units,
        "list_price": list_price,
        "royalty_rate": Decimal("0.70"),
        "gross_revenue": list_price * net_units if net_units else Decimal("0.00"),
        "net_revenue": royalty,
        "currency": currency,
        "period_start": period_start,
        "period_end": period_end,
        "raw_data": dict(row),
    }


def _parse_ingram_spark_row(row: dict[str, str], row_num: int) -> dict[str, Any] | None:
    """Parse one IngramSpark CSV row into a normalised royalty dict.

    Expected IngramSpark columns:
        Title, ISBN, Format, Quantity, Publisher Compensation,
        Currency Code, Sale/Return, Reporting Date
    """
    title = (row.get("Title") or row.get("title") or "").strip()
    if not title:
        logger.debug("IngramSpark row %d: missing title, skipping", row_num)
        return None

    quantity = _safe_int(row.get("Quantity") or row.get("quantity"))
    compensation = _safe_decimal(row.get("Publisher Compensation") or row.get("publisher_compensation"))
    currency = (row.get("Currency Code") or row.get("currency_code") or "USD").strip() or "USD"

    sale_type = (row.get("Sale/Return") or row.get("sale_return") or "Sale").strip()
    if sale_type.lower() == "return":
        units_sold = 0
        units_refunded = abs(quantity)
    else:
        units_sold = quantity
        units_refunded = 0
    net_units = units_sold - units_refunded

    period_str = row.get("Reporting Date") or row.get("reporting_date") or ""
    period_start = _parse_date(period_str)
    if period_start is None:
        period_start = datetime.now(UTC).replace(day=1)

    period_end = _compute_period_end(period_start)

    return {
        "platform": Platform.INGRAM_SPARK.value,
        "marketplace": "IngramSpark",
        "title": title,
        "asin": None,
        "isbn": (row.get("ISBN") or row.get("isbn") or "").strip() or None,
        "format_type": _infer_format(row.get("Format") or row.get("format") or ""),
        "units_sold": units_sold,
        "units_refunded": units_refunded,
        "net_units": net_units,
        "list_price": Decimal("0.00"),
        "royalty_rate": Decimal("0.00"),
        "gross_revenue": compensation,
        "net_revenue": compensation,
        "currency": currency,
        "period_start": period_start,
        "period_end": period_end,
        "raw_data": dict(row),
    }


def _parse_d2d_row(row: dict[str, str], row_num: int) -> dict[str, Any] | None:
    """Parse one Draft2Digital CSV row into a normalised royalty dict.

    Expected D2D columns:
        Title, ISBN, Channel, Payout, Currency, Period, Units
    """
    title = (row.get("Title") or row.get("title") or "").strip()
    if not title:
        logger.debug("D2D row %d: missing title, skipping", row_num)
        return None

    units = _safe_int(row.get("Units") or row.get("units"))
    payout = _safe_decimal(row.get("Payout") or row.get("payout"))
    currency = (row.get("Currency") or row.get("currency") or "USD").strip() or "USD"

    period_str = row.get("Period") or row.get("period") or ""
    period_start = _parse_date(period_str)
    if period_start is None:
        period_start = datetime.now(UTC).replace(day=1)

    period_end = _compute_period_end(period_start)

    return {
        "platform": Platform.DRAFT2DIGITAL.value,
        "marketplace": (row.get("Channel") or row.get("channel") or "D2D").strip() or "D2D",
        "title": title,
        "asin": None,
        "isbn": (row.get("ISBN") or row.get("isbn") or "").strip() or None,
        "format_type": "ebook",
        "units_sold": units,
        "units_refunded": 0,
        "net_units": units,
        "list_price": Decimal("0.00"),
        "royalty_rate": Decimal("0.60"),
        "gross_revenue": payout,
        "net_revenue": payout,
        "currency": currency,
        "period_start": period_start,
        "period_end": period_end,
        "raw_data": dict(row),
    }


# Map Platform enum members to their per-row parser functions.
_ROW_PARSERS: dict[Platform, Any] = {
    Platform.KDP: _parse_kdp_row,
    Platform.INGRAM_SPARK: _parse_ingram_spark_row,
    Platform.DRAFT2DIGITAL: _parse_d2d_row,
}


# ---------------------------------------------------------------------------
# CSVImportQueue
# ---------------------------------------------------------------------------


class CSVImportQueue:
    """Queue-like service that accepts raw CSV data, parses and validates it,
    and returns a list of normalised royalty record dicts.

    Supports KDP, IngramSpark, and Draft2Digital CSV formats.

    Example::

        queue = CSVImportQueue(csv_data=raw_csv, platform="kdp")
        validated_records = queue.process()
        # validated_records is a list[dict[str, Any]] ready for DB insertion

    Attributes:
        platform: Resolved ``Platform`` enum member.
        errors: List of human-readable error strings accumulated during parsing.
    """

    def __init__(
        self,
        csv_data: str | bytes,
        platform: str,
    ) -> None:
        """Initialise the queue with raw CSV data and a platform identifier.

        Args:
            csv_data: Raw CSV content as a UTF-8 string or bytes.  Both
                plain text and bytes (with or without BOM) are accepted.
            platform: Platform identifier string.  Accepts canonical analytics
                keys (``"kdp"``, ``"ingram_spark"``, ``"draft2digital"``),
                publishing-module keys (``"ingramspark"``, ``"d2d"``), and
                common alternatives (``"kindle"``, ``"amazon_kdp"``).

        Raises:
            ValueError: If *platform* cannot be resolved to a known platform.
        """
        self.platform: Platform = _resolve_platform(platform)
        self._csv_text: str = self._decode(csv_data)
        self.errors: list[str] = []

    # -- Internal helpers --------------------------------------------------

    @staticmethod
    def _decode(data: str | bytes) -> str:
        """Normalise *data* to a plain UTF-8 string."""
        if isinstance(data, bytes):
            # Handle BOM if present
            return data.decode("utf-8-sig")
        return data

    def _validate_row(self, record: dict[str, Any], row_num: int) -> bool:
        """Check that *record* contains all required fields.

        Required: title, units_sold (aliased from ``units``), net_revenue
        (aliased from ``revenue``), and period_start (aliased from ``date``).

        Returns ``True`` when valid; appends to ``self.errors`` and returns
        ``False`` otherwise.
        """
        missing: list[str] = []
        if not record.get("title"):
            missing.append("title")
        if record.get("units_sold") is None:
            missing.append("units (units_sold)")
        if record.get("net_revenue") is None:
            missing.append("revenue (net_revenue)")
        if record.get("period_start") is None:
            missing.append("date (period_start)")

        if missing:
            msg = f"Row {row_num}: missing required field(s): {', '.join(missing)}"
            self.errors.append(msg)
            logger.warning("CSV validation failure: %s", msg)
            return False
        return True

    # -- Public API --------------------------------------------------------

    def process(self) -> list[dict[str, Any]]:
        """Parse and validate the CSV data.

        Returns:
            A list of validated royalty record dicts.  Each dict contains all
            fields needed to construct a ``RoyaltyRecord`` model instance
            (minus ``org_id`` and ``import_batch_id``, which are supplied at
            insertion time).

        Invalid rows are skipped and their errors are accumulated in
        ``self.errors``.
        """
        self.errors = []
        row_parser = _ROW_PARSERS.get(self.platform)

        if row_parser is None:
            msg = f"No CSV parser available for platform: {self.platform.value}"
            self.errors.append(msg)
            logger.error(msg)
            return []

        reader = csv.DictReader(io.StringIO(self._csv_text))
        validated: list[dict[str, Any]] = []

        for i, row in enumerate(reader, start=2):  # row 1 = header
            try:
                parsed = row_parser(row, i)
                if parsed is None:
                    # Row was intentionally skipped (e.g. blank title).
                    self.errors.append(f"Row {i}: skipped (missing title)")
                    continue
                if self._validate_row(parsed, i):
                    validated.append(parsed)
            except (
                KeyError,
                ValueError,
                TypeError,
                InvalidOperation,
                AttributeError,
            ) as exc:
                msg = f"Row {i}: parse error: {exc}"
                self.errors.append(msg)
                logger.warning("CSV parse error at row %d: %s", i, exc, exc_info=True)

        logger.info(
            "CSVImportQueue processed %d valid record(s) for platform %s " "(%d error(s))",
            len(validated),
            self.platform.value,
            len(self.errors),
        )
        return validated


# ---------------------------------------------------------------------------
# High-level async import function
# ---------------------------------------------------------------------------


async def process_csv_import(
    db_session: AsyncSession,
    account_id: uuid.UUID,
    platform: str,
    csv_data: str | bytes,
) -> int:
    """Parse a CSV payload and insert valid royalty records into the database.

    This is the main entry point intended to be called from the
    ``royalty_sync`` Celery task (or any other caller that needs batch CSV
    import).

    Args:
        db_session: An active SQLAlchemy async session.
        account_id: The organisation (tenant) UUID that owns the records.
            This is used as ``org_id`` on each ``RoyaltyRecord``.
        platform: Platform identifier string (see ``CSVImportQueue`` for
            accepted values).
        csv_data: Raw CSV content as a string or bytes.

    Returns:
        The number of records successfully inserted into the database.
        Invalid rows are logged but do not cause the entire import to fail.
    """
    try:
        queue = CSVImportQueue(csv_data=csv_data, platform=platform)
    except ValueError as exc:
        logger.error(
            "Failed to initialise CSVImportQueue for account %s: %s",
            account_id,
            exc,
        )
        return 0

    validated_records = queue.process()

    if not validated_records:
        logger.info(
            "No valid records to import for account %s (platform=%s). " "Errors: %s",
            account_id,
            platform,
            queue.errors[:10] if queue.errors else "none",
        )
        return 0

    batch_id = uuid.uuid4()
    imported = 0

    for i, record_data in enumerate(validated_records):
        try:
            record = RoyaltyRecord(
                org_id=account_id,
                import_batch_id=batch_id,
                **record_data,
            )
            db_session.add(record)
            imported += 1
        except (TypeError, ValueError, KeyError) as exc:
            logger.warning(
                "Failed to create RoyaltyRecord %d/%d for account %s: %s",
                i + 1,
                len(validated_records),
                account_id,
                exc,
                exc_info=True,
            )

    if imported > 0:
        await db_session.flush()

    logger.info(
        "CSV import complete for account %s (platform=%s): " "%d record(s) imported, %d skipped, batch_id=%s",
        account_id,
        platform,
        imported,
        len(validated_records) - imported,
        batch_id,
    )

    if queue.errors:
        logger.warning(
            "CSV import had %d validation error(s) for account %s: %s",
            len(queue.errors),
            account_id,
            queue.errors[:5],
        )

    return imported
