"""Service layer for the Tax module.

All monetary math uses ``Decimal``.
"""

from __future__ import annotations

import io
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.royalties.models import RoyaltyEntry
from app.modules.royalties.service import _render_simple_pdf
from app.modules.tax.schemas import (
    FilingStatus,
    IncomeSourceRow,
    QuarterlyEstimate,
    QuarterlyPaymentUpdate,
    TaxDashboard,
    TaxExpenseCreate,
    TaxExpenseOut,
    TaxExpenseUpdate,
)
from app.modules.royalties.models import (
    QuarterlyTaxPayment,
    TaxExpense,
)


_CENTS = Decimal("0.01")


def _q(v: Decimal) -> Decimal:
    return v.quantize(_CENTS, rounding=ROUND_HALF_UP)


DEFAULT_TAX_RATE = Decimal("0.25")
FORM_1099_THRESHOLD = Decimal("600")


_DISTRIBUTOR_LABELS = {
    "kdp": "Amazon KDP",
    "ingram": "IngramSpark",
    "d2d": "Draft2Digital",
}


_QUARTER_DUE_DATES = {
    1: (4, 15),   # Q1 due Apr 15
    2: (6, 15),   # Q2 due Jun 15
    3: (9, 15),   # Q3 due Sep 15
    4: (1, 15),   # Q4 due Jan 15 (next year)
}


def quarter_due_date(tax_year: int, quarter: int) -> date:
    month, day = _QUARTER_DUE_DATES[quarter]
    year = tax_year + 1 if quarter == 4 else tax_year
    return date(year, month, day)


# ---------------------------------------------------------------------------
# Expenses CRUD
# ---------------------------------------------------------------------------

