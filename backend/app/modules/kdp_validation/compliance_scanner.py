"""Content compliance scanning for KDP submissions.

Scans titles, subtitles, descriptions, keywords, and content samples
for policy violations, trademark infringements, and HTML compliance.
"""

from __future__ import annotations

import re

from app.modules.kdp_validation.rules import (
    CONTENT_POLICY_PATTERNS,
    DESCRIPTION_ALLOWED_HTML_TAGS,
    DESCRIPTION_DISALLOWED_HTML,
    TRADEMARK_PATTERNS,
    ComplianceRule,
)
from app.modules.kdp_validation.schemas import (
    ComplianceScanRequest,
    Severity,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
    ValidationType,
)


class ComplianceScanner:
    """Scans content for KDP policy compliance issues."""

    def scan(self, request: ComplianceScanRequest) -> ValidationResult:
        """Run all compliance checks and return aggregated result."""
        issues: list[ValidationIssue] = []

        issues.extend(self._check_trademarks(request))
        issues.extend(self._check_content_policy(request))
        issues.extend(self._check_description_html(request))
        issues.extend(self._check_keywords(request))

        status = self._determine_status(issues)

        return ValidationResult(
            validation_type=ValidationType.COMPLIANCE,
            status=status,
            issues=issues,
            metadata={
                "title_length": len(request.title),
                "description_length": len(request.description),
                "keyword_count": len(request.keywords),
            },
        )

    # ------------------------------------------------------------------
    # Trademark checks
    # ------------------------------------------------------------------

    def _check_trademarks(self, req: ComplianceScanRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        # Fields to scan for trademark issues
        fields = {
            "title": req.title,
            "subtitle": req.subtitle,
            "description": req.description,
        }

        for rule in TRADEMARK_PATTERNS:
            for field_name, field_value in fields.items():
                if not field_value:
                    continue
                if re.search(rule.pattern, field_value, re.IGNORECASE):
                    issues.append(
                        ValidationIssue(
                            severity=Severity(rule.severity),
                            rule="trademark_violation",
                            message=f"[{field_name}] {rule.description}",
                            location=field_name,
                            details={"pattern": rule.pattern},
                        )
                    )

        # Also check keywords list
        for keyword in req.keywords:
            for rule in TRADEMARK_PATTERNS:
                if re.search(rule.pattern, keyword, re.IGNORECASE):
                    issues.append(
                        ValidationIssue(
                            severity=Severity(rule.severity),
                            rule="trademark_violation",
                            message=f"[keyword: {keyword}] {rule.description}",
                            location="keywords",
                            details={"pattern": rule.pattern, "keyword": keyword},
                        )
                    )

        return issues

    # ------------------------------------------------------------------
    # Content policy checks
    # ------------------------------------------------------------------

    def _check_content_policy(self, req: ComplianceScanRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        text_to_scan = " ".join(
            filter(None, [req.title, req.subtitle, req.description, req.content_sample])
        )

        if not text_to_scan.strip():
            return issues

        for rule in CONTENT_POLICY_PATTERNS:
            if re.search(rule.pattern, text_to_scan, re.IGNORECASE):
                issues.append(
                    ValidationIssue(
                        severity=Severity(rule.severity),
                        rule="content_policy",
                        message=rule.description,
                        location="content",
                        details={"pattern": rule.pattern},
                    )
                )

        return issues

    # ------------------------------------------------------------------
    # Description HTML checks
    # ------------------------------------------------------------------

    def _check_description_html(self, req: ComplianceScanRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if not req.description:
            return issues

        desc_lower = req.description.lower()

        # Check for disallowed HTML elements
        for disallowed in DESCRIPTION_DISALLOWED_HTML:
            if disallowed.lower() in desc_lower:
                issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        rule="description_html_disallowed",
                        message=(
                            f"Description contains disallowed HTML element or attribute: "
                            f"'{disallowed}'. This will be rejected by KDP."
                        ),
                        location="description",
                        details={"disallowed_element": disallowed},
                    )
                )

        # Check for HTML tags not in the allowed set
        tag_pattern = re.compile(r"</?(\w+)[^>]*>")
        found_tags = set(tag_pattern.findall(req.description.lower()))
        disallowed_tags = found_tags - DESCRIPTION_ALLOWED_HTML_TAGS
        for tag in sorted(disallowed_tags):
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    rule="description_html_tag",
                    message=(
                        f"Description contains HTML tag '<{tag}>' which is not in "
                        "the KDP allowed tag list and may be stripped."
                    ),
                    location="description",
                    details={"tag": tag, "allowed_tags": sorted(DESCRIPTION_ALLOWED_HTML_TAGS)},
                )
            )

        return issues

    # ------------------------------------------------------------------
    # Keyword checks
    # ------------------------------------------------------------------

    def _check_keywords(self, req: ComplianceScanRequest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if len(req.keywords) > 7:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    rule="keyword_count",
                    message=(
                        f"You have {len(req.keywords)} keywords. "
                        "KDP allows a maximum of 7 keyword fields."
                    ),
                    location="keywords",
                )
            )

        for kw in req.keywords:
            if len(kw) > 50:
                issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        rule="keyword_length",
                        message=(
                            f"Keyword '{kw[:50]}...' exceeds 50 characters. "
                            "Long keywords may be truncated."
                        ),
                        location="keywords",
                    )
                )

        # Check for duplicate keywords
        seen: set[str] = set()
        for kw in req.keywords:
            kw_lower = kw.strip().lower()
            if kw_lower in seen:
                issues.append(
                    ValidationIssue(
                        severity=Severity.INFO,
                        rule="keyword_duplicate",
                        message=f"Duplicate keyword detected: '{kw}'.",
                        location="keywords",
                    )
                )
            seen.add(kw_lower)

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
