"""Print file validation for KDP submissions.

Validates margins, bleed, spine width, font embedding, image DPI,
color space, and page count against KDP requirements.
"""

from __future__ import annotations

from app.modules.kdp_validation.rules import (
    BLEED_SIZE,
    MIN_PAGE_COUNT,
    MIN_PRINT_DPI,
    TRIM_SIZES,
    PaperType,
    calculate_spine_width,
    get_inside_margin,
    get_max_page_count,
)
from app.modules.kdp_validation.schemas import (
    PrintValidationRequest,
    Severity,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
    ValidationType,
)


class PrintValidator:
    """Validates print-ready files against KDP requirements."""

    def validate(self, request: PrintValidationRequest) -> ValidationResult:
        """Run all print validation checks and return aggregated result."""
        issues: list[ValidationIssue] = []

        issues.extend(self._check_trim_size(request))
        issues.extend(self._check_page_count(request))
        issues.extend(self._check_margins(request))
        issues.extend(self._check_bleed(request))
        issues.extend(self._check_fonts(request))
        issues.extend(self._check_image_dpi(request))
        issues.extend(self._check_color_space(request))

        spine_width = self._calculate_spine(request)

        status = self._determine_status(issues)

        return ValidationResult(
            validation_type=ValidationType.PRINT,
            status=status,
            issues=issues,
            metadata={
                "spine_width_inches": spine_width,
                "trim_size": request.trim_size,
                "page_count": request.page_count,
            },
        )

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_trim_size(self, req: PrintValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if req.trim_size not in TRIM_SIZES:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="trim_size_valid",
                    message=f"Trim size '{req.trim_size}' is not a supported KDP trim size. "
                    f"Supported: {', '.join(sorted(TRIM_SIZES.keys()))}",
                    location="trim_size",
                )
            )
        return issues

    def _check_page_count(self, req: PrintValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if req.page_count < MIN_PAGE_COUNT:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="page_count_min",
                    message=f"Page count {req.page_count} is below the KDP minimum of {MIN_PAGE_COUNT}.",
                    location="page_count",
                )
            )

        try:
            paper = PaperType(req.paper_type)
        except ValueError:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="paper_type_valid",
                    message=f"Paper type '{req.paper_type}' is not valid. Use 'white' or 'cream'.",
                    location="paper_type",
                )
            )
            return issues

        max_pages = get_max_page_count(paper)
        if req.page_count > max_pages:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="page_count_max",
                    message=f"Page count {req.page_count} exceeds KDP maximum of {max_pages} for {paper.value} paper.",
                    location="page_count",
                )
            )

        if req.page_count % 2 != 0:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    rule="page_count_even",
                    message="Page count should be even for print books. KDP will add a blank page.",
                    location="page_count",
                )
            )

        return issues

    def _check_margins(self, req: PrintValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        trim = TRIM_SIZES.get(req.trim_size)
        if trim is None:
            return issues  # already flagged in trim_size check

        # Inside margin scales with page count
        required_inside = get_inside_margin(trim.min_inside_margin, req.page_count)

        if req.inside_margin < required_inside:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="margin_inside",
                    message=(
                        f'Inside margin {req.inside_margin}" is below the required '
                        f'{required_inside}" for {trim.label} with {req.page_count} pages.'
                    ),
                    location="inside_margin",
                    details={"required": required_inside, "actual": req.inside_margin},
                )
            )

        if req.outside_margin < trim.min_outside_margin:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="margin_outside",
                    message=(
                        f'Outside margin {req.outside_margin}" is below the required '
                        f'{trim.min_outside_margin}" for {trim.label}.'
                    ),
                    location="outside_margin",
                    details={"required": trim.min_outside_margin, "actual": req.outside_margin},
                )
            )

        if req.top_margin < trim.min_top_margin:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="margin_top",
                    message=(
                        f'Top margin {req.top_margin}" is below the required '
                        f'{trim.min_top_margin}" for {trim.label}.'
                    ),
                    location="top_margin",
                    details={"required": trim.min_top_margin, "actual": req.top_margin},
                )
            )

        if req.bottom_margin < trim.min_bottom_margin:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="margin_bottom",
                    message=(
                        f'Bottom margin {req.bottom_margin}" is below the required '
                        f'{trim.min_bottom_margin}" for {trim.label}.'
                    ),
                    location="bottom_margin",
                    details={"required": trim.min_bottom_margin, "actual": req.bottom_margin},
                )
            )

        return issues

    def _check_bleed(self, req: PrintValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if req.has_bleed:
            issues.append(
                ValidationIssue(
                    severity=Severity.INFO,
                    rule="bleed_enabled",
                    message=f'Full bleed is enabled. Ensure {BLEED_SIZE}" bleed on all sides.',
                    location="bleed",
                    details={"required_bleed": BLEED_SIZE},
                )
            )
        return issues

    def _check_fonts(self, req: PrintValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if not req.fonts_embedded:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="fonts_embedded",
                    message="All fonts must be embedded in the PDF for KDP print submission.",
                    location="fonts",
                )
            )
        return issues

    def _check_image_dpi(self, req: PrintValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if req.image_dpi is not None and req.image_dpi < MIN_PRINT_DPI:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="image_dpi_print",
                    message=(f"Image DPI ({req.image_dpi}) is below the required " f"{MIN_PRINT_DPI} DPI for print."),
                    location="images",
                    details={"required": MIN_PRINT_DPI, "actual": req.image_dpi},
                )
            )
        return issues

    def _check_color_space(self, req: PrintValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if req.color_space is not None:
            expected = "RGB"  # KDP interior should be sRGB
            if req.color_space.upper() != expected:
                issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        rule="color_space_interior",
                        message=(
                            f"Interior color space is '{req.color_space}'. "
                            f"KDP recommends '{expected}' for interior files."
                        ),
                        location="color_space",
                    )
                )
        return issues

    def _calculate_spine(self, req: PrintValidationRequest) -> float:
        try:
            paper = PaperType(req.paper_type)
        except ValueError:
            paper = PaperType.WHITE
        return calculate_spine_width(req.page_count, paper)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @staticmethod
    def _determine_status(issues: list[ValidationIssue]) -> ValidationStatus:
        has_errors = any(i.severity == Severity.ERROR for i in issues)
        has_warnings = any(i.severity == Severity.WARNING for i in issues)
        if has_errors:
            return ValidationStatus.FAILED
        if has_warnings:
            return ValidationStatus.WARNINGS
        return ValidationStatus.PASSED
