"""FastAPI router for bulk operations (Feature 6B).

Mounted under /api/v1/books so the canonical endpoint is POST /api/v1/books/bulk.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.bulk_ops import service
from app.modules.bulk_ops.schemas import BulkActionRequest, BulkActionResponse

router = APIRouter()


@router.post(
    "/bulk",
    summary="Bulk operation on books",
    description=(
        "Run a bulk action against a set of book IDs. "
        "Supported actions: archive, delete, change_price, add_tags, "
        "export_metadata_csv. Only books whose parent project belongs to "
        "the caller's organization are affected."
    ),
)
async def bulk_action(
    body: BulkActionRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dispatch the requested bulk action."""
    org_id = current_user["org_id"]
    action = body.action
    book_ids = body.book_ids
    params = body.params or {}

    if action == "archive":
        affected, skipped = await service.bulk_archive(db, book_ids, org_id)
        return BulkActionResponse(
            action=action,
            requested=len(book_ids),
            affected=affected,
            skipped_ids=skipped,
        )

    if action == "delete":
        affected, skipped = await service.bulk_delete(db, book_ids, org_id)
        return BulkActionResponse(
            action=action,
            requested=len(book_ids),
            affected=affected,
            skipped_ids=skipped,
        )

    if action == "change_price":
        price = params.get("price")
        if price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="params.price is required for change_price",
            )
        try:
            price_f = float(price)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="params.price must be a number",
            ) from None
        if price_f < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="params.price must be non-negative",
            )
        affected, skipped = await service.bulk_change_price(
            db, book_ids, org_id, price_f
        )
        return BulkActionResponse(
            action=action,
            requested=len(book_ids),
            affected=affected,
            skipped_ids=skipped,
        )

    if action == "add_tags":
        tags = params.get("tags")
        if not isinstance(tags, list) or not tags:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="params.tags must be a non-empty list of strings",
            )
        affected, skipped = await service.bulk_add_tags(
            db, book_ids, org_id, [str(t) for t in tags]
        )
        return BulkActionResponse(
            action=action,
            requested=len(book_ids),
            affected=affected,
            skipped_ids=skipped,
        )

    if action == "export_metadata_csv":
        csv_text = await service.export_metadata_csv(db, book_ids, org_id)
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="books_metadata.csv"',
            },
        )

    # Pydantic validates the pattern, but fall through defensively.
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unknown action: {action}",
    )
