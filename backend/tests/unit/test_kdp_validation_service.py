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
)
from app.modules.kdp_validation.service import ValidationService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_validation_result(
    validator_name: str = "test_validator",
    status: ValidationStatus = ValidationStatus.PASSED,
    issues: list[ValidationIssue] | None = None,
) -> ValidationResult:
    """Create a mock validation result."""
    return ValidationResult(
        validator_name=validator_name,
        status=status,
        issues=issues or [],
        metadata={},
    )


def make_issue(
    code: str = "TEST_ERROR",
    message: str = "Test error message",
    severity: Severity = Severity.ERROR,
) -> ValidationIssue:
    """Create a validation issue."""
    return ValidationIssue(
        code=code,
        message=message,
        severity=severity,
        field=None,
        suggested_fix=None,
    )


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
            mock_print.return_value = make_validation_result("print_validator")
            mock_ebook.return_value = make_validation_result("ebook_validator")
            mock_cover.return_value = make_validation_result("cover_validator")
            mock_compliance.return_value = make_validation_result("compliance_scanner")

            request = FullValidationRequest(
                print_validation=PrintValidationRequest(
                    trim_size="6x9",
                    page_count=200,
                    interior_type="black_and_white",
                ),
                ebook_validation=EbookValidationRequest(
                    file_path="/path/to/book.epub",
                    format="epub",
                ),
                cover_validation=CoverValidationRequest(
                    file_path="/path/to/cover.jpg",
                    trim_size="6x9",
                ),
                compliance_scan=ComplianceScanRequest(
                    manuscript_text="Sample text",
                ),
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
                "print_validator",
                ValidationStatus.FAILED,
                [make_issue("INVALID_TRIM", "Invalid trim size", Severity.ERROR)],
            )
            mock_ebook.return_value = make_validation_result(
                "ebook_validator",
                ValidationStatus.PASSED,
            )

            request = FullValidationRequest(
                print_validation=PrintValidationRequest(
                    trim_size="invalid",
                    page_count=50,
                    interior_type="color",
                ),
                ebook_validation=EbookValidationRequest(
                    file_path="/path/to/book.epub",
                    format="epub",
                ),
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
                "cover_validator",
                ValidationStatus.WARNINGS,
                [make_issue("LOW_RES", "Cover resolution is low", Severity.WARNING)],
            )

            request = FullValidationRequest(
                cover_validation=CoverValidationRequest(
                    file_path="/path/to/cover.jpg",
                    trim_size="6x9",
                ),
            )

            result = service.run_full_validation(request)

        assert result.overall_status == ValidationStatus.WARNINGS
        assert result.total_errors == 0
        assert result.total_warnings == 1

    def test_full_validation_stores_results(self):
        """Should store results for later retrieval."""
        service = ValidationService()

        with patch.object(service.print_validator, "validate") as mock_print:
            mock_print.return_value = make_validation_result("print_validator")

            request = FullValidationRequest(
                print_validation=PrintValidationRequest(
                    trim_size="6x9",
                    page_count=100,
                    interior_type="black_and_white",
                ),
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

        request = PrintValidationRequest(
            trim_size="6x9",
            page_count=150,
            interior_type="black_and_white",
            paper_type="cream",
        )

        with patch.object(service.print_validator, "validate") as mock_validate:
            mock_validate.return_value = make_validation_result("print_validator")

            result = service.validate_print(request)

        mock_validate.assert_called_once_with(request)
        assert result.validator_name == "print_validator"


class TestValidateEbook:
    def test_validate_ebook_delegates_to_validator(self):
        """Should delegate to EbookValidator."""
        service = ValidationService()

        request = EbookValidationRequest(
            file_path="/path/to/book.epub",
            format="epub",
        )

        with patch.object(service.ebook_validator, "validate") as mock_validate:
            mock_validate.return_value = make_validation_result("ebook_validator")

            result = service.validate_ebook(request)

        mock_validate.assert_called_once_with(request)
        assert result.validator_name == "ebook_validator"


class TestValidateCover:
    def test_validate_cover_delegates_to_validator(self):
        """Should delegate to CoverValidator."""
        service = ValidationService()

        request = CoverValidationRequest(
            file_path="/path/to/cover.jpg",
            trim_size="6x9",
            bleed=0.125,
        )

        with patch.object(service.cover_validator, "validate") as mock_validate:
            mock_validate.return_value = make_validation_result("cover_validator")

            result = service.validate_cover(request)

        mock_validate.assert_called_once_with(request)
        assert result.validator_name == "cover_validator"


class TestScanCompliance:
    def test_scan_compliance_delegates_to_scanner(self):
        """Should delegate to ComplianceScanner."""
        service = ValidationService()

        request = ComplianceScanRequest(
            manuscript_text="Sample text for compliance scanning",
        )

        with patch.object(service.compliance_scanner, "scan") as mock_scan:
            mock_scan.return_value = make_validation_result("compliance_scanner")

            result = service.scan_compliance(request)

        mock_scan.assert_called_once_with(request)
        assert result.validator_name == "compliance_scanner"


# ---------------------------------------------------------------------------
# Result retrieval tests
# ---------------------------------------------------------------------------


class TestGetResults:
    def test_get_results_existing(self):
        """Should retrieve stored validation results by ID."""
        service = ValidationService()

        with patch.object(service.print_validator, "validate") as mock_print:
            mock_print.return_value = make_validation_result("print_validator")

            request = FullValidationRequest(
                print_validation=PrintValidationRequest(
                    trim_size="6x9",
                    page_count=100,
                    interior_type="black_and_white",
                ),
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
            make_validation_result("val1", ValidationStatus.PASSED),
            make_validation_result("val2", ValidationStatus.PASSED),
        ]
        status = ValidationService._aggregate_status(results)
        assert status == ValidationStatus.PASSED

    def test_aggregate_any_failed(self):
        """Should return FAILED if any validator failed."""
        results = [
            make_validation_result("val1", ValidationStatus.PASSED),
            make_validation_result("val2", ValidationStatus.FAILED),
            make_validation_result("val3", ValidationStatus.WARNINGS),
        ]
        status = ValidationService._aggregate_status(results)
        assert status == ValidationStatus.FAILED

    def test_aggregate_warnings_only(self):
        """Should return WARNINGS if no failures but has warnings."""
        results = [
            make_validation_result("val1", ValidationStatus.PASSED),
            make_validation_result("val2", ValidationStatus.WARNINGS),
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
                "print_validator",
                ValidationStatus.FAILED,
                [
                    make_issue("ERR1", "Error 1", Severity.ERROR),
                    make_issue("ERR2", "Error 2", Severity.ERROR),
                    make_issue("WARN1", "Warning 1", Severity.WARNING),
                ],
            )
            mock_ebook.return_value = make_validation_result(
                "ebook_validator",
                ValidationStatus.WARNINGS,
                [
                    make_issue("WARN2", "Warning 2", Severity.WARNING),
                ],
            )

            request = FullValidationRequest(
                print_validation=PrintValidationRequest(
                    trim_size="6x9",
                    page_count=100,
                    interior_type="black_and_white",
                ),
                ebook_validation=EbookValidationRequest(
                    file_path="/path/to/book.epub",
                    format="epub",
                ),
            )

            result = service.run_full_validation(request)

        assert result.total_errors == 2
        assert result.total_warnings == 2
