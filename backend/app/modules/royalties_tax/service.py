"""Business logic for Royalty Tracking & Tax Dashboard."""

from __future__ import annotations

import csv
import io
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import RoyaltyRecord
from app.modules.royalties_tax.models import PlatformRoyaltyImport, TaxDocument

logger = logging.getLogger(__name__)


# ----- Helpers -----------------------------------------------------------


def _year_bounds(year: int) -> tuple[datetime, datetime]:
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    return start, end


def _month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start, end


# ----- Summary -----------------------------------------------------------


async def get_summary(
    db: AsyncSession,
    org_id: UUID,
    year: int,
    period: str = "ytd",
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    year_start, year_end = _year_bounds(year)
    month_start, month_end = _month_bounds(year, now.month if year == now.year else 1)

    # YTD earnings
    stmt_ytd = select(func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0)).where(
        and_(
            RoyaltyRecord.org_id == org_id,
            RoyaltyRecord.period_start >= year_start,
            RoyaltyRecord.period_start < year_end,
        )
    )
    ytd = Decimal(str((await db.execute(stmt_ytd)).scalar_one() or 0))

    stmt_month = select(func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0)).where(
        and_(
            RoyaltyRecord.org_id == org_id,
            RoyaltyRecord.period_start >= month_start,
            RoyaltyRecord.period_start < month_end,
        )
    )
    month = Decimal(str((await db.execute(stmt_month)).scalar_one() or 0))

    # Pending payout: sum of last 30 days
    from datetime import timedelta

    recent_start = now - timedelta(days=30)
    stmt_pending = select(func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0)).where(
        and_(
            RoyaltyRecord.org_id == org_id,
            RoyaltyRecord.period_start >= recent_start,
        )
    )
    pending = Decimal(str((await db.execute(stmt_pending)).scalar_one() or 0))

    # Next payout: convention is last day of next month
    next_month = now.replace(day=1) + timedelta(days=32)
    next_payout = next_month.replace(day=29).date()

    return {
        "ytd_earnings": ytd,
        "month_earnings": month,
        "pending_payout": pending,
        "next_payout_date": next_payout,
        "period": period,
        "year": year,
        "currency": "USD",
    }


# ----- Records -----------------------------------------------------------


