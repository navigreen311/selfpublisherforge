"""FastAPI router for the Tax module.

Endpoints (prefix /api/v1/tax):
  GET    /                          dashboard
  GET    /expenses                  list expenses
  POST   /expenses                  create expense
  PATCH  /expenses/{id}             update expense
  DELETE /expenses/{id}             delete expense
  PATCH  /quarterly-payment/{q}     mark paid
  GET    /export                    CSV or PDF year-end summary
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.tax import service
from app.modules.tax.schemas import (
    FilingStatus,
    QuarterlyPaymentUpdate,
    TaxDashboard,
    TaxExpenseCreate,
    TaxExpenseOut,
    TaxExpenseUpdate,
)

router = APIRouter()


@router.get("", response_model=TaxDashboard)
async def get_tax_dashboard(
    year: int = Query(...),
    tax_rate: Decimal | None = Query(None, ge=0, le=1),
    filing_status: FilingStatus = Query(FilingStatus.SINGLE),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TaxDashboard:
    return await service.get_dashboard(
        db,
        current_user["org_id"],
        year,
        tax_rate=tax_rate,
        filing_status=filing_status,
    )


@router.get("/expenses", response_model=list[TaxExpenseOut])
async def list_expenses(
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[TaxExpenseOut]:
    rows = await service.list_expenses(db, current_user["org_id"], year)
    return [TaxExpenseOut.model_validate(r) for r in rows]


@router.post(
    "/expenses",
    response_model=TaxExpenseOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_expense(
    payload: TaxExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TaxExpenseOut:
    row = await service.create_expense(db, current_user["org_id"], payload)
    return TaxExpenseOut.model_validate(row)


@router.patch("/expenses/{expense_id}", response_model=TaxExpenseOut)
async def update_expense(
    expense_id: UUID,
    payload: TaxExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TaxExpenseOut:
    row = await service.update_expense(db, current_user["org_id"], expense_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return TaxExpenseOut.model_validate(row)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    ok = await service.delete_expense(db, current_user["org_id"], expense_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Expense not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/quarterly-payment/{quarter}")
async def mark_quarterly_payment(
    quarter: int,
    payload: QuarterlyPaymentUpdate,
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    if quarter not in (1, 2, 3, 4):
        raise HTTPException(status_code=400, detail="Quarter must be 1-4")
    row = await service.update_quarterly_payment(
        db, current_user["org_id"], year, quarter, payload
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Quarterly row not found")
    return {
        "quarter": row.quarter,
        "tax_year": row.tax_year,
        "paid": row.paid,
        "paid_date": row.paid_date,
        "actual_amount": row.actual_amount,
        "estimated_amount": row.estimated_amount,
        "due_date": row.due_date,
    }


@router.get("/export")
async def export(
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    year: int = Query(...),
    tax_rate: Decimal | None = Query(None, ge=0, le=1),
    filing_status: FilingStatus = Query(FilingStatus.SINGLE),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    dashboard = await service.get_dashboard(
        db,
        current_user["org_id"],
        year,
        tax_rate=tax_rate,
        filing_status=filing_status,
    )
    expenses_rows = await service.list_expenses(db, current_user["org_id"], year)
    expenses = [TaxExpenseOut.model_validate(r) for r in expenses_rows]
    if format == "csv":
        data = service.export_csv(dashboard, expenses).encode("utf-8")
        return Response(
            content=data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="tax_{year}.csv"'
            },
        )
    data = service.export_pdf(dashboard, expenses)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="tax_{year}.pdf"'
        },
    )
