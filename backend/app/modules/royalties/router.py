"""FastAPI router for the Royalties module.

Endpoints (prefix /api/v1/royalties):
  GET    /                         list royalty entries (filterable)
  GET    /by-distributor           dashboard breakdown by distributor
  GET    /monthly-statement        monthly statement table
  POST   /import                   upload distributor CSV
  POST   /manual-entry             create a single manual entry
  GET    /export                   export CSV or PDF

Authentication only — RBAC is Stream 1's concern.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.royalties import service
from app.modules.royalties.schemas import (
    MonthlyStatement,
    RoyaltyDashboard,
    RoyaltyEntryCreate,
    RoyaltyEntryOut,
    RoyaltyImportResult,
)

router = APIRouter()


@router.get("", response_model=list[RoyaltyEntryOut])
async def list_royalties(
    period: str = Query("ytd"),
    year: int | None = Query(None),
    month: int | None = Query(None),
    pen_name_id: UUID | None = Query(None),
    distributor: str | None = Query(None),
    limit: int = Query(500, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[RoyaltyEntryOut]:
    entries = await service.list_entries(
        db,
        current_user["org_id"],
        period=period,
        year=year,
        month=month,
        pen_name_id=pen_name_id,
        distributor=distributor,
        limit=limit,
    )
    return [RoyaltyEntryOut.model_validate(e) for e in entries]


@router.get("/by-distributor", response_model=RoyaltyDashboard)
async def by_distributor(
    year: int | None = Query(None),
    pen_name_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> RoyaltyDashboard:
    return await service.get_dashboard(
        db, current_user["org_id"], year=year, pen_name_id=pen_name_id
    )


@router.get("/monthly-statement", response_model=MonthlyStatement)
async def monthly_statement(
    year: int = Query(...),
    pen_name_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> MonthlyStatement:
    return await service.get_monthly_statement(
        db, current_user["org_id"], year, pen_name_id=pen_name_id
    )


@router.post(
    "/import",
    response_model=RoyaltyImportResult,
    status_code=status.HTTP_201_CREATED,
)
async def import_csv(
    file: UploadFile = File(...),
    distributor: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> RoyaltyImportResult:
    if distributor.lower() not in ("kdp", "ingram", "ingramspark", "d2d", "draft2digital"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported distributor: {distributor}",
        )
    content = await file.read()
    try:
        return await service.import_csv(db, current_user["org_id"], distributor, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/manual-entry",
    response_model=RoyaltyEntryOut,
    status_code=status.HTTP_201_CREATED,
)
async def manual_entry(
    payload: RoyaltyEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> RoyaltyEntryOut:
    entry = await service.create_manual_entry(db, current_user["org_id"], payload)
    return RoyaltyEntryOut.model_validate(entry)


@router.get("/export")
async def export(
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    year: int = Query(...),
    pen_name_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    statement = await service.get_monthly_statement(
        db, current_user["org_id"], year, pen_name_id=pen_name_id
    )
    if format == "csv":
        data = service.export_csv(statement).encode("utf-8")
        return Response(
            content=data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="royalties_{year}.csv"'
            },
        )
    data = service.export_pdf(statement)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="royalties_{year}.pdf"'
        },
    )
