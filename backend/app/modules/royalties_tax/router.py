"""FastAPI routers for Royalty Tracking & Tax Dashboard (Feature 3).

Endpoints:

* GET  /api/v1/royalties/summary
* GET  /api/v1/royalties/records
* GET  /api/v1/royalties/platform-breakdown
* GET  /api/v1/royalties/book-breakdown
* POST /api/v1/royalties/import
* GET  /api/v1/tax/documents
* GET  /api/v1/tax/documents/{id}/download
* POST /api/v1/tax/documents/generate
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.royalties_tax import service
from app.modules.royalties_tax.schemas import (
    BookBreakdown,
    PlatformBreakdown,
    RoyaltyImportOut,
    RoyaltyRecordList,
    RoyaltySummary,
    TaxDocumentGenerateRequest,
    TaxDocumentList,
    TaxDocumentOut,
)

royalties_router = APIRouter()
tax_router = APIRouter()


def _current_year() -> int:
    return datetime.now(timezone.utc).year


# ---------- Royalties ---------------------------------------------------


@royalties_router.get(
    "/summary",
    response_model=RoyaltySummary,
    summary="Get royalty summary KPIs",
)
async def get_summary(
    period: str = Query("ytd", pattern="^(ytd|month|quarter|year)$"),
    year: int = Query(default_factory=_current_year, ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> RoyaltySummary:
    data = await service.get_summary(db, current_user["org_id"], year=year, period=period)
    return RoyaltySummary(**data)


@royalties_router.get(
    "/records",
    response_model=RoyaltyRecordList,
    summary="List royalty records",
)
async def list_records(
    year: int | None = Query(None),
    platform: str | None = Query(None),
    book_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> RoyaltyRecordList:
    data = await service.list_records(
        db,
        current_user["org_id"],
        year=year,
        platform=platform,
        book_id=book_id,
        limit=limit,
        offset=offset,
    )
    return RoyaltyRecordList(**data)


@royalties_router.get(
    "/platform-breakdown",
    response_model=PlatformBreakdown,
    summary="Earnings grouped by distribution platform",
)
async def get_platform_breakdown(
    year: int = Query(default_factory=_current_year, ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PlatformBreakdown:
    data = await service.platform_breakdown(db, current_user["org_id"], year=year)
    return PlatformBreakdown(**data)


@royalties_router.get(
    "/book-breakdown",
    response_model=BookBreakdown,
    summary="Earnings grouped by book",
)
async def get_book_breakdown(
    year: int = Query(default_factory=_current_year, ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> BookBreakdown:
    data = await service.book_breakdown(db, current_user["org_id"], year=year)
    return BookBreakdown(**data)


@royalties_router.post(
    "/import",
    response_model=RoyaltyImportOut,
    summary="Import royalty CSV/XLSX from a distributor",
    status_code=status.HTTP_201_CREATED,
)
async def import_royalties(
    platform: str = Form(..., description="kdp | ingram | d2d | manual"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> RoyaltyImportOut:
    if platform not in {"kdp", "ingram", "d2d", "manual"}:
        raise HTTPException(status_code=400, detail="Invalid platform")
    content = await file.read()
    imp = await service.import_royalty_file(
        db,
        org_id=current_user["org_id"],
        user_id=current_user.get("user_id"),
        platform=platform,
        filename=file.filename or "",
        content=content,
    )
    return RoyaltyImportOut(
        id=imp.id,
        platform=imp.platform,
        status=imp.status,
        source_filename=imp.source_filename,
        records_processed=imp.records_processed,
        records_failed=imp.records_failed,
        total_amount=imp.total_amount,
        currency=imp.currency,
        imported_at=imp.imported_at,
    )


# ---------- Tax ---------------------------------------------------------


@tax_router.get(
    "/documents",
    response_model=TaxDocumentList,
    summary="List generated tax documents",
)
async def list_tax_documents(
    year: int | None = Query(None, ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TaxDocumentList:
    data = await service.list_tax_documents(db, current_user["org_id"], year=year)
    items = [
        TaxDocumentOut(
            id=d.id,
            tax_year=d.tax_year,
            document_type=d.document_type,
            platform=d.platform,
            title=d.title,
            status=d.status,
            format=d.format,
            gross_income=d.gross_income,
            total_expenses=d.total_expenses,
            estimated_tax=d.estimated_tax,
            file_size_bytes=d.file_size_bytes,
            generated_at=d.generated_at,
        )
        for d in data["items"]
    ]
    return TaxDocumentList(items=items, total=data["total"])


@tax_router.get(
    "/documents/{doc_id}/download",
    summary="Download a tax document",
)
async def download_tax_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    doc = await service.get_tax_document(db, current_user["org_id"], doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Tax document not found")

    body, content_type = service.render_tax_document_body(doc)
    ext = "csv" if (doc.format or "pdf").lower() == "csv" else "txt"
    filename = f"{doc.title.replace(' ', '_')}.{ext}"
    return Response(
        content=body,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@tax_router.post(
    "/documents/generate",
    response_model=TaxDocumentOut,
    summary="Generate a new tax document",
    status_code=status.HTTP_201_CREATED,
)
async def generate_tax_document(
    payload: TaxDocumentGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TaxDocumentOut:
    doc = await service.generate_tax_document(
        db,
        current_user["org_id"],
        tax_year=payload.tax_year,
        document_type=payload.document_type,
        platform=payload.platform,
        format=payload.format,
    )
    return TaxDocumentOut(
        id=doc.id,
        tax_year=doc.tax_year,
        document_type=doc.document_type,
        platform=doc.platform,
        title=doc.title,
        status=doc.status,
        format=doc.format,
        gross_income=doc.gross_income,
        total_expenses=doc.total_expenses,
        estimated_tax=doc.estimated_tax,
        file_size_bytes=doc.file_size_bytes,
        generated_at=doc.generated_at,
    )
