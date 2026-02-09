"""Ebook validation for KDP submissions.

Validates Table of Contents, images, internal links, prohibited elements
(JavaScript, external resources), font size recommendations, and file size.
"""

from __future__ import annotations

from app.modules.kdp_validation.rules import (
    ALLOWED_EBOOK_IMAGE_FORMATS,
    DISALLOWED_EBOOK_ELEMENTS,
    MAX_EBOOK_FILE_SIZE_BYTES,
    MAX_EBOOK_IMAGE_SIZE_BYTES,
    MIN_EBOOK_DPI,
    RECOMMENDED_MIN_FONT_SIZE_PT,
)
from app.modules.kdp_validation.schemas import (
    EbookValidationRequest,
    Severity,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
    ValidationType,
)


class EbookValidator:
    """Validates ebook files against KDP requirements."""

    def validate(self, request: EbookValidationRequest) -> ValidationResult:
        """Run all ebook validation checks and return aggregated result."""
        issues: list[ValidationIssue] = []

        issues.extend(self._check_toc(request))
        issues.extend(self._check_images(request))
        issues.extend(self._check_links(request))
        issues.extend(self._check_prohibited_elements(request))
        issues.extend(self._check_font_size(request))
        issues.extend(self._check_file_size(request))

        status = self._determine_status(issues)

        return ValidationResult(
            validation_type=ValidationType.EBOOK,
            status=status,
            issues=issues,
            metadata={
                "image_count": len(request.images),
                "link_count": len(request.links),
                "file_size_bytes": request.file_size_bytes,
            },
        )

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_toc(self, req: EbookValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if not req.has_ncx_toc:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="toc_ncx",
                    message="NCX Table of Contents is missing. KDP requires an NCX TOC for navigation.",
                    location="toc",
                )
            )

        if not req.has_html_toc:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    rule="toc_html",
                    message=(
                        "HTML Table of Contents is missing. While not strictly required, "
                        "Amazon strongly recommends an HTML TOC for better reader experience."
                    ),
                    location="toc",
                )
            )

        return issues

    def _check_images(self, req: EbookValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for img in req.images:
            # Format check
            if img.format.upper() not in ALLOWED_EBOOK_IMAGE_FORMATS:
                issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        rule="ebook_image_format",
                        message=(
                            f"Image '{img.filename}' uses format '{img.format}'. "
                            f"Allowed formats: {', '.join(sorted(ALLOWED_EBOOK_IMAGE_FORMATS))}."
                        ),
                        location=f"image:{img.filename}",
                    )
                )

            # Size check
            if img.size_bytes > MAX_EBOOK_IMAGE_SIZE_BYTES:
                size_mb = img.size_bytes / (1024 * 1024)
                max_mb = MAX_EBOOK_IMAGE_SIZE_BYTES / (1024 * 1024)
                issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        rule="ebook_image_size",
                        message=(
                            f"Image '{img.filename}' is {size_mb:.1f} MB, "
                            f"exceeding the {max_mb:.0f} MB limit."
                        ),
                        location=f"image:{img.filename}",
                        details={"max_bytes": MAX_EBOOK_IMAGE_SIZE_BYTES, "actual_bytes": img.size_bytes},
                    )
                )

            # DPI check (informational for ebooks)
            if img.dpi is not None and img.dpi < MIN_EBOOK_DPI:
                issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        rule="ebook_image_dpi",
                        message=(
                            f"Image '{img.filename}' has {img.dpi} DPI, "
                            f"below the recommended minimum of {MIN_EBOOK_DPI} DPI."
                        ),
                        location=f"image:{img.filename}",
                    )
                )

        return issues

    def _check_links(self, req: EbookValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for link in req.links:
            if link.is_internal and not link.is_valid:
                issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        rule="ebook_link_broken",
                        message=(
                            f"Internal link to '{link.href}' is broken. "
                            "All internal links must resolve to valid destinations."
                        ),
                        location=f"link:{link.href}",
                    )
                )
            elif not link.is_internal:
                issues.append(
                    ValidationIssue(
                        severity=Severity.INFO,
                        rule="ebook_link_external",
                        message=(
                            f"External link found: '{link.href}'. "
                            "External links are allowed but may not work on all devices."
                        ),
                        location=f"link:{link.href}",
                    )
                )

        return issues

    def _check_prohibited_elements(self, req: EbookValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if req.has_javascript:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="ebook_no_javascript",
                    message="JavaScript is not allowed in KDP ebooks and will be stripped.",
                    location="content",
                )
            )

        if req.has_external_resources:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="ebook_no_external_resources",
                    message=(
                        "External resources (stylesheets, images, etc.) are not allowed. "
                        "All resources must be embedded in the ebook file."
                    ),
                    location="content",
                )
            )

        return issues

    def _check_font_size(self, req: EbookValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if req.min_font_size_pt is not None and req.min_font_size_pt < RECOMMENDED_MIN_FONT_SIZE_PT:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    rule="ebook_font_size",
                    message=(
                        f"Minimum font size {req.min_font_size_pt}pt is below the "
                        f"recommended {RECOMMENDED_MIN_FONT_SIZE_PT}pt. "
                        "Small text may be difficult to read on some devices."
                    ),
                    location="typography",
                    details={
                        "recommended_min": RECOMMENDED_MIN_FONT_SIZE_PT,
                        "actual_min": req.min_font_size_pt,
                    },
                )
            )

        return issues

    def _check_file_size(self, req: EbookValidationRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if req.file_size_bytes > MAX_EBOOK_FILE_SIZE_BYTES:
            size_mb = req.file_size_bytes / (1024 * 1024)
            max_mb = MAX_EBOOK_FILE_SIZE_BYTES / (1024 * 1024)
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="ebook_file_size",
                    message=(
                        f"Ebook file size ({size_mb:.0f} MB) exceeds "
                        f"the KDP limit of {max_mb:.0f} MB."
                    ),
                    location="file",
                    details={"max_bytes": MAX_EBOOK_FILE_SIZE_BYTES, "actual_bytes": req.file_size_bytes},
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
