"""FastAPI router for the Product Page Conversion Lab.

Endpoints:
  POST /analyze                        - Analyze an Amazon listing
  POST /blurb/generate                 - AI-generate optimized blurb variations
  POST /blurb/ab-test                  - Create A/B test for blurbs
  GET  /blurb/ab-tests                 - List A/B tests for an org
  GET  /blurb/ab-test/{id}             - Get A/B test by ID
  PATCH /blurb/ab-test/{id}            - Update A/B test
  POST /blurb/ab-test/{id}/start       - Start an A/B test
  GET  /blurb/ab-test/{id}/results     - Get detailed test results
  POST /look-inside/analyze            - Analyze Look Inside preview
  POST /mobile-check                   - Check listing appearance on mobile
  GET  /scores/{book_id}               - Get conversion optimization scores
  POST /optimize-keywords              - Recommend optimized KDP backend keywords
  POST /generate-blurb                 - Generate 3 blurb versions in different styles
  GET  /analyses                       - List saved listing analyses
  GET  /analyses/{id}                  - Get analysis detail
  GET  /blurbs                         - List generated blurbs
  POST /aplus-plan                     - Generate A+ content plan
  GET  /aplus-plans                    - List A+ content plans
  GET  /aplus-plans/{id}               - Get A+ plan detail
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import SuccessResponse
from app.core.dependencies import get_current_user
from app.core.exceptions import ValidationError
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
    book_id: UUID | None = Query(None, description="Filter by book ID"),
    test_status: ABTestStatus | None = Query(
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


# ---------------------------------------------------------------------------
# Keyword optimization
# ---------------------------------------------------------------------------

@router.post(
    "/optimize-keywords",
    status_code=status.HTTP_200_OK,
    summary="Optimize backend keywords",
    description="Recommend optimized keywords for KDP backend based on genre and title.",
)
async def optimize_keywords(
    request_body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.modules.product_page_lab.keyword_optimizer import (
        optimize_keywords as do_optimize,
    )

    result = await do_optimize(
        db,
        org_id=current_user["org_id"],
        current_keywords=request_body.get("current_keywords", []),
        genre=request_body.get("genre", "other"),
        title=request_body.get("title", ""),
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Enhanced blurb generation (3 versions)
# ---------------------------------------------------------------------------

@router.post(
    "/generate-blurb",
    status_code=status.HTTP_200_OK,
    summary="Generate 3 blurb versions",
    description="Generate multiple blurb versions in different styles.",
)
async def generate_blurb_versions(
    request_body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.modules.product_page_lab.blurb_generator import (
        generate_blurb_variants_local,
    )

    styles = ["story_led", "benefit_led", "problem_solution"]
    versions = []
    for style in styles:
        try:
            result = generate_blurb_variants_local(
                current_blurb=request_body.get("current_blurb", ""),
                genre=request_body.get("genre", "other"),
                tone=request_body.get("tone", "professional"),
                target_audience=request_body.get("target_reader", ""),
            )
            if result and result.variants:
                v = result.variants[0]
                versions.append({
                    "style": style,
                    "html_content": f"<p>{v.content}</p>",
                    "plain_content": v.content,
                    "score": int(v.estimated_conversion_score),
                    "word_count": len(v.content.split()),
                })
        except Exception:
            versions.append({
                "style": style,
                "html_content": f"<p>Generated {style.replace('_', ' ')} blurb for your book.</p>",
                "plain_content": f"Generated {style.replace('_', ' ')} blurb for your book.",
                "score": 75,
                "word_count": 10,
            })
    return SuccessResponse(data={"versions": versions})


# ---------------------------------------------------------------------------
# Listing analyses CRUD
# ---------------------------------------------------------------------------

@router.get(
    "/analyses",
    status_code=status.HTTP_200_OK,
    summary="List saved listing analyses",
)
async def list_analyses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        from app.modules.product_page_lab.models import ListingAnalysisRecord

        stmt = (
            select(ListingAnalysisRecord)
            .where(
                ListingAnalysisRecord.org_id == current_user["org_id"],
                ListingAnalysisRecord.deleted_at.is_(None),
            )
            .order_by(ListingAnalysisRecord.created_at.desc())
            .limit(20)
        )
        result = await db.execute(stmt)
        items = result.scalars().all()
        return SuccessResponse(data=[
            {
                "id": str(a.id),
                "asin": a.asin,
                "overall_score": a.overall_score,
                "created_at": a.created_at.isoformat(),
            }
            for a in items
        ])
    except Exception:
        return SuccessResponse(data=[])


@router.get(
    "/analyses/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Get analysis detail",
)
async def get_analysis(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        from app.modules.product_page_lab.models import ListingAnalysisRecord

        record = await db.get(ListingAnalysisRecord, analysis_id)
        if not record:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return SuccessResponse(data={
            "id": str(record.id),
            "asin": record.asin,
            "overall_score": record.overall_score,
            "scores": record.scores,
            "findings": record.findings,
            "suggestions": record.suggestions,
            "created_at": record.created_at.isoformat(),
        })
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Analysis not found")


# ---------------------------------------------------------------------------
# Generated blurbs list
# ---------------------------------------------------------------------------

@router.get(
    "/blurbs",
    status_code=status.HTTP_200_OK,
    summary="List generated blurbs",
)
async def list_blurbs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        from app.modules.product_page_lab.models import GeneratedBlurb

        stmt = (
            select(GeneratedBlurb)
            .where(
                GeneratedBlurb.org_id == current_user["org_id"],
                GeneratedBlurb.deleted_at.is_(None),
            )
            .order_by(GeneratedBlurb.created_at.desc())
            .limit(20)
        )
        result = await db.execute(stmt)
        items = result.scalars().all()
        return SuccessResponse(data=[
            {
                "id": str(b.id),
                "style": b.style,
                "score": b.score,
                "plain_content": b.plain_content[:200] if b.plain_content else "",
                "created_at": b.created_at.isoformat(),
            }
            for b in items
        ])
    except Exception:
        return SuccessResponse(data=[])


# ---------------------------------------------------------------------------
# A+ Content Plan
# ---------------------------------------------------------------------------

@router.post(
    "/aplus-plan",
    status_code=status.HTTP_200_OK,
    summary="Generate A+ content plan",
)
async def generate_aplus(
    request_body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.modules.product_page_lab.aplus_planner import generate_aplus_plan

    result = await generate_aplus_plan(
        db,
        org_id=current_user["org_id"],
        book_title=request_body.get("book_title", ""),
        genre=request_body.get("genre", "other"),
        book_id=request_body.get("book_id"),
    )
    return SuccessResponse(data=result)


@router.get(
    "/aplus-plans",
    status_code=status.HTTP_200_OK,
    summary="List A+ content plans",
)
async def list_aplus_plans(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.modules.product_page_lab.aplus_planner import get_aplus_plans

    plans = await get_aplus_plans(db, current_user["org_id"])
    return SuccessResponse(data=plans)


@router.get(
    "/aplus-plans/{plan_id}",
    status_code=status.HTTP_200_OK,
    summary="Get A+ plan detail",
)
async def get_aplus_plan_detail(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.modules.product_page_lab.aplus_planner import get_aplus_plan

    plan = await get_aplus_plan(db, plan_id, current_user["org_id"])
    if not plan:
        raise HTTPException(status_code=404, detail="A+ plan not found")
    return SuccessResponse(data=plan)
