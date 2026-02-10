"""Cover validation for KDP submissions.

Validates cover resolution, dimensions (including bleed/spine), safe zones,
file format, and color space compliance for both print and ebook covers.
"""

from __future__ import annotations

from app.modules.kdp_validation.rules import (
    ALLOWED_EBOOK_COVER_FORMATS,
    ALLOWED_PRINT_COVER_FORMATS,
    BLEED_SIZE,
    COVER_COLOR_SPACE,
    COVER_DIMENSION_TOLERANCE,
    MIN_EBOOK_DPI,
    MIN_PRINT_DPI,
    SAFE_ZONE_INCHES,
    TRIM_SIZES,
    CoverType,
    PaperType,
    calculate_spine_width,
    expected_print_cover_height,
    expected_print_cover_width,
)
from app.modules.kdp_validation.schemas import (
    CoverValidationRequest,
    Severity,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
    ValidationType,
)


class CoverValidator:
    """Validates cover files against KDP requirements."""

    def validate(self, request: CoverValidationRequest) -> ValidationResult:
        """Run all cover validation checks and return aggregated result."""
        issues: list[ValidationIssue] = []

        issues.extend(self._check_resolution(request))
        issues.extend(self._check_dimensions(request))
        issues.extend(self._check_safe_zones(request))
        issues.extend(self._check_file_format(request))
        issues.extend(self._check_color_space(request))

        status = self._determine_status(issues)

        metadata: dict = {
            "cover_type": request.cover_type,
            "width_inches": request.width_inches,
            "height_inches": request.height_inches,
            "dpi": request.dpi,
        }

        # Add expected dimensions for print covers
        if request.cover_type == CoverType.PRINT.value and request.trim_size:
            trim = TRIM_SIZES.get(request.trim_size)
            if trim and request.page_count:
                try:
                    paper = PaperType(request.paper_type)
                except ValueError:
                    paper = PaperType.WHITE
                spine = calculate_spine_width(request.page_count, paper)
                metadata["expected_width"] = round(
                    expected_print_cover_width(trim.width, spine), 4
                )
                metadata["expected_height"] = round(
                    expected_print_cover_height(trim.height), 4
                )
                metadata["spine_width"] = spine

        return ValidationResult(
            validation_type=ValidationType.COVER,
            status=status,
            issues=issues,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_resolution(self, req: CoverValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if req.cover_type == CoverType.PRINT.value:
            min_dpi = MIN_PRINT_DPI
        else:
            min_dpi = MIN_EBOOK_DPI

        if req.dpi < min_dpi:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="cover_resolution",
                    message=(
                        f"Cover resolution ({req.dpi} DPI) is below the required "
                        f"{min_dpi} DPI for {req.cover_type} covers."
                    ),
                    location="cover_dpi",
                    details={"required": min_dpi, "actual": req.dpi},
                )
            )

        return issues

    def _check_dimensions(self, req: CoverValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if req.cover_type != CoverType.PRINT.value:
            return issues

        if not req.trim_size or not req.page_count:
            issues.append(
                ValidationIssue(
                    severity=Severity.INFO,
                    rule="cover_dimensions_skipped",
                    message=(
                        "Trim size or page count not provided; "
                        "cannot verify cover dimensions match requirements."
                    ),
                    location="cover_dimensions",
                )
            )
            return issues

        trim = TRIM_SIZES.get(req.trim_size)
        if trim is None:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="cover_trim_size_valid",
                    message=f"Trim size '{req.trim_size}' is not supported.",
                    location="cover_dimensions",
                )
            )
            return issues

        try:
            paper = PaperType(req.paper_type)
        except ValueError:
            paper = PaperType.WHITE

        spine = calculate_spine_width(req.page_count, paper)
        exp_width = expected_print_cover_width(trim.width, spine)
        exp_height = expected_print_cover_height(trim.height)

        width_diff = abs(req.width_inches - exp_width)
        height_diff = abs(req.height_inches - exp_height)

        if width_diff > COVER_DIMENSION_TOLERANCE:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="cover_width",
                    message=(
                        f"Cover width {req.width_inches}\" does not match the expected "
                        f"{exp_width:.4f}\" (front + back + spine + bleed). "
                        f"Difference: {width_diff:.4f}\"."
                    ),
                    location="cover_dimensions",
                    details={"expected": round(exp_width, 4), "actual": req.width_inches},
                )
            )

        if height_diff > COVER_DIMENSION_TOLERANCE:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="cover_height",
                    message=(
                        f"Cover height {req.height_inches}\" does not match the expected "
                        f"{exp_height:.4f}\" (trim + bleed). "
                        f"Difference: {height_diff:.4f}\"."
                    ),
                    location="cover_dimensions",
                    details={"expected": round(exp_height, 4), "actual": req.height_inches},
                )
            )

        return issues

    def _check_safe_zones(self, req: CoverValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if req.has_text_in_bleed:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="cover_safe_zone",
                    message=(
                        f"Text detected in the bleed/safe zone area ({SAFE_ZONE_INCHES}\" from trim edge). "
                        "Text in the bleed area may be cut off during trimming."
                    ),
                    location="cover_safe_zone",
                    details={"safe_zone_inches": SAFE_ZONE_INCHES},
                )
            )

        return issues

    def _check_file_format(self, req: CoverValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        fmt = req.file_format.upper()

        if req.cover_type == CoverType.PRINT.value:
            allowed = ALLOWED_PRINT_COVER_FORMATS
        else:
            allowed = ALLOWED_EBOOK_COVER_FORMATS

        if fmt not in allowed:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="cover_format",
                    message=(
                        f"Cover format '{req.file_format}' is not accepted for "
                        f"{req.cover_type} covers. Allowed: {', '.join(sorted(allowed))}."
                    ),
                    location="cover_format",
                )
            )

        return issues

    def _check_color_space(self, req: CoverValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if req.color_space is None:
            return issues

        if req.cover_type == CoverType.PRINT.value:
            if req.color_space.upper() != COVER_COLOR_SPACE:
                issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        rule="cover_color_space",
                        message=(
                            f"Print cover color space is '{req.color_space}'. "
                            f"KDP recommends '{COVER_COLOR_SPACE}' for print covers."
                        ),
                        location="cover_color_space",
                    )
                )
        else:
            # Ebook covers should be sRGB
            if req.color_space.upper() not in ("RGB", "SRGB"):
                issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        rule="cover_color_space",
                        message=(
                            f"Ebook cover color space is '{req.color_space}'. "
                            "KDP recommends 'sRGB' for ebook covers."
                        ),
                        location="cover_color_space",
                    )
                )

        return issues

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
