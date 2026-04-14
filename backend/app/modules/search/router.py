"""Global search endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.search import service
from app.modules.search.schemas import SearchResponse

router = APIRouter()


@router.get(
    "",
    response_model=SearchResponse,
    summary="Global search",
    description=(
        "Aggregated search across projects, books, chapters, recipes, and "
        "reviews for the current organization."
    ),
)
async def search(
    q: str = Query(..., min_length=1, description="Search term"),
    types: str | None = Query(
        None,
        description=(
            "Comma-separated list of types to include "
            "(projects,books,recipes,chapters,reviews). Defaults to all."
        ),
    ),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    type_list: list[str] | None = None
    if types:
        type_list = [t.strip() for t in types.split(",") if t.strip()]
    return await service.search(db, current_user["org_id"], q, type_list)
