"""CSV importer for distributor royalty reports.

Uses a generic header-mapping approach so the parsers tolerate the
column-name churn that Amazon KDP, IngramSpark, and Draft2Digital
introduce every few quarters.

For each distributor we maintain an ordered list of column aliases.
The first alias present in the CSV header wins.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable


# ---------------------------------------------------------------------------
# Header alias maps
# ---------------------------------------------------------------------------

KDP_ALIASES: dict[str, list[str]] = {
    "amount": [
        "Royalty",
        "royalty",
        "Royalty (USD)",
        "Earnings",
        "earnings",
        "Net Royalty",
    ],
    "units": ["Units Sold", "Net Units Sold", "Units", "Paid Units"],
    "kenp": ["KENP Read", "KENP Pages", "Pages Read"],
    "royalty_type": [
        "Transaction Type",
        "Type",
        "Format",
        "Royalty Type",
    ],
    "title": ["Title", "Book Title", "ASIN Title"],
    "asin": ["ASIN"],
    "isbn": ["ISBN"],
    "period": [
        "Royalty Date",
        "Royalty Period",
        "Date",
        "Reporting Period",
    ],
    "rate": ["Royalty Rate", "Rate"],
    "currency": ["Currency", "Currency Code"],
}

INGRAM_ALIASES: dict[str, list[str]] = {
    "amount": [
        "Publisher Compensation",
        "Net Compensation",
        "Compensation",
        "Publisher Comp",
        "Amount",
    ],
    "units": ["Net Qty", "Qty Sold", "Units Sold", "Quantity"],
    "title": ["Title", "Book Title"],
    "isbn": ["ISBN", "ISBN13"],
    "period": [
        "Reporting Month",
        "Month",
        "Transaction Date",
        "Sales Date",
    ],
    "royalty_type": ["Sales Channel", "Channel", "Product Type"],
    "currency": ["Currency"],
}

D2D_ALIASES: dict[str, list[str]] = {
    "amount": [
        "Earnings",
        "Author Earnings",
        "Net Earnings",
        "Royalty",
        "Amount",
    ],
    "units": ["Units Sold", "Units", "Qty"],
    "title": ["Book", "Title", "Book Title"],
    "retailer": ["Retailer", "Vendor", "Store"],
    "period": ["Sale Date", "Month", "Reporting Month", "Period"],
    "royalty_type": ["Format", "Product Type"],
    "currency": ["Currency"],
}


@dataclass
class ParsedRow:
    distributor: str
    royalty_type: str
    amount: Decimal
    currency: str = "USD"
    units_sold: int | None = None
    kenp_pages: int | None = None
    royalty_rate: Decimal | None = None
    period_month: int | None = None
    period_year: int | None = None
    payment_date: date | None = None
    notes: str | None = None


@dataclass
class ParseResult:
    rows: list[ParsedRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped: int = 0

    @property
    def total(self) -> Decimal:
        return sum((r.amount for r in self.rows), Decimal("0"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pick(row: dict[str, str], aliases: list[str]) -> str | None:
    """Return the first non-empty value from ``row`` whose key matches one of
    the provided aliases (case-insensitive, stripped)."""
    lower = {k.strip().lower(): k for k in row.keys() if k}
    for alias in aliases:
        key = lower.get(alias.strip().lower())
        if key is not None:
            val = row.get(key)
            if val is not None and str(val).strip() != "":
                return str(val).strip()
    return None


def _to_decimal(raw: str | None) -> Decimal:
    if raw is None:
        return Decimal("0")
    s = raw.replace("$", "").replace(",", "").strip()
    if s in ("", "-", "—"):
        return Decimal("0")
    # Handle parentheses as negative
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def _to_int(raw: str | None) -> int | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(Decimal(str(raw).replace(",", "").strip()))
    except (InvalidOperation, ValueError):
        return None


def _parse_period(raw: str | None) -> tuple[int | None, int | None]:
    """Return (month, year) from many formats: 2026-03, Mar 2026, 3/2026, etc."""
    if not raw:
        return None, None
    s = raw.strip()
    # ISO-ish
    for fmt in ("%Y-%m", "%Y-%m-%d", "%m/%Y", "%m-%Y", "%b %Y", "%B %Y", "%Y/%m/%d"):
        try:
            d = datetime.strptime(s, fmt)
            return d.month, d.year
        except ValueError:
            continue
    return None, None


def _normalize_kdp_type(raw: str | None) -> str:
    if not raw:
        return "other"
    v = raw.lower()
    if "kenp" in v or "ku" in v or "pages read" in v or "kindle unlimited" in v:
        return "ku_kenp"
    if "paperback" in v:
        return "paperback"
    if "hardcover" in v or "hardback" in v:
        return "hardcover"
    if "ebook" in v or "kindle" in v:
        return "kindle_ebook"
    return "other"


def _normalize_ingram_type(raw: str | None) -> str:
    # Ingram is print-dominated; default to print.
    if not raw:
        return "print"
    v = raw.lower()
    if "ebook" in v:
        return "ebook"
    return "print"


def _normalize_d2d_type(raw: str | None) -> str:
    if not raw:
        return "ebook"
    return "ebook" if "ebook" in raw.lower() or "digital" in raw.lower() else "other"


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _iter_rows(content: bytes | str) -> Iterable[dict[str, str]]:
    if isinstance(content, bytes):
        # Strip BOM if present.
        text = content.decode("utf-8-sig", errors="replace")
    else:
        text = content
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        yield row


def parse_kdp(content: bytes | str) -> ParseResult:
    result = ParseResult()
    for i, row in enumerate(_iter_rows(content), start=2):
        amount_raw = _pick(row, KDP_ALIASES["amount"])
        if amount_raw is None:
            result.skipped += 1
            continue
        amount = _to_decimal(amount_raw)
        if amount == 0:
            result.skipped += 1
            continue
        rtype = _normalize_kdp_type(_pick(row, KDP_ALIASES["royalty_type"]))
        month, year = _parse_period(_pick(row, KDP_ALIASES["period"]))
        rate_raw = _pick(row, KDP_ALIASES["rate"])
        rate = _to_decimal(rate_raw) if rate_raw else None
        if rate is not None and rate > 1:
            # percentages -> fraction
            rate = rate / Decimal("100")
        title = _pick(row, KDP_ALIASES["title"]) or ""
        asin = _pick(row, KDP_ALIASES["asin"]) or ""
        note_bits = [b for b in [title, asin] if b]
        result.rows.append(
            ParsedRow(
                distributor="kdp",
                royalty_type=rtype,
                amount=amount,
                currency=_pick(row, KDP_ALIASES["currency"]) or "USD",
                units_sold=_to_int(_pick(row, KDP_ALIASES["units"])),
                kenp_pages=_to_int(_pick(row, KDP_ALIASES["kenp"])),
                royalty_rate=rate,
                period_month=month,
                period_year=year,
                notes=" | ".join(note_bits) or None,
            )
        )
    return result


def parse_ingram(content: bytes | str) -> ParseResult:
    result = ParseResult()
    for row in _iter_rows(content):
        amount_raw = _pick(row, INGRAM_ALIASES["amount"])
        if amount_raw is None:
            result.skipped += 1
            continue
        amount = _to_decimal(amount_raw)
        if amount == 0:
            result.skipped += 1
            continue
        rtype = _normalize_ingram_type(_pick(row, INGRAM_ALIASES["royalty_type"]))
        month, year = _parse_period(_pick(row, INGRAM_ALIASES["period"]))
        title = _pick(row, INGRAM_ALIASES["title"]) or ""
        isbn = _pick(row, INGRAM_ALIASES["isbn"]) or ""
        note_bits = [b for b in [title, isbn] if b]
        result.rows.append(
            ParsedRow(
                distributor="ingram",
                royalty_type=rtype,
                amount=amount,
                currency=_pick(row, INGRAM_ALIASES["currency"]) or "USD",
                units_sold=_to_int(_pick(row, INGRAM_ALIASES["units"])),
                period_month=month,
                period_year=year,
                notes=" | ".join(note_bits) or None,
            )
        )
    return result


def parse_d2d(content: bytes | str) -> ParseResult:
    result = ParseResult()
    for row in _iter_rows(content):
        amount_raw = _pick(row, D2D_ALIASES["amount"])
        if amount_raw is None:
            result.skipped += 1
            continue
        amount = _to_decimal(amount_raw)
        if amount == 0:
            result.skipped += 1
            continue
        rtype = _normalize_d2d_type(_pick(row, D2D_ALIASES["royalty_type"]))
        month, year = _parse_period(_pick(row, D2D_ALIASES["period"]))
        title = _pick(row, D2D_ALIASES["title"]) or ""
        retailer = _pick(row, D2D_ALIASES["retailer"]) or ""
        note_bits = [b for b in [retailer, title] if b]
        result.rows.append(
            ParsedRow(
                distributor="d2d",
                royalty_type=rtype,
                amount=amount,
                currency=_pick(row, D2D_ALIASES["currency"]) or "USD",
                units_sold=_to_int(_pick(row, D2D_ALIASES["units"])),
                period_month=month,
                period_year=year,
                notes=" | ".join(note_bits) or None,
            )
        )
    return result


def parse(distributor: str, content: bytes | str) -> ParseResult:
    d = distributor.lower().strip()
    if d == "kdp":
        return parse_kdp(content)
    if d in ("ingram", "ingramspark"):
        return parse_ingram(content)
    if d in ("d2d", "draft2digital"):
        return parse_d2d(content)
    raise ValueError(f"Unknown distributor: {distributor}")
