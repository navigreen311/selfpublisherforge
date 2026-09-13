"""Unit tests for the KDP Validation service layer.

Tests validation orchestration, individual validators, result aggregation,
and result storage/retrieval.
"""

import uuid
from unittest.mock import patch

from app.modules.kdp_validation.schemas import (
    ComplianceScanRequest,
    CoverValidationRequest,
    EbookValidationRequest,
    FullValidationRequest,
    PrintValidationRequest,
    Severity,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
    ValidationType,
)
from app.modules.kdp_validation.service import ValidationService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_validation_result(
    validation_type: ValidationType = ValidationType.PRINT,
    status: ValidationStatus = ValidationStatus.PASSED,
    issues: list[ValidationIssue] | None = None,
) -> ValidationResult:
    """Create a mock validation result."""
    return ValidationResult(
        validation_type=validation_type,
        status=status,
        issues=issues or [],
        metadata={},
    )


def make_issue(
    rule: str = "TEST_ERROR",
    message: str = "Test error message",
    severity: Severity = Severity.ERROR,
) -> ValidationIssue:
    """Create a validation issue."""
    return ValidationIssue(
        rule=rule,
        message=message,
        severity=severity,
        location=None,
        details=None,
    )


def make_print_request(**overrides) -> PrintValidationRequest:
    """A valid print-validation request; override only what a test cares about."""
    payload = {
        "trim_size": "6x9",
        "page_count": 200,
        "paper_type": "white",
        "inside_margin": 0.75,
        "outside_margin": 0.5,
        "top_margin": 0.5,
        "bottom_margin": 0.5,
    }
    payload.update(overrides)
    return PrintValidationRequest(**payload)


def make_cover_request(**overrides) -> CoverValidationRequest:
    """A valid cover-validation request."""
    payload = {
        "cover_type": "print",
        "width_inches": 12.5,
        "height_inches": 9.25,
        "dpi": 300,
        "file_format": "TIFF",
        "color_space": "CMYK",
        "trim_size": "6x9",
        "page_count": 200,
    }
    payload.update(overrides)
    return CoverValidationRequest(**payload)


def make_ebook_request(**overrides) -> EbookValidationRequest:
    """A valid ebook-validation request."""
    payload = {"has_ncx_toc": True, "has_html_toc": True}
    payload.update(overrides)
    return EbookValidationRequest(**payload)


def make_compliance_request(**overrides) -> ComplianceScanRequest:
    """A valid compliance-scan request."""
    payload = {"title": "Sample Book", "description": "Sample description"}
    payload.update(overrides)
    return ComplianceScanRequest(**payload)


# ---------------------------------------------------------------------------
# Full validation tests
# ---------------------------------------------------------------------------


