"""KDP Validation Service — orchestrates the validation pipeline.

Coordinates print, ebook, cover, and compliance validators, aggregates
results, and manages validation lifecycle (store / retrieve results).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.modules.kdp_validation.compliance_scanner import ComplianceScanner
from app.modules.kdp_validation.cover_validator import CoverValidator
from app.modules.kdp_validation.ebook_validator import EbookValidator
from app.modules.kdp_validation.print_validator import PrintValidator
from app.modules.kdp_validation.schemas import (
    ComplianceScanRequest,
    CoverValidationRequest,
    EbookValidationRequest,
    FullValidationRequest,
    FullValidationResponse,
    PrintValidationRequest,
    Severity,
    ValidationResult,
    ValidationResultResponse,
    ValidationStatus,
)


class ValidationService:
    """Orchestrates KDP validation and manages results."""

    def __init__(self) -> None:
        self.print_validator = PrintValidator()
        self.ebook_validator = EbookValidator()
        self.cover_validator = CoverValidator()
        self.compliance_scanner = ComplianceScanner()
        # In-memory store for validation results (replace with DB in production)
        self._results_store: dict[uuid.UUID, FullValidationResponse] = {}

    # ------------------------------------------------------------------
    # Full validation
    # ------------------------------------------------------------------

    def run_full_validation(self, request: FullValidationRequest) -> FullValidationResponse:
        """Run all requested validations and return aggregated response."""
        results: list[ValidationResult] = []

        if request.print_validation is not None:
            results.append(self.validate_print(request.print_validation))

        if request.ebook_validation is not None:
            results.append(self.validate_ebook(request.ebook_validation))

        if request.cover_validation is not None:
            results.append(self.validate_cover(request.cover_validation))

        if request.compliance_scan is not None:
            results.append(self.scan_compliance(request.compliance_scan))

        total_errors = sum(
            sum(1 for i in r.issues if i.severity == Severity.ERROR)
            for r in results
        )
        total_warnings = sum(
            sum(1 for i in r.issues if i.severity == Severity.WARNING)
            for r in results
        )

        overall_status = self._aggregate_status(results)

        response = FullValidationResponse(
            overall_status=overall_status,
            results=results,
            total_errors=total_errors,
            total_warnings=total_warnings,
        )

        # Persist in store
        self._results_store[response.id] = response

        return response

    # ------------------------------------------------------------------
    # Individual validations
    # ------------------------------------------------------------------

    def validate_print(self, request: PrintValidationRequest) -> ValidationResult:
        """Run print validation only."""
        return self.print_validator.validate(request)

    def validate_ebook(self, request: EbookValidationRequest) -> ValidationResult:
        """Run ebook validation only."""
        return self.ebook_validator.validate(request)

    def validate_cover(self, request: CoverValidationRequest) -> ValidationResult:
        """Run cover validation only."""
        return self.cover_validator.validate(request)

    def scan_compliance(self, request: ComplianceScanRequest) -> ValidationResult:
        """Run compliance scan only."""
        return self.compliance_scanner.scan(request)

    # ------------------------------------------------------------------
    # Result retrieval
    # ------------------------------------------------------------------

    def get_results(self, validation_id: uuid.UUID) -> FullValidationResponse | None:
        """Retrieve stored validation results by ID."""
        return self._results_store.get(validation_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate_status(results: list[ValidationResult]) -> ValidationStatus:
        """Determine overall status from individual validation results."""
        if not results:
            return ValidationStatus.PASSED

        if any(r.status == ValidationStatus.FAILED for r in results):
            return ValidationStatus.FAILED
        if any(r.status == ValidationStatus.WARNINGS for r in results):
            return ValidationStatus.WARNINGS
        return ValidationStatus.PASSED