async def list_records(
    db: AsyncSession,
    org_id: UUID,
    year: int | None = None,
    platform: str | None = None,
    book_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    clauses = [RoyaltyRecord.org_id == org_id]
    if year:
        ys, ye = _year_bounds(year)
        clauses.extend([RoyaltyRecord.period_start >= ys, RoyaltyRecord.period_start < ye])
    if platform:
        clauses.append(RoyaltyRecord.platform == platform)
    if book_id:
        clauses.append(RoyaltyRecord.book_id == book_id)

    total_stmt = select(func.count()).select_from(RoyaltyRecord).where(and_(*clauses))
    total = (await db.execute(total_stmt)).scalar_one()

    stmt = (
        select(RoyaltyRecord)
        .where(and_(*clauses))
        .order_by(RoyaltyRecord.period_start.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()

    items = []
    for r in rows:
        items.append(
            {
                "id": r.id,
                "book_id": r.book_id,
                "platform": r.platform,
                "title": getattr(r, "title", None),
                "format_type": getattr(r, "format_type", None),
                "units_sold": getattr(r, "units_sold", 0) or 0,
                "royalty_rate": getattr(r, "royalty_rate", None),
                "gross_revenue": getattr(r, "gross_revenue", Decimal("0")) or Decimal("0"),
                "net_revenue": getattr(r, "net_revenue", Decimal("0")) or Decimal("0"),
                "currency": getattr(r, "currency", "USD") or "USD",
                "period_start": r.period_start,
                "period_end": r.period_end,
            }
        )

    return {"items": items, "total": int(total or 0), "limit": limit, "offset": offset}


# ----- Platform breakdown -----------------------------------------------


async def platform_breakdown(
    db: AsyncSession, org_id: UUID, year: int
) -> dict[str, Any]:
    ys, ye = _year_bounds(year)
    stmt = (
        select(
            RoyaltyRecord.platform,
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("amount"),
            func.coalesce(func.sum(RoyaltyRecord.units_sold), 0).label("units"),
            func.max(RoyaltyRecord.period_end).label("last_period"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.period_start >= ys,
                RoyaltyRecord.period_start < ye,
            )
        )
        .group_by(RoyaltyRecord.platform)
    )
    rows = (await db.execute(stmt)).all()
    total = sum((Decimal(str(r.amount or 0)) for r in rows), Decimal("0"))

    entries = []
    for r in rows:
        amt = Decimal(str(r.amount or 0))
        pct = float(amt / total * 100) if total > 0 else 0.0
        entries.append(
            {
                "platform": r.platform,
                "amount": amt,
                "percentage": round(pct, 2),
                "units_sold": int(r.units or 0),
                "last_payment_amount": None,
                "last_payment_date": r.last_period.date() if r.last_period else None,
                "royalty_rate": None,
            }
        )

    entries.sort(key=lambda e: e["amount"], reverse=True)
    return {"total": total, "currency": "USD", "entries": entries}


# ----- Book breakdown ---------------------------------------------------


async def book_breakdown(
    db: AsyncSession, org_id: UUID, year: int
) -> dict[str, Any]:
    ys, ye = _year_bounds(year)
    stmt = (
        select(
            RoyaltyRecord.book_id,
            func.coalesce(func.max(RoyaltyRecord.title), "Untitled").label("title"),
            func.coalesce(func.sum(RoyaltyRecord.units_sold), 0).label("units"),
            func.coalesce(func.sum(RoyaltyRecord.gross_revenue), 0).label("gross"),
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("net"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.period_start >= ys,
                RoyaltyRecord.period_start < ye,
            )
        )
        .group_by(RoyaltyRecord.book_id)
    )
    rows = (await db.execute(stmt)).all()

    total = sum((Decimal(str(r.net or 0)) for r in rows), Decimal("0"))

    entries = []
    for r in rows:
        entries.append(
            {
                "book_id": r.book_id,
                "title": r.title or "Untitled",
                "units_sold": int(r.units or 0),
                "gross_revenue": Decimal(str(r.gross or 0)),
                "net_revenue": Decimal(str(r.net or 0)),
                "platforms": [],
            }
        )

    entries.sort(key=lambda e: e["net_revenue"], reverse=True)
    return {"total": total, "entries": entries}


# ----- Import -----------------------------------------------------------


def _parse_csv_rows(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return [row for row in reader]


async def import_royalty_file(
    db: AsyncSession,
    org_id: UUID,
    user_id: UUID | None,
    platform: str,
    filename: str,
    content: bytes,
) -> PlatformRoyaltyImport:
    """Record an import and (best effort) create royalty_records rows."""

    imp = PlatformRoyaltyImport(
        org_id=org_id,
        user_id=user_id,
        platform=platform,
        source_filename=filename,
        file_size_bytes=len(content) if content else 0,
        status="processing",
    )
    db.add(imp)
    await db.flush()

    processed = 0
    failed = 0
    total_amount = Decimal("0")
    batch_id = uuid4()

    try:
        rows = _parse_csv_rows(content) if content else []
    except Exception as exc:  # pragma: no cover
        imp.status = "failed"
        imp.error_message = f"CSV parse error: {exc}"
        await db.flush()
        return imp

    for row in rows:
        try:
            title = (
                row.get("Title")
                or row.get("title")
                or row.get("Book Title")
                or "Imported Record"
            )
            units_raw = (
                row.get("Units Sold")
                or row.get("units_sold")
                or row.get("Net Units Sold")
                or "0"
            )
            amount_raw = (
                row.get("Royalty")
                or row.get("Net Revenue")
                or row.get("royalty")
                or row.get("Earnings")
                or "0"
            )
            units = int(float(str(units_raw).replace(",", "") or 0))
            amount = Decimal(str(amount_raw).replace(",", "").replace("$", "") or "0")
            period_start = datetime.now(timezone.utc).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            record = RoyaltyRecord(
                org_id=org_id,
                platform=platform,
                marketplace=row.get("Marketplace", "US") or "US",
                title=title[:500],
                asin=(row.get("ASIN") or None),
                isbn=(row.get("ISBN") or None),
                format_type=(row.get("Format") or "ebook").lower()[:50],
                units_sold=units,
                units_refunded=0,
                net_units=units,
                list_price=Decimal("0"),
                royalty_rate=Decimal("0.70"),
                gross_revenue=amount,
                net_revenue=amount,
                currency=(row.get("Currency") or "USD")[:3],
                period_start=period_start,
                period_end=period_start,
                import_batch_id=batch_id,
                raw_data=row,
            )
            db.add(record)
            processed += 1
            total_amount += amount
        except Exception as exc:
            logger.debug("Skipping row due to parse error: %s", exc)
            failed += 1

    imp.records_processed = processed
    imp.records_failed = failed
    imp.total_amount = total_amount
    imp.status = "completed" if failed == 0 else "completed_with_errors"
    await db.flush()
    return imp


# ----- Tax documents ----------------------------------------------------


async def list_tax_documents(
    db: AsyncSession, org_id: UUID, year: int | None = None
) -> dict[str, Any]:
    clauses = [TaxDocument.org_id == org_id]
    if year:
        clauses.append(TaxDocument.tax_year == year)

    stmt = (
        select(TaxDocument)
        .where(and_(*clauses))
        .order_by(TaxDocument.generated_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": rows, "total": len(rows)}


async def get_tax_document(
    db: AsyncSession, org_id: UUID, doc_id: UUID
) -> TaxDocument | None:
    stmt = select(TaxDocument).where(
        and_(TaxDocument.id == doc_id, TaxDocument.org_id == org_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def generate_tax_document(
    db: AsyncSession,
    org_id: UUID,
    tax_year: int,
    document_type: str,
    platform: str | None = None,
    format: str = "pdf",
) -> TaxDocument:
    """Generate a tax document from aggregated royalty_records.

    Stores aggregate totals; ``file_path`` is left null and can be generated
    on-demand when download is requested.
    """

    ys, ye = _year_bounds(tax_year)
    clauses = [
        RoyaltyRecord.org_id == org_id,
        RoyaltyRecord.period_start >= ys,
        RoyaltyRecord.period_start < ye,
    ]
    if platform:
        clauses.append(RoyaltyRecord.platform == platform)

    stmt = select(
        func.coalesce(func.sum(RoyaltyRecord.gross_revenue), 0),
        func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0),
    ).where(and_(*clauses))
    row = (await db.execute(stmt)).one()
    gross = Decimal(str(row[0] or 0))
    net = Decimal(str(row[1] or 0))

    # Rough 25% default tax estimate on net income
    est_tax = (net * Decimal("0.25")).quantize(Decimal("0.01"))

    title_map = {
        "1099_summary": f"1099 Summary {tax_year}",
        "year_end_summary": f"Year-End Summary {tax_year}",
        "tax_preparer_csv": f"Tax Preparer Export {tax_year}",
    }
    title = title_map.get(document_type, f"{document_type} {tax_year}")
    if platform:
        title = f"{title} ({platform})"

    doc = TaxDocument(
        org_id=org_id,
        tax_year=tax_year,
        document_type=document_type,
        platform=platform,
        title=title,
        status="ready",
        format=format,
        gross_income=gross,
        total_expenses=None,
        estimated_tax=est_tax,
        doc_metadata={"net_income": str(net)},
    )
    db.add(doc)
    await db.flush()
    return doc


def render_tax_document_body(doc: TaxDocument) -> tuple[bytes, str]:
    """Render a simple downloadable representation (CSV/text).

    Returns (content_bytes, content_type).
    """

    if (doc.format or "pdf").lower() == "csv":
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["field", "value"])
        writer.writerow(["title", doc.title])
        writer.writerow(["tax_year", doc.tax_year])
        writer.writerow(["document_type", doc.document_type])
        writer.writerow(["platform", doc.platform or ""])
        writer.writerow(["gross_income", str(doc.gross_income or 0)])
        writer.writerow(["total_expenses", str(doc.total_expenses or 0)])
        writer.writerow(["estimated_tax", str(doc.estimated_tax or 0)])
        writer.writerow(
            ["generated_at", doc.generated_at.isoformat() if doc.generated_at else ""]
        )
        return out.getvalue().encode("utf-8"), "text/csv"

    # Default: simple text-as-pdf-placeholder (plain text body)
    lines = [
        f"Title: {doc.title}",
        f"Tax Year: {doc.tax_year}",
        f"Document Type: {doc.document_type}",
        f"Platform: {doc.platform or 'All'}",
        f"Gross Income: ${doc.gross_income or 0}",
        f"Total Expenses: ${doc.total_expenses or 0}",
        f"Estimated Tax: ${doc.estimated_tax or 0}",
        f"Generated: {doc.generated_at.isoformat() if doc.generated_at else ''}",
        "",
        "NOTE: This is an estimate only. Consult a tax professional for",
        "accurate tax advice. SelfPublisherForge is not a tax advisor.",
    ]
    return "\n".join(lines).encode("utf-8"), "text/plain"
