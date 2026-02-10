"""FastAPI router for the Product Page Conversion Lab.

Endpoints:
  POST /analyze                        - Analyze an Amazon listing
  POST /blurb/generate                 - AI-generate optimized blurb variations
  POST /blurb/ab-test                  - Create A/B test for blurbs
  GET  /blurb/ab-test                  - List A/B tests for an org
  GET  /blurb/ab-test/{id}             - Get A/B test by ID
  PATCH /blurb/ab-test/{id}            - Update A/B test
  POST /blurb/ab-test/{id}/start       - Start an A/B test
  GET  /blurb/ab-test/{id}/results     - Get detailed test results
  POST /look-inside/analyze            - Analyze Look Inside preview
  POST /mobile-check                   - Check listing appearance on mobile
  GET  /scores/{book_id}               - Get conversion optimization scores
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.product_page_lab import service
from app.modules.product_page_lab.schemas import (
    ABTestCreateRequest,
    ABTestResponse,
    ABTestResultsResponse,
    ABTestStatus,
    ABTestUpdateRequest,
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
from app.core.exceptions import ValidationError
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
        raise ValidationError(
            message="Either 'asin' or 'url' must be provided.",
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
    current_user: dict = Depends(get_current_user),
) -> SuccessResponse[ABTestResponse]:
    result = await service.create_ab_test(request, current_user["org_id"], db)
    return SuccessResponse(data=result)


@router.get(
    "/blurb/ab-tests",
    response_model=SuccessResponse[list[ABTestResponse]],
    status_code=status.HTTP_200_OK,
    summary="List A/B tests",
    description="List A/B tests for the current organisation with optional filters.",
)
async def list_ab_tests(
    book_id: Optional[UUID] = Query(None, description="Filter by book ID"),
    test_status: Optional[ABTestStatus] = Query(
        None, alias="status", description="Filter by test status"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> SuccessResponse[list[ABTestResponse]]:
    results = await service.list_ab_tests(current_user["org_id"], db, book_id=book_id, status=test_status)
    return SuccessResponse(data=results)


@router.get(
    "/blurb/ab-test/{test_id}",
    response_model=SuccessResponse[ABTestResponse],
    status_code=status.HTTP_200_OK,
    summary="Get A/B test",
    description="Retrieve A/B test configuration and results by ID.",
)
async def get_ab_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[ABTestResponse]:
    result = await service.get_ab_test(test_id, db)
    return SuccessResponse(data=result)


@router.patch(
    "/blurb/ab-test/{test_id}",
    response_model=SuccessResponse[ABTestResponse],
    status_code=status.HTTP_200_OK,
    summary="Update A/B test",
    description="Update an existing A/B test (name, variants, duration, status).",
)
async def update_ab_test(
    test_id: UUID,
    request: ABTestUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[ABTestResponse]:
    result = await service.update_ab_test(test_id, request, db)
    return SuccessResponse(data=result)


@router.post(
    "/blurb/ab-test/{test_id}/start",
    response_model=SuccessResponse[ABTestResponse],
    status_code=status.HTTP_200_OK,
    summary="Start A/B test",
    description="Start a DRAFT or PAUSED A/B test.",
)
async def start_ab_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[ABTestResponse]:
    result = await service.start_ab_test(test_id, db)
    return SuccessResponse(data=result)


@router.get(
    "/blurb/ab-test/{test_id}/results",
    response_model=SuccessResponse[ABTestResultsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get A/B test results",
    description="Retrieve detailed A/B test results with statistical significance analysis.",
)
async def get_ab_test_results(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[ABTestResultsResponse]:
    result = await service.get_test_results(test_id, db)
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