async def list_expenses(
    db: AsyncSession, org_id: UUID, tax_year: int
) -> list[TaxExpense]:
    stmt = (
        select(TaxExpense)
        .where(and_(TaxExpense.org_id == org_id, TaxExpense.tax_year == tax_year))
        .order_by(TaxExpense.expense_date.desc().nullslast())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def create_expense(
    db: AsyncSession, org_id: UUID, payload: TaxExpenseCreate
) -> TaxExpense:
    expense = TaxExpense(
        org_id=org_id,
        category=payload.category,
        amount=payload.amount,
        description=payload.description,
        expense_date=payload.expense_date,
        tax_year=payload.tax_year,
        receipt_url=payload.receipt_url,
    )
    db.add(expense)
    await db.flush()
    return expense


async def update_expense(
    db: AsyncSession,
    org_id: UUID,
    expense_id: UUID,
    payload: TaxExpenseUpdate,
) -> TaxExpense | None:
    stmt = select(TaxExpense).where(
        and_(TaxExpense.id == expense_id, TaxExpense.org_id == org_id)
    )
    res = await db.execute(stmt)
    expense = res.scalar_one_or_none()
    if expense is None:
        return None
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(expense, field, val)
    await db.flush()
    return expense


async def delete_expense(
    db: AsyncSession, org_id: UUID, expense_id: UUID
) -> bool:
    stmt = select(TaxExpense).where(
        and_(TaxExpense.id == expense_id, TaxExpense.org_id == org_id)
    )
    res = await db.execute(stmt)
    expense = res.scalar_one_or_none()
    if expense is None:
        return False
    await db.delete(expense)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

async def _gross_income_by_distributor(
    db: AsyncSession, org_id: UUID, tax_year: int
) -> dict[str, Decimal]:
    stmt = select(RoyaltyEntry).where(
        and_(RoyaltyEntry.org_id == org_id, RoyaltyEntry.period_year == tax_year)
    )
    res = await db.execute(stmt)
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for e in res.scalars().all():
        totals[e.distributor] += e.amount
    return dict(totals)


async def _gross_income_by_quarter(
    db: AsyncSession, org_id: UUID, tax_year: int
) -> dict[int, Decimal]:
    stmt = select(RoyaltyEntry).where(
        and_(RoyaltyEntry.org_id == org_id, RoyaltyEntry.period_year == tax_year)
    )
    res = await db.execute(stmt)
    by_q: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    for e in res.scalars().all():
        if not e.period_month:
            continue
        q = (e.period_month - 1) // 3 + 1
        by_q[q] += e.amount
    return dict(by_q)


async def _expenses_by_quarter(
    db: AsyncSession, org_id: UUID, tax_year: int
) -> dict[int, Decimal]:
    expenses = await list_expenses(db, org_id, tax_year)
    by_q: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    for e in expenses:
        if e.expense_date:
            q = (e.expense_date.month - 1) // 3 + 1
        else:
            q = 1
        by_q[q] += e.amount
    return dict(by_q)


async def _ensure_quarterly_rows(
    db: AsyncSession, org_id: UUID, tax_year: int
) -> list[QuarterlyTaxPayment]:
    stmt = select(QuarterlyTaxPayment).where(
        and_(
            QuarterlyTaxPayment.org_id == org_id,
            QuarterlyTaxPayment.tax_year == tax_year,
        )
    )
    existing = {q.quarter: q for q in (await db.execute(stmt)).scalars().all()}
    created = False
    for q in (1, 2, 3, 4):
        if q not in existing:
            row = QuarterlyTaxPayment(
                org_id=org_id,
                tax_year=tax_year,
                quarter=q,
                due_date=quarter_due_date(tax_year, q),
                paid=False,
            )
            db.add(row)
            existing[q] = row
            created = True
    if created:
        await db.flush()
    return [existing[q] for q in (1, 2, 3, 4)]


async def get_dashboard(
    db: AsyncSession,
    org_id: UUID,
    tax_year: int,
    *,
    tax_rate: Decimal | None = None,
    filing_status: FilingStatus = FilingStatus.SINGLE,
) -> TaxDashboard:
    rate = tax_rate if tax_rate is not None else DEFAULT_TAX_RATE

    income_by_dist = await _gross_income_by_distributor(db, org_id, tax_year)
    gross = sum(income_by_dist.values(), Decimal("0"))

    expenses_list = await list_expenses(db, org_id, tax_year)
    total_expenses = sum((e.amount for e in expenses_list), Decimal("0"))

    net = max(gross - total_expenses, Decimal("0"))
    est_tax = net * rate

    income_by_q = await _gross_income_by_quarter(db, org_id, tax_year)
    exp_by_q = await _expenses_by_quarter(db, org_id, tax_year)

    rows = await _ensure_quarterly_rows(db, org_id, tax_year)

    estimates: list[QuarterlyEstimate] = []
    today = date.today()
    next_due: date | None = None
    quarter_labels = {
        1: "Q1 (Jan-Mar)",
        2: "Q2 (Apr-Jun)",
        3: "Q3 (Jul-Sep)",
        4: "Q4 (Oct-Dec)",
    }
    for row in rows:
        q_gross = income_by_q.get(row.quarter, Decimal("0"))
        q_expenses = exp_by_q.get(row.quarter, Decimal("0"))
        q_net = max(q_gross - q_expenses, Decimal("0"))
        q_est = _q(q_net * rate)
        row.estimated_amount = q_est
        estimates.append(
            QuarterlyEstimate(
                quarter=row.quarter,
                tax_year=tax_year,
                label=quarter_labels[row.quarter],
                due_date=row.due_date,
                estimated_amount=q_est,
                actual_amount=row.actual_amount,
                paid=row.paid,
                paid_date=row.paid_date,
            )
        )
        if not row.paid and row.due_date >= today and next_due is None:
            next_due = row.due_date
    await db.flush()

    income_rows = [
        IncomeSourceRow(
            source=_DISTRIBUTOR_LABELS.get(dist, dist.title()),
            amount=_q(amt),
            expects_1099=amt >= FORM_1099_THRESHOLD,
        )
        for dist, amt in sorted(income_by_dist.items(), key=lambda kv: -kv[1])
    ]

    return TaxDashboard(
        tax_year=tax_year,
        filing_status=filing_status,
        tax_rate=rate,
        gross_income=_q(gross),
        estimated_expenses=_q(total_expenses),
        net_income=_q(net),
        estimated_tax_owed=_q(est_tax),
        income_by_source=income_rows,
        quarterly_estimates=estimates,
        next_quarterly_due=next_due,
    )


async def update_quarterly_payment(
    db: AsyncSession,
    org_id: UUID,
    tax_year: int,
    quarter: int,
    payload: QuarterlyPaymentUpdate,
) -> QuarterlyTaxPayment | None:
    if quarter not in (1, 2, 3, 4):
        return None
    await _ensure_quarterly_rows(db, org_id, tax_year)
    stmt = select(QuarterlyTaxPayment).where(
        and_(
            QuarterlyTaxPayment.org_id == org_id,
            QuarterlyTaxPayment.tax_year == tax_year,
            QuarterlyTaxPayment.quarter == quarter,
        )
    )
    res = await db.execute(stmt)
    row = res.scalar_one_or_none()
    if row is None:
        return None
    row.paid = payload.paid
    if payload.paid_date is not None:
        row.paid_date = payload.paid_date
    elif payload.paid and row.paid_date is None:
        row.paid_date = date.today()
    if payload.actual_amount is not None:
        row.actual_amount = payload.actual_amount
    await db.flush()
    return row


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_csv(dashboard: TaxDashboard, expenses: list[TaxExpenseOut]) -> str:
    buf = io.StringIO()
    buf.write(f"Tax Year,{dashboard.tax_year}\n")
    buf.write(f"Filing Status,{dashboard.filing_status.value}\n")
    buf.write(f"Tax Rate,{dashboard.tax_rate}\n")
    buf.write("\nIncome by Source\n")
    buf.write("Source,Amount,1099 Expected\n")
    for r in dashboard.income_by_source:
        buf.write(f"{r.source},{r.amount},{'Yes' if r.expects_1099 else 'No'}\n")
    buf.write(f"Total Gross Income,{dashboard.gross_income}\n")
    buf.write("\nDeductible Expenses\n")
    buf.write("Category,Amount,Description,Date\n")
    for e in expenses:
        buf.write(
            f"{e.category},{e.amount},{(e.description or '').replace(',', ';')},"
            f"{e.expense_date or ''}\n"
        )
    buf.write(f"Total Expenses,{dashboard.estimated_expenses}\n")
    buf.write("\nNet Income,{}\n".format(dashboard.net_income))
    buf.write("Estimated Tax Owed,{}\n".format(dashboard.estimated_tax_owed))
    buf.write("\nQuarterly Estimated Payments\n")
    buf.write("Quarter,Due Date,Estimated,Actual,Paid\n")
    for q in dashboard.quarterly_estimates:
        buf.write(
            f"{q.label},{q.due_date},{q.estimated_amount},"
            f"{q.actual_amount or ''},{'Yes' if q.paid else 'No'}\n"
        )
    buf.write(f"\nDisclaimer,\"{dashboard.disclaimer}\"\n")
    return buf.getvalue()


def export_pdf(dashboard: TaxDashboard, expenses: list[TaxExpenseOut]) -> bytes:
    lines = [
        f"Year-End Tax Summary - {dashboard.tax_year}",
        "",
        f"Filing Status: {dashboard.filing_status.value}",
        f"Tax Rate: {dashboard.tax_rate}",
        "",
        f"Gross Income:          {dashboard.gross_income}",
        f"Total Expenses:        {dashboard.estimated_expenses}",
        f"Net Income:            {dashboard.net_income}",
        f"Estimated Tax Owed:    {dashboard.estimated_tax_owed}",
        "",
        "Income by Source:",
    ]
    for r in dashboard.income_by_source:
        lines.append(
            f"  {r.source:<20} {str(r.amount):>12} "
            f"{'1099' if r.expects_1099 else '    '}"
        )
    lines.append("")
    lines.append("Expenses:")
    for e in expenses:
        cat = (e.category or "")[:20]
        desc = (e.description or "")[:40]
        lines.append(f"  {cat:<22} {str(e.amount):>10}  {desc}")
    lines.append("")
    lines.append("Quarterly Estimates:")
    for q in dashboard.quarterly_estimates:
        paid = "PAID" if q.paid else "    "
        lines.append(
            f"  {q.label:<14} due {q.due_date} est {str(q.estimated_amount):>10} {paid}"
        )
    lines.append("")
    lines.append(dashboard.disclaimer)
    return _render_simple_pdf(lines)
