"""FastAPI router for Print Quality endpoints (/api/v1/specialty/).

Covers:
  - POST /pricing/calculate       - KDP print cost engine
  - POST /pricing/ink-coverage     - per-page ink coverage analysis
  - POST /color/soft-proof         - CMYK soft-proof simulation
  - POST /color/auto-adjust        - auto-fix gamut/ink/shadow issues
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user
from app.modules.specialty_books import service_print_quality as svc

router = APIRouter()


# -- Request / Response Schemas --------------------------------------------


class PrintCostRequest(BaseModel):
    page_count: int = Field(..., ge=1, le=1000)
    interior_type: str = Field(..., description="black_white, standard_color, or premium_color")
    trim_size: str = Field(..., description="e.g. 6x9, 8.5x11")
    marketplace: str = Field("us", max_length=10)
    ink_coverage_pct: float | None = Field(None, ge=0.0, le=100.0)
    category: str | None = Field(None, description="Category key for norm-based pricing")


class PrintCostResponse(BaseModel):
    base_cost: float
    ink_cost_adjustment: float
    total_cost: float
    scenarios: list[dict[str, Any]]
    recommended_price: float | None = None
    warnings: list[str] = Field(default_factory=list)
    page_count: int
    interior_type: str
    trim_size: str
    marketplace: str


class InkCoveragePageInput(BaseModel):
    page_num: int
    coverage_pct: float | None = Field(None, ge=0.0, le=100.0)
    pixel_data: list[int] | None = None


class InkCoverageRequest(BaseModel):
    pages: list[InkCoveragePageInput] = Field(..., min_length=1)


class InkCoveragePageResult(BaseModel):
    page_num: int
    coverage_pct: float
    heavy_warning: bool
    light_warning: bool


class InkCoverageResponse(BaseModel):
    per_page: list[InkCoveragePageResult]
    average: float
    max: float
    min: float


class PixelInput(BaseModel):
    page: int = 1
    x: int = 0
    y: int = 0
    r: int = Field(0, ge=0, le=255)
    g: int = Field(0, ge=0, le=255)
    b: int = Field(0, ge=0, le=255)


class SoftProofRequest(BaseModel):
    image_data: list[PixelInput] = Field(..., min_length=1)
    profile: str = Field("US_SWOP_v2", max_length=50)


class SoftProofResponse(BaseModel):
    cmyk_preview_url: str
    out_of_gamut_areas: list[dict[str, Any]] = Field(default_factory=list)
    shadow_crush_warnings: list[dict[str, Any]] = Field(default_factory=list)
    ink_density_issues: list[dict[str, Any]] = Field(default_factory=list)


class AutoAdjustRequest(BaseModel):
    image_data: list[PixelInput] = Field(..., min_length=1)


class AutoAdjustResponse(BaseModel):
    adjusted_pixels: list[dict[str, Any]]
    changes_log: list[dict[str, Any]]
    total_changes: int


# -- Endpoints -------------------------------------------------------------


@router.post(
    "/pricing/calculate",
    response_model=PrintCostResponse,
    summary="Calculate KDP print cost and pricing scenarios",
    status_code=status.HTTP_200_OK,
)
async def calculate_pricing(
    body: PrintCostRequest,
    user: dict = Depends(get_current_user),
) -> PrintCostResponse:
    result = svc.calculate_print_cost(
        page_count=body.page_count,
        interior_type=body.interior_type,
        trim_size=body.trim_size,
        marketplace=body.marketplace,
        ink_coverage_pct=body.ink_coverage_pct,
        category=body.category,
    )
    return PrintCostResponse(**result)


@router.post(
    "/pricing/ink-coverage",
    response_model=InkCoverageResponse,
    summary="Analyze ink coverage per page",
    status_code=status.HTTP_200_OK,
)
async def analyze_ink_coverage(
    body: InkCoverageRequest,
    user: dict = Depends(get_current_user),
) -> InkCoverageResponse:
    pages_data = [p.model_dump() for p in body.pages]
    result = svc.analyze_ink_coverage(pages_data)
    return InkCoverageResponse(**result)


@router.post(
    "/color/soft-proof",
    response_model=SoftProofResponse,
    summary="Generate CMYK soft-proof simulation",
    status_code=status.HTTP_200_OK,
)
async def soft_proof(
    body: SoftProofRequest,
    user: dict = Depends(get_current_user),
) -> SoftProofResponse:
    image_data = [p.model_dump() for p in body.image_data]
    result = svc.generate_soft_proof(image_data, profile=body.profile)
    return SoftProofResponse(**result)


@router.post(
    "/color/auto-adjust",
    response_model=AutoAdjustResponse,
    summary="Auto-fix gamut, ink density, and shadow crush issues",
    status_code=status.HTTP_200_OK,
)
async def auto_adjust(
    body: AutoAdjustRequest,
    user: dict = Depends(get_current_user),
) -> AutoAdjustResponse:
    image_data = [p.model_dump() for p in body.image_data]
    result = svc.auto_adjust_color(image_data)
    return AutoAdjustResponse(**result)
