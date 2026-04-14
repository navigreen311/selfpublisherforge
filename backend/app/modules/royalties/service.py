"""Service layer for the Royalties module.

All monetary math uses ``Decimal`` — never float.
"""

from __future__ import annotations

import calendar
import io
import uuid
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.royalties import importer
from app.modules.royalties.models import RoyaltyEntry
from app.modules.royalties.schemas import (
    DistributorSummary,
    MonthlyStatement,
    MonthlyStatementRow,
    RoyaltyDashboard,
    RoyaltyEntryCreate,
    RoyaltyImportResult,
)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

async def list_entries(
    db: AsyncSession,
    org_id: UUID,
    *,
    period: str = "ytd",
    year: int | None = None,
    month: int | None = None,
    pen_name_id: UUID | None = None,
    distributor: str | None = None,
    limit: int = 500,
) -> list[RoyaltyEntry]:
    today = date.today()
    y = year or today.year
    stmt = select(RoyaltyEntry).where(RoyaltyEntry.org_id == org_id)

    if period == "ytd":
        stmt = stmt.where(RoyaltyEntry.period_year == y)
    elif period == "year":
        stmt = stmt.where(RoyaltyEntry.period_year == y)
    elif period == "month":
        m = month or today.month
        stmt = stmt.where(
            and_(RoyaltyEntry.period_year == y, RoyaltyEntry.period_month == m)
        )
    elif period == "quarter":
        q_month = month or today.month
        q = (q_month - 1) // 3 + 1
        months = [3 * (q - 1) + 1, 3 * (q - 1) + 2, 3 * (q - 1) + 3]
        stmt = stmt.where(
            and_(RoyaltyEntry.period_year == y, RoyaltyEntry.period_month.in_(months))
        )

    if pen_name_id is not None:
        stmt = stmt.where(RoyaltyEntry.pen_name_id == pen_name_id)
    if distributor:
        stmt = stmt.where(RoyaltyEntry.distributor == distributor)

    stmt = stmt.order_by(
        RoyaltyEntry.period_year.desc().nullslast(),
        RoyaltyEntry.period_month.desc().nullslast(),
    ).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


# ---------------------------------------------------------------------------
# Dashboard / aggregations
# ---------------------------------------------------------------------------

_PCT_QUANT = Decimal("0.01")


def _q(v: Decimal) -> Decimal:
    return v.quantize(_PCT_QUANT, rounding=ROUND_HALF_UP)


def _pct(part: Decimal, total: Decimal) -> float:
    if total <= 0:
        return 0.0
    return float((part / total * Decimal("100")).quantize(Decimal("0.01")))


async def get_dashboard(
    db: AsyncSession,
    org_id: UUID,
    *,
    year: int | None = None,
    pen_name_id: UUID | None = None,
) -> RoyaltyDashboard:
    today = date.today()
    y = year or today.year
    entries = await list_entries(
        db, org_id, period="year", year=y, pen_name_id=pen_name_id, limit=10_000
    )

    ytd = sum((e.amount for e in entries), Decimal("0"))
    this_month = sum(
        (e.amount for e in entries if e.period_month == today.month),
        Decimal("0"),
    )

    # Breakdown by distributor
    by_dist: dict[str, list[RoyaltyEntry]] = defaultdict(list)
    for e in entries:
        by_dist[e.distributor].append(e)

    summaries: list[DistributorSummary] = []
    for dist, rows in sorted(by_dist.items(), key=lambda kv: -sum((r.amount for r in kv[1]), Decimal(0))):
        total = sum((r.amount for r in rows), Decimal("0"))
        breakdown: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for r in rows:
            breakdown[r.royalty_type] += r.amount
        # most recent payment
        paid = [r for r in rows if r.payment_date is not None]
        paid.sort(key=lambda r: r.payment_date, reverse=True)
        last_amt = paid[0].amount if paid else None
        last_date = paid[0].payment_date if paid else None
        summaries.append(
            DistributorSummary(
                distributor=dist,
                total=_q(total),
                pct=_pct(total, ytd),
                breakdown={k: _q(v) for k, v in breakdown.items()},
                units_sold=sum((r.units_sold or 0) for r in rows),
                kenp_pages=sum((r.kenp_pages or 0) for r in rows),
                last_payment_amount=_q(last_amt) if last_amt is not None else None,
                last_payment_date=last_date,
            )
        )

    pending = sum(
        (e.amount for e in entries if e.payment_date is None),
        Decimal("0"),
    )

    return RoyaltyDashboard(
        ytd_earnings=_q(ytd),
        this_month_earnings=_q(this_month),
        pending_payout=_q(pending),
        next_payout_date=_next_payout_date(today),
        by_distributor=summaries,
        total=_q(ytd),
        period="ytd",
        year=y,
    )


