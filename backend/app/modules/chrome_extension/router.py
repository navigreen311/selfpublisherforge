"""FastAPI router for the Chrome Extension API.

Endpoints:
    POST /api/v1/extension/extract        — Save extracted Amazon data
    GET  /api/v1/extension/quick-research  — Quick niche data for sidebar
    POST /api/v1/extension/clip            — Save clip to Knowledge Vault
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.chrome_extension import service
from app.modules.chrome_extension.schemas import (
    AmazonMarketplace,
    ClipSaveRequest,
    ClipSaveResponse,
    ExtractDataRequest,
    ExtractedDataResponse,
    QuickResearchQuery,
    QuickResearchResponse,
)
from shared.contracts.api import SuccessResponse

router = APIRouter(prefix="/extension", tags=["chrome-extension"])

# ---------------------------------------------------------------------------
# Placeholder dependency
# ---------------------------------------------------------------------------

_PLACEHOLDER_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


async def _get_org_id() -> UUID:
    """Return the current organisation ID (placeholder for auth)."""
    return _PLACEHOLDER_ORG_ID


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/extract",
    response_model=SuccessResponse[ExtractedDataResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Save extracted Amazon product data",
    description="Save product data extracted by the Chrome extension from an Amazon page.",
)
async def save_extracted_data(
    request: ExtractDataRequest,
    db: AsyncSession = Depends(get_db),
    org_id: UUID = Depends(_get_org_id),
):
    result = await service.save_extracted_data(db, org_id, request)
    return SuccessResponse(data=result)


@router.get(
    "/quick-research",
    response_model=SuccessResponse[QuickResearchResponse],
    summary="Quick niche research data for the extension sidebar",
    description="Return quick niche research data (competition, demand) for the extension sidebar.",
)
async def quick_research(
    asin: str | None = Query(None, min_length=10, max_length=10),
    keywords: list[str] = Query(default=[]),
    category: str | None = Query(None),
    marketplace: AmazonMarketplace = Query(AmazonMarketplace.US),
    db: AsyncSession = Depends(get_db),
    org_id: UUID = Depends(_get_org_id),
):
    query = QuickResearchQuery(
        asin=asin,
        keywords=keywords,
        category=category,
        marketplace=marketplace,
    )
    result = await service.get_quick_research(db, org_id, query)
    return SuccessResponse(data=result)


@router.post(
    "/clip",
    response_model=SuccessResponse[ClipSaveResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Save a clip to the Knowledge Vault",
    description="Save a text or image clip from the browser to the Knowledge Vault.",
)
async def save_clip(
    request: ClipSaveRequest,
    db: AsyncSession = Depends(get_db),
    org_id: UUID = Depends(_get_org_id),
):
    result = await service.save_clip(db, org_id, request)
    return SuccessResponse(data=result)