class TestRunFullValidation:
    def test_full_validation_all_passed(self):
        """Should aggregate results from all validators when all pass."""
        service = ValidationService()

        with (
            patch.object(service.print_validator, "validate") as mock_print,
            patch.object(service.ebook_validator, "validate") as mock_ebook,
            patch.object(service.cover_validator, "validate") as mock_cover,
            patch.object(service.compliance_scanner, "scan") as mock_compliance,
        ):
            mock_print.return_value = make_validation_result(ValidationType.PRINT)
            mock_ebook.return_value = make_validation_result(ValidationType.EBOOK)
            mock_cover.return_value = make_validation_result(ValidationType.COVER)
            mock_compliance.return_value = make_validation_result(ValidationType.COMPLIANCE)

            request = FullValidationRequest(
                print_validation=make_print_request(),
                ebook_validation=make_ebook_request(),
                cover_validation=make_cover_request(),
                compliance_scan=make_compliance_request(),
            )

            result = service.run_full_validation(request)

        assert result.overall_status == ValidationStatus.PASSED
        assert len(result.results) == 4
        assert result.total_errors == 0
        assert result.total_warnings == 0

    def test_full_validation_with_errors(self):
        """Should aggregate errors and set overall status to FAILED."""
        service = ValidationService()

        with (
            patch.object(service.print_validator, "validate") as mock_print,
            patch.object(service.ebook_validator, "validate") as mock_ebook,
        ):
            mock_print.return_value = make_validation_result(
                ValidationType.PRINT,
                ValidationStatus.FAILED,
                [make_issue("INVALID_TRIM", "Invalid trim size", Severity.ERROR)],
            )
            mock_ebook.return_value = make_validation_result(
                ValidationType.EBOOK,
                ValidationStatus.PASSED,
            )

            request = FullValidationRequest(
                print_validation=make_print_request(),
                ebook_validation=make_ebook_request(),
            )

            result = service.run_full_validation(request)

        assert result.overall_status == ValidationStatus.FAILED
        assert result.total_errors == 1
        assert result.total_warnings == 0

    def test_full_validation_with_warnings(self):
        """Should aggregate warnings and set overall status to WARNINGS."""
        service = ValidationService()

        with patch.object(service.cover_validator, "validate") as mock_cover:
            mock_cover.return_value = make_validation_result(
                ValidationType.COVER,
                ValidationStatus.WARNINGS,
                [make_issue("LOW_RES", "Cover resolution is low", Severity.WARNING)],
            )

            request = FullValidationRequest(
                cover_validation=make_cover_request(),
            )

            result = service.run_full_validation(request)

        assert result.overall_status == ValidationStatus.WARNINGS
        assert result.total_errors == 0
        assert result.total_warnings == 1

    def test_full_validation_stores_results(self):
        """Should store results for later retrieval."""
        service = ValidationService()

        with patch.object(service.print_validator, "validate") as mock_print:
            mock_print.return_value = make_validation_result(ValidationType.PRINT)

            request = FullValidationRequest(
                print_validation=make_print_request(),
            )

            result = service.run_full_validation(request)

        # Should be able to retrieve by ID
        retrieved = service.get_results(result.id)
        assert retrieved is not None
        assert retrieved.id == result.id


# ---------------------------------------------------------------------------
# Individual validation tests
# ---------------------------------------------------------------------------


class TestValidatePrint:
    def test_validate_print_delegates_to_validator(self):
        """Should delegate to PrintValidator."""
        service = ValidationService()

        request = make_print_request()

        with patch.object(service.print_validator, "validate") as mock_validate:
            mock_validate.return_value = make_validation_result(ValidationType.PRINT)

            result = service.validate_print(request)

        mock_validate.assert_called_once_with(request)
        assert result.validation_type == ValidationType.PRINT


class TestValidateEbook:
    def test_validate_ebook_delegates_to_validator(self):
        """Should delegate to EbookValidator."""
        service = ValidationService()

        request = make_ebook_request()

        with patch.object(service.ebook_validator, "validate") as mock_validate:
            mock_validate.return_value = make_validation_result(ValidationType.EBOOK)

            result = service.validate_ebook(request)

        mock_validate.assert_called_once_with(request)
        assert result.validation_type == ValidationType.EBOOK


class TestValidateCover:
    def test_validate_cover_delegates_to_validator(self):
        """Should delegate to CoverValidator."""
        service = ValidationService()

        request = make_cover_request()

        with patch.object(service.cover_validator, "validate") as mock_validate:
            mock_validate.return_value = make_validation_result(ValidationType.COVER)

            result = service.validate_cover(request)

        mock_validate.assert_called_once_with(request)
        assert result.validation_type == ValidationType.COVER


class TestScanCompliance:
    def test_scan_compliance_delegates_to_scanner(self):
        """Should delegate to ComplianceScanner."""
        service = ValidationService()

        request = make_compliance_request()

        with patch.object(service.compliance_scanner, "scan") as mock_scan:
            mock_scan.return_value = make_validation_result(ValidationType.COMPLIANCE)

            result = service.scan_compliance(request)

        mock_scan.assert_called_once_with(request)
        assert result.validation_type == ValidationType.COMPLIANCE


