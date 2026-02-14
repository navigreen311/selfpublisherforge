"""FastAPI router for the Cover Design Studio.

Endpoints:
    POST /api/v1/covers/generate            — Generate cover concept via AI
    GET  /api/v1/covers/templates            — List cover templates by genre
    POST /api/v1/covers/analyze-competitors  — Analyse competitor covers
    POST /api/v1/covers/{id}/variations      — Generate variations of a cover
    GET  /api/v1/covers/book/{book_id}       — List covers for a book
    DELETE /api/v1/covers/{id}               — Delete a cover
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import SuccessResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.cover_design import service
from app.modules.cover_design.schemas import (
    ABTestResponse,
    CompetitorAnalysisResponse,
    CompetitorCoverAnalysisRequest,
    CoverFormat,
    CoverGenerateRequest,
    CoverGenre,
    CoverListSortBy,
    CoverResponse,
    CoverTemplateResponse,
    CoverVariationRequest,
    CreateABTestRequest,
    EndABTestRequest,
    ExportRequest,
    ExportResponse,
    GenerationJobResponse,
    UpdateEditorStateRequest,
    VoteRequest,
    VoteResponse,
)

router = APIRouter(prefix="/covers", tags=["covers"])


@router.post(
    "/generate",
    response_model=SuccessResponse[CoverResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate a cover concept via AI",
    description="Generate an AI cover concept based on genre, title, and style preferences.",
)
async def generate_cover(
    request: CoverGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cover = await service.generate_cover(db, current_user["org_id"], request)
    return SuccessResponse(data=cover)


@router.get(
    "/templates",
    response_model=SuccessResponse[list[CoverTemplateResponse]],
    summary="List cover templates, optionally filtered by genre",
    description="List available cover design templates with optional genre filter.",
)
async def list_templates(
    genre: CoverGenre | None = Query(None, description="Filter templates by genre"),
):
    templates = await service.list_templates(genre)
    return SuccessResponse(data=templates)


@router.post(
    "/analyze-competitors",
    response_model=SuccessResponse[CompetitorAnalysisResponse],
    summary="Analyse competitor covers in a niche",
    description="Analyse competitor covers to identify trends, color palettes, and design patterns.",
)
async def analyze_competitors(
    request: CompetitorCoverAnalysisRequest,
):
    analysis = await service.analyze_competitors(request)
    return SuccessResponse(data=analysis)


@router.post(
    "/{cover_id}/variations",
    response_model=SuccessResponse[list[CoverResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Generate variations of an existing cover",
    description="Generate style or color variations of an existing cover design.",
)
async def create_variations(
    cover_id: UUID,
    request: CoverVariationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        variations = await service.create_variations(db, current_user["org_id"], cover_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return SuccessResponse(data=variations)


@router.get(
    "/book/{book_id}",
    response_model=SuccessResponse[list[CoverResponse]],
    summary="List covers for a specific book",
    description="List all cover designs associated with a specific book.",
)
async def list_covers_for_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    covers = await service.list_covers_for_book(db, current_user["org_id"], book_id)
    return SuccessResponse(data=covers)


@router.delete(
    "/{cover_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cover (soft-delete)",
    description="Soft-delete a cover design. The record is retained but hidden from listings.",
)
async def delete_cover(
    cover_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deleted = await service.delete_cover(db, current_user["org_id"], cover_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cover {cover_id} not found",
        )
    return


# ---------------------------------------------------------------------------
# Additional Cover CRUD Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=SuccessResponse[list[CoverResponse]],
    summary="List covers with optional filters",
)
async def list_covers_filtered(
    project_id: UUID | None = Query(None),
    format: str | None = Query(None),
    sort: str = Query("created_at"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    covers = await service.list_covers(
        db, current_user["org_id"],
        project_id=project_id,
        format_filter=format,
        sort_by=sort,
    )
    return SuccessResponse(data=covers)


@router.get(
    "/{cover_id}",
    response_model=SuccessResponse[CoverResponse],
    summary="Get a single cover by ID",
)
async def get_cover_by_id(
    cover_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cover = await service.get_cover_by_id(db, current_user["org_id"], cover_id)
    return SuccessResponse(data=cover)


@router.patch(
    "/{cover_id}",
    response_model=SuccessResponse[CoverResponse],
    summary="Update cover metadata",
)
async def update_cover_metadata(
    cover_id: UUID,
    updates: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cover = await service.update_cover(db, current_user["org_id"], cover_id, **updates)
    return SuccessResponse(data=cover)


# ---------------------------------------------------------------------------
# Generation Job Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/generate/{job_id}",
    response_model=SuccessResponse[dict],
    summary="Poll cover generation status",
)
async def get_generation_job_status(
    job_id: str,
):
    status_data = await service.get_generation_job_status(job_id)
    return SuccessResponse(data=status_data)


# ---------------------------------------------------------------------------
# Editor Endpoints
# ---------------------------------------------------------------------------


@router.patch(
    "/{cover_id}/editor-state",
    response_model=SuccessResponse[CoverResponse],
    summary="Update editor state",
)
async def update_editor_state(
    cover_id: UUID,
    request: UpdateEditorStateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cover = await service.update_editor_state(
        db, current_user["org_id"], cover_id,
        request.editor_state.model_dump(),
    )
    return SuccessResponse(data=cover)


@router.post(
    "/{cover_id}/export",
    response_model=SuccessResponse[dict],
    summary="Export cover",
)
async def export_cover_endpoint(
    cover_id: UUID,
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await service.export_cover(
        db, current_user["org_id"], cover_id,
        export_format=request.format.value,
        dpi=request.dpi,
        include_bleed=request.include_bleed,
        color_profile=request.color_profile,
    )
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Template Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/templates/{template_id}",
    response_model=SuccessResponse[CoverTemplateResponse],
    summary="Get template by ID",
)
async def get_template_by_id(
    template_id: str,
):
    templates = await service.list_templates()
    template = next((t for t in templates if t.id == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return SuccessResponse(data=template)


# ---------------------------------------------------------------------------
# Competitor Analysis (GET endpoint)
# ---------------------------------------------------------------------------


@router.get(
    "/competitor-analysis",
    response_model=SuccessResponse[CompetitorAnalysisResponse],
    summary="Get competitor analysis",
)
async def get_competitor_analysis(
    genre: CoverGenre = Query(...),
    subcategory: str | None = Query(None),
):
    niche_keywords = [subcategory] if subcategory else [genre.value]
    request = CompetitorCoverAnalysisRequest(
        genre=genre,
        niche_keywords=niche_keywords,
        max_results=10,
    )
    analysis = await service.analyze_competitors(request)
    return SuccessResponse(data=analysis)


# ---------------------------------------------------------------------------
# A/B Testing Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/ab-tests",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create A/B test",
)
async def create_ab_test_endpoint(
    request: CreateABTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ab_test = await service.create_ab_test(
        db, current_user["org_id"],
        name=request.name,
        description=request.description,
        cover_a_id=request.cover_a_id,
        cover_b_id=request.cover_b_id,
        target_audience=request.target_audience,
        duration_days=request.duration_days,
        public_url_enabled=request.public_url_enabled,
    )
    return SuccessResponse(data=ab_test)


@router.get(
    "/ab-tests",
    response_model=SuccessResponse[list],
    summary="List A/B tests",
)
async def list_ab_tests_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    tests = await service.list_ab_tests(db, current_user["org_id"])
    return SuccessResponse(data=tests)


@router.get(
    "/ab-tests/{test_id}",
    response_model=SuccessResponse[dict],
    summary="Get A/B test details",
)
async def get_ab_test_endpoint(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    test = await service.get_ab_test(db, test_id, current_user["org_id"])
    return SuccessResponse(data=test)


@router.post(
    "/ab-tests/{test_id}/vote",
    response_model=SuccessResponse[dict],
    summary="Vote on A/B test (PUBLIC)",
)
async def vote_on_ab_test_endpoint(
    test_id: UUID,
    request: VoteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint - no authentication required."""
    result = await service.vote_on_ab_test(
        db, test_id,
        choice=request.choice,
        voter_fingerprint=request.voter_fingerprint,
    )
    return SuccessResponse(data=result)


@router.patch(
    "/ab-tests/{test_id}/end",
    response_model=SuccessResponse[dict],
    summary="End A/B test",
)
async def end_ab_test_endpoint(
    test_id: UUID,
    request: EndABTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    test = await service.end_ab_test(
        db, current_user["org_id"], test_id,
        winner=request.winner,
        notes=request.notes,
    )
    return SuccessResponse(data=test)
