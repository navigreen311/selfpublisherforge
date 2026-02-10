"""FastAPI router for the Chrome Extension API.

Endpoints:
    GET  /api/v1/extension/version         — Current published extension version
    POST /api/v1/extension/extract         — Save extracted Amazon data
    GET  /api/v1/extension/quick-research  — Quick niche data for sidebar
    POST /api/v1/extension/clip            — Save clip to Knowledge Vault
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.chrome_extension import service
from app.modules.chrome_extension.constants import (
    EXTENSION_CHANGELOG,
    EXTENSION_MIN_VERSION,
    EXTENSION_UPDATE_URL,
    EXTENSION_VERSION,
)
from app.modules.chrome_extension.schemas import (
    AmazonMarketplace,
    ClipSaveRequest,
    ClipSaveResponse,
    ExtensionVersionResponse,
    ExtractDataRequest,
    ExtractedDataResponse,
    QuickResearchQuery,
    QuickResearchResponse,
)
from app.core.contracts import SuccessResponse

router = APIRouter(prefix="/extension", tags=["chrome-extension"])


@router.get(
    "/version",
    response_model=SuccessResponse[ExtensionVersionResponse],
    summary="Current published extension version",
    description="Returns the latest published extension version, minimum supported version, update URL, and changelog. No authentication required.",
)
async def get_extension_version():
    return SuccessResponse(
        data=ExtensionVersionResponse(
            version=EXTENSION_VERSION,
            min_version=EXTENSION_MIN_VERSION,
            update_url=EXTENSION_UPDATE_URL,
            changelog=EXTENSION_CHANGELOG,
        )
    )


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
    current_user: dict = Depends(get_current_user),
):
    result = await service.save_extracted_data(db, current_user["org_id"], request)
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
    current_user: dict = Depends(get_current_user),
):
    query = QuickResearchQuery(
        asin=asin,
        keywords=keywords,
        category=category,
        marketplace=marketplace,
    )
    result = await service.get_quick_research(db, current_user["org_id"], query)
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
    current_user: dict = Depends(get_current_user),
):
    result = await service.save_clip(db, current_user["org_id"], request)
    return SuccessResponse(data=result)
