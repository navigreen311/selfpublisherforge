"""API router for the KDP Failure-Proofing System.

Endpoints:
    POST /api/v1/publishing/validate           — Run full pre-flight validation
    POST /api/v1/publishing/validate/print      — Print file validation
    POST /api/v1/publishing/validate/ebook      — Ebook validation
    POST /api/v1/publishing/validate/cover      — Cover validation
    GET  /api/v1/publishing/validate/{id}/results — Get validation results
    POST /api/v1/publishing/compliance-scan      — Content compliance scan
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from app.modules.kdp_validation.schemas import (
    ComplianceScanRequest,
    CoverValidationRequest,
    EbookValidationRequest,
    FullValidationRequest,
    FullValidationResponse,
    PrintValidationRequest,
    ValidationResult,
)
from app.modules.kdp_validation.service import ValidationService

router = APIRouter(prefix="/publishing", tags=["kdp-validation"])

# Module-level service instance
_service = ValidationService()


def get_service() -> ValidationService:
    """Return the validation service instance."""
    return _service


# ------------------------------------------------------------------
# POST /validate — Full pre-flight validation
# ------------------------------------------------------------------


@router.post(
    "/validate",
    response_model=FullValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run full pre-flight validation",
    description=(
        "Runs all requested validations (print, ebook, cover, compliance) "
        "and returns aggregated results with an overall pass/fail status."
    ),
)
async def run_full_validation(
    request: FullValidationRequest,
) -> FullValidationResponse:
    service = get_service()
    return service.run_full_validation(request)


# ------------------------------------------------------------------
# POST /validate/print — Print file validation
# ------------------------------------------------------------------


@router.post(
    "/validate/print",
    response_model=ValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate print file",
    description="Validate margins, bleed, spine, fonts, DPI, color space, and page count.",
)
async def validate_print(
    request: PrintValidationRequest,
) -> ValidationResult:
    service = get_service()
    return service.validate_print(request)


# ------------------------------------------------------------------
# POST /validate/ebook — Ebook validation
# ------------------------------------------------------------------


@router.post(
    "/validate/ebook",
    response_model=ValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate ebook",
    description="Validate TOC, images, links, prohibited elements, font sizes, and file size.",
)
async def validate_ebook(
    request: EbookValidationRequest,
) -> ValidationResult:
    service = get_service()
    return service.validate_ebook(request)


# ------------------------------------------------------------------
# POST /validate/cover — Cover validation
# ------------------------------------------------------------------


@router.post(
    "/validate/cover",
    response_model=ValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate cover",
    description="Validate resolution, dimensions, safe zones, format, and color space.",
)
async def validate_cover(
    request: CoverValidationRequest,
) -> ValidationResult:
    service = get_service()
    return service.validate_cover(request)


# ------------------------------------------------------------------
# GET /validate/{id}/results — Retrieve stored results
# ------------------------------------------------------------------


@router.get(
    "/validate/{validation_id}/results",
    response_model=FullValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get validation results",
    description="Retrieve previously stored validation results by ID.",
)
async def get_validation_results(
    validation_id: uuid.UUID,
) -> FullValidationResponse:
    service = get_service()
    result = service.get_results(validation_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation results not found for id '{validation_id}'.",
        )
    return result


# ------------------------------------------------------------------
# POST /compliance-scan — Content compliance scan
# ------------------------------------------------------------------


@router.post(
    "/compliance-scan",
    response_model=ValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Run compliance scan",
    description="Scan title, description, keywords, and content for policy violations and trademarks.",
)
async def compliance_scan(
    request: ComplianceScanRequest,
) -> ValidationResult:
    service = get_service()
    return service.scan_compliance(request)