def _next_payout_date(today: date) -> date:
    """Amazon pays ~60 days in arrears at month end. Heuristic only."""
    # 29th of next month is a reasonable placeholder.
    year = today.year
    month = today.month + 1
    if month > 12:
        month = 1
        year += 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(29, last))


async def get_monthly_statement(
    db: AsyncSession,
    org_id: UUID,
    year: int,
    *,
    pen_name_id: UUID | None = None,
) -> MonthlyStatement:
    entries = await list_entries(
        db, org_id, period="year", year=year, pen_name_id=pen_name_id, limit=100_000
    )

    months: dict[int, MonthlyStatementRow] = {}
    for m in range(1, 13):
        months[m] = MonthlyStatementRow(
            month=m,
            year=year,
            label=f"{calendar.month_abbr[m]} {year}",
        )

    for e in entries:
        if not e.period_month:
            continue
        row = months[e.period_month]
        amt = e.amount
        d = e.distributor
        rt = e.royalty_type
        if d == "kdp":
            if rt == "ku_kenp":
                row.ku_kenp += amt
            elif rt in ("paperback", "hardcover", "print"):
                row.kdp_print += amt
            else:
                row.kdp_ebook += amt
        elif d == "ingram":
            row.ingram += amt
        elif d == "d2d":
            row.d2d += amt
        else:
            row.other += amt
        row.total += amt

    # YTD totals
    ytd = MonthlyStatementRow(month=0, year=year, label="YTD Total")
    for r in months.values():
        ytd.kdp_ebook += r.kdp_ebook
        ytd.kdp_print += r.kdp_print
        ytd.ku_kenp += r.ku_kenp
        ytd.ingram += r.ingram
        ytd.d2d += r.d2d
        ytd.other += r.other
        ytd.total += r.total

    rows = [
        MonthlyStatementRow(
            month=r.month,
            year=r.year,
            label=r.label,
            kdp_ebook=_q(r.kdp_ebook),
            kdp_print=_q(r.kdp_print),
            ku_kenp=_q(r.ku_kenp),
            ingram=_q(r.ingram),
            d2d=_q(r.d2d),
            other=_q(r.other),
            total=_q(r.total),
        )
        for r in months.values()
    ]
    ytd = MonthlyStatementRow(
        month=0,
        year=year,
        label="YTD Total",
        kdp_ebook=_q(ytd.kdp_ebook),
        kdp_print=_q(ytd.kdp_print),
        ku_kenp=_q(ytd.ku_kenp),
        ingram=_q(ytd.ingram),
        d2d=_q(ytd.d2d),
        other=_q(ytd.other),
        total=_q(ytd.total),
    )
    return MonthlyStatement(year=year, rows=rows, ytd_totals=ytd)


# ---------------------------------------------------------------------------
# Create / import
# ---------------------------------------------------------------------------

