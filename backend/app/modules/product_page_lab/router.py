"""FastAPI router for the Product Page Conversion Lab.

Endpoints:
  POST /analyze                  - Analyze an Amazon listing
  POST /blurb/generate           - AI-generate optimized blurb variations
  POST /blurb/ab-test            - Create A/B test for blurbs
  GET  /blurb/ab-test/{id}       - Get A/B test results
  POST /look-inside/analyze      - Analyze Look Inside preview
  POST /mobile-check             - Check listing appearance on mobile
  GET  /scores/{book_id}         - Get conversion optimization scores
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.product_page_lab import service
from app.modules.product_page_lab.schemas import (
    ABTestCreateRequest,
    ABTestResponse,
    BlurbGenerateRequest,
    BlurbGenerateResponse,
    ConversionScores,
    ListingAnalysis,
    ListingAnalyzeRequest,
    LookInsideAnalysis,
    LookInsideAnalyzeRequest,
    MobileCheckRequest,
    MobileCheckResult,
)
from shared.contracts.api import SuccessResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Listing analysis
# ---------------------------------------------------------------------------

@router.post(
    "/analyze",
    response_model=SuccessResponse[ListingAnalysis],
    status_code=status.HTTP_200_OK,
    summary="Analyze an Amazon listing",
    description="Analyze an Amazon listing by ASIN or URL for conversion optimization.",
)
async def analyze_listing(
    request: ListingAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[ListingAnalysis]:
    if not request.asin and not request.url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either 'asin' or 'url' must be provided.",
        )
    analysis = await service.analyze_amazon_listing(request, db)
    return SuccessResponse(data=analysis)


# ---------------------------------------------------------------------------
# Blurb generation
# ---------------------------------------------------------------------------

@router.post(
    "/blurb/generate",
    response_model=SuccessResponse[BlurbGenerateResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate optimized blurb variations",
    description="AI-generate optimized blurb variations for a book listing.",
)
async def generate_blurb(
    request: BlurbGenerateRequest,
) -> SuccessResponse[BlurbGenerateResponse]:
    result = await service.generate_blurb_variants(request)
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# A/B testing
# ---------------------------------------------------------------------------

@router.post(
    "/blurb/ab-test",
    response_model=SuccessResponse[ABTestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create A/B test for blurbs",
    description="Create a new A/B test comparing two blurb variants.",
)
async def create_ab_test(
    request: ABTestCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[ABTestResponse]:
    # In production, org_id would come from the authenticated user
    from uuid import uuid4
    org_id = uuid4()  # Placeholder until auth is wired
    result = await service.create_ab_test(request, org_id, db)
    return SuccessResponse(data=result)


@router.get(
    "/blurb/ab-test/{test_id}",
    response_model=SuccessResponse[ABTestResponse],
    status_code=status.HTTP_200_OK,
    summary="Get A/B test results",
    description="Retrieve A/B test configuration and results by ID.",
)
async def get_ab_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[ABTestResponse]:
    result = await service.get_ab_test(test_id, db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found.",
        )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Look Inside analysis
# ---------------------------------------------------------------------------

@router.post(
    "/look-inside/analyze",
    response_model=SuccessResponse[LookInsideAnalysis],
    status_code=status.HTTP_200_OK,
    summary="Analyze Look Inside preview",
    description="Analyze the effectiveness of a book's Look Inside preview.",
)
async def analyze_look_inside(
    request: LookInsideAnalyzeRequest,
) -> SuccessResponse[LookInsideAnalysis]:
    result = await service.analyze_look_inside(request)
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Mobile check
# ---------------------------------------------------------------------------

@router.post(
    "/mobile-check",
    response_model=SuccessResponse[MobileCheckResult],
    status_code=status.HTTP_200_OK,
    summary="Check listing on mobile",
    description="Simulate how a book listing appears on mobile devices.",
)
async def mobile_check(
    request: MobileCheckRequest,
) -> SuccessResponse[MobileCheckResult]:
    result = await service.check_mobile_listing(request)
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Conversion scores
# ---------------------------------------------------------------------------

@router.get(
    "/scores/{book_id}",
    response_model=SuccessResponse[ConversionScores],
    status_code=status.HTTP_200_OK,
    summary="Get conversion optimization scores",
    description="Get aggregate conversion optimization scores for a book.",
)
async def get_scores(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[ConversionScores]:
    result = await service.get_conversion_scores(book_id, db)
    return SuccessResponse(data=result)