# ---------------------------------------------------------------------------
# Result retrieval tests
# ---------------------------------------------------------------------------


class TestGetResults:
    def test_get_results_existing(self):
        """Should retrieve stored validation results by ID."""
        service = ValidationService()

        with patch.object(service.print_validator, "validate") as mock_print:
            mock_print.return_value = make_validation_result(ValidationType.PRINT)

            request = FullValidationRequest(
                print_validation=make_print_request(),
            )

            result = service.run_full_validation(request)
            validation_id = result.id

        retrieved = service.get_results(validation_id)
        assert retrieved is not None
        assert retrieved.id == validation_id

    def test_get_results_not_found(self):
        """Should return None if validation ID not found."""
        service = ValidationService()
        result = service.get_results(uuid.uuid4())
        assert result is None


# ---------------------------------------------------------------------------
# Status aggregation tests
# ---------------------------------------------------------------------------


class TestAggregateStatus:
    def test_aggregate_empty_results(self):
        """Should return PASSED for empty results."""
        status = ValidationService._aggregate_status([])
        assert status == ValidationStatus.PASSED

    def test_aggregate_all_passed(self):
        """Should return PASSED when all validators passed."""
        results = [
            make_validation_result(ValidationType.PRINT, ValidationStatus.PASSED),
            make_validation_result(ValidationType.EBOOK, ValidationStatus.PASSED),
        ]
        status = ValidationService._aggregate_status(results)
        assert status == ValidationStatus.PASSED

    def test_aggregate_any_failed(self):
        """Should return FAILED if any validator failed."""
        results = [
            make_validation_result(ValidationType.PRINT, ValidationStatus.PASSED),
            make_validation_result(ValidationType.EBOOK, ValidationStatus.FAILED),
            make_validation_result(ValidationType.COVER, ValidationStatus.WARNINGS),
        ]
        status = ValidationService._aggregate_status(results)
        assert status == ValidationStatus.FAILED

    def test_aggregate_warnings_only(self):
        """Should return WARNINGS if no failures but has warnings."""
        results = [
            make_validation_result(ValidationType.PRINT, ValidationStatus.PASSED),
            make_validation_result(ValidationType.EBOOK, ValidationStatus.WARNINGS),
        ]
        status = ValidationService._aggregate_status(results)
        assert status == ValidationStatus.WARNINGS


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_validation_with_no_validators_selected(self):
        """Should handle validation request with no validators enabled."""
        service = ValidationService()
        request = FullValidationRequest()

        result = service.run_full_validation(request)

        assert result.overall_status == ValidationStatus.PASSED
        assert len(result.results) == 0
        assert result.total_errors == 0
        assert result.total_warnings == 0

    def test_multiple_errors_and_warnings(self):
        """Should correctly count multiple errors and warnings."""
        service = ValidationService()

        with (
            patch.object(service.print_validator, "validate") as mock_print,
            patch.object(service.ebook_validator, "validate") as mock_ebook,
        ):
            mock_print.return_value = make_validation_result(
                ValidationType.PRINT,
                ValidationStatus.FAILED,
                [
                    make_issue("ERR1", "Error 1", Severity.ERROR),
                    make_issue("ERR2", "Error 2", Severity.ERROR),
                    make_issue("WARN1", "Warning 1", Severity.WARNING),
                ],
            )
            mock_ebook.return_value = make_validation_result(
                ValidationType.EBOOK,
                ValidationStatus.WARNINGS,
                [
                    make_issue("WARN2", "Warning 2", Severity.WARNING),
                ],
            )

            request = FullValidationRequest(
                print_validation=make_print_request(),
                ebook_validation=make_ebook_request(),
            )

            result = service.run_full_validation(request)

        assert result.total_errors == 2
        assert result.total_warnings == 2