async def create_manual_entry(
    db: AsyncSession, org_id: UUID, payload: RoyaltyEntryCreate
) -> RoyaltyEntry:
    entry = RoyaltyEntry(
        org_id=org_id,
        distributor=payload.distributor,
        royalty_type=payload.royalty_type,
        amount=payload.amount,
        currency=payload.currency,
        units_sold=payload.units_sold,
        kenp_pages=payload.kenp_pages,
        royalty_rate=payload.royalty_rate,
        period_month=payload.period_month,
        period_year=payload.period_year,
        payment_date=payload.payment_date,
        book_id=payload.book_id,
        pen_name_id=payload.pen_name_id,
        notes=payload.notes,
        source="manual",
    )
    db.add(entry)
    await db.flush()
    return entry


async def import_csv(
    db: AsyncSession,
    org_id: UUID,
    distributor: str,
    content: bytes,
) -> RoyaltyImportResult:
    result = importer.parse(distributor, content)
    batch_id = uuid.uuid4()
    imported = 0
    for row in result.rows:
        db.add(
            RoyaltyEntry(
                org_id=org_id,
                distributor=row.distributor,
                royalty_type=row.royalty_type,
                amount=row.amount,
                currency=row.currency,
                units_sold=row.units_sold,
                kenp_pages=row.kenp_pages,
                royalty_rate=row.royalty_rate,
                period_month=row.period_month,
                period_year=row.period_year,
                payment_date=row.payment_date,
                notes=row.notes,
                source="import",
                import_batch_id=batch_id,
            )
        )
        imported += 1
    await db.flush()
    return RoyaltyImportResult(
        imported=imported,
        skipped=result.skipped,
        distributor=distributor.lower(),
        import_batch_id=batch_id,
        errors=result.errors,
        total_amount=_q(result.total),
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_csv(statement: MonthlyStatement) -> str:
    buf = io.StringIO()
    buf.write("Month,KDP eBook,KDP Print,KU/KENP,Ingram,D2D,Other,Total\n")
    for r in statement.rows:
        buf.write(
            f"{r.label},{r.kdp_ebook},{r.kdp_print},{r.ku_kenp},"
            f"{r.ingram},{r.d2d},{r.other},{r.total}\n"
        )
    y = statement.ytd_totals
    buf.write(
        f"{y.label},{y.kdp_ebook},{y.kdp_print},{y.ku_kenp},"
        f"{y.ingram},{y.d2d},{y.other},{y.total}\n"
    )
    return buf.getvalue()


def export_pdf(statement: MonthlyStatement) -> bytes:
    """Render a minimal PDF of the monthly statement.

    Generates a valid single-page PDF using a hand-rolled PDF writer so we
    don't add a heavy new dependency. Adequate for "download the statement"
    use case; sophisticated typography is out of scope.
    """
    lines: list[str] = [
        f"Royalty Statement - {statement.year}",
        "",
        f"{'Month':<12}{'KDP eBook':>12}{'KDP Print':>12}{'KU/KENP':>10}"
        f"{'Ingram':>10}{'D2D':>10}{'Other':>10}{'Total':>12}",
    ]
    for r in statement.rows:
        lines.append(
            f"{r.label:<12}{str(r.kdp_ebook):>12}{str(r.kdp_print):>12}"
            f"{str(r.ku_kenp):>10}{str(r.ingram):>10}{str(r.d2d):>10}"
            f"{str(r.other):>10}{str(r.total):>12}"
        )
    y = statement.ytd_totals
    lines.append(
        f"{y.label:<12}{str(y.kdp_ebook):>12}{str(y.kdp_print):>12}"
        f"{str(y.ku_kenp):>10}{str(y.ingram):>10}{str(y.d2d):>10}"
        f"{str(y.other):>10}{str(y.total):>12}"
    )
    return _render_simple_pdf(lines)


def _render_simple_pdf(lines: list[str]) -> bytes:
    """Hand-build a minimal 1-page PDF with Courier text."""
    # Build a single content stream
    content_lines = ["BT", "/F1 9 Tf", "50 780 Td", "12 TL"]
    for i, raw in enumerate(lines):
        safe = raw.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            content_lines.append(f"({safe}) Tj")
        else:
            content_lines.append(f"T* ({safe}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    ]

    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode())
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_offset = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return bytes(out)
