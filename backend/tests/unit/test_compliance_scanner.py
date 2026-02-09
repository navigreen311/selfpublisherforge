"""Unit tests for ComplianceScanner — trademarks, content policy, HTML compliance, keywords."""

from __future__ import annotations

import pytest

from app.modules.kdp_validation.compliance_scanner import ComplianceScanner
from app.modules.kdp_validation.schemas import (
    ComplianceScanRequest,
    Severity,
    ValidationStatus,
)


@pytest.fixture
def scanner() -> ComplianceScanner:
    return ComplianceScanner()


def _make_request(**overrides) -> ComplianceScanRequest:
    """Create a clean compliance scan request."""
    defaults = dict(
        title="My Great Book",
        subtitle="A Novel",
        description="<p>A wonderful story about life.</p>",
        keywords=["fiction", "adventure", "novel"],
        categories=["Fiction > Adventure"],
        content_sample="",
    )
    defaults.update(overrides)
    return ComplianceScanRequest(**defaults)


# ===================================================================
# Trademark checks
# ===================================================================

class TestTrademarks:
    def test_clean_title(self, scanner: ComplianceScanner):
        req = _make_request(title="My Great Book")
        result = scanner.scan(req)
        tm_issues = [i for i in result.issues if i.rule == "trademark_violation"]
        assert len(tm_issues) == 0

    def test_kindle_unlimited_in_title(self, scanner: ComplianceScanner):
        req = _make_request(title="Available on Kindle Unlimited Now")
        result = scanner.scan(req)
        tm_issues = [i for i in result.issues if i.rule == "trademark_violation"]
        assert any("Kindle Unlimited" in i.message for i in tm_issues)

    def test_kindle_edition_in_subtitle(self, scanner: ComplianceScanner):
        req = _make_request(subtitle="Kindle Edition")
        result = scanner.scan(req)
        tm_issues = [i for i in result.issues if i.rule == "trademark_violation"]
        assert any("Kindle Edition" in i.message for i in tm_issues)

    def test_amazon_bestseller_warning(self, scanner: ComplianceScanner):
        req = _make_request(title="Amazon Bestseller: My Book")
        result = scanner.scan(req)
        tm_issues = [i for i in result.issues if i.rule == "trademark_violation"]
        warnings = [i for i in tm_issues if i.severity == Severity.WARNING]
        assert len(warnings) > 0

    def test_case_insensitive_detection(self, scanner: ComplianceScanner):
        req = _make_request(title="KINDLE UNLIMITED Special")
        result = scanner.scan(req)
        tm_issues = [i for i in result.issues if i.rule == "trademark_violation"]
        assert len(tm_issues) > 0

    def test_kindle_in_keyword(self, scanner: ComplianceScanner):
        req = _make_request(keywords=["kindle books", "fiction"])
        result = scanner.scan(req)
        tm_issues = [i for i in result.issues if i.rule == "trademark_violation"]
        assert len(tm_issues) > 0

    def test_number_one_bestseller_warning(self, scanner: ComplianceScanner):
        req = _make_request(title="#1 Best Seller in Fiction")
        result = scanner.scan(req)
        tm_issues = [i for i in result.issues if i.rule == "trademark_violation"]
        assert any("#1 Bestseller" in i.message or "#1 Best" in i.message for i in tm_issues)

    def test_trademark_in_description(self, scanner: ComplianceScanner):
        req = _make_request(description="Read this on Kindle Unlimited today!")
        result = scanner.scan(req)
        tm_issues = [i for i in result.issues if i.rule == "trademark_violation"]
        assert len(tm_issues) > 0


# ===================================================================
# Content policy
# ===================================================================

class TestContentPolicy:
    def test_clean_content(self, scanner: ComplianceScanner):
        req = _make_request(content_sample="A beautiful story about nature.")
        result = scanner.scan(req)
        policy_issues = [i for i in result.issues if i.rule == "content_policy"]
        assert len(policy_issues) == 0

    def test_public_domain_original_claim(self, scanner: ComplianceScanner):
        req = _make_request(
            content_sample="This public domain work is presented as an original publication."
        )
        result = scanner.scan(req)
        policy_issues = [i for i in result.issues if i.rule == "content_policy"]
        assert len(policy_issues) > 0

    def test_empty_content_skips(self, scanner: ComplianceScanner):
        req = _make_request(
            title="", subtitle="", description="", content_sample=""
        )
        result = scanner.scan(req)
        policy_issues = [i for i in result.issues if i.rule == "content_policy"]
        assert len(policy_issues) == 0


# ===================================================================
# Description HTML compliance
# ===================================================================

class TestDescriptionHTML:
    def test_clean_html(self, scanner: ComplianceScanner):
        req = _make_request(description="<p>A <b>great</b> book with <em>exciting</em> content.</p>")
        result = scanner.scan(req)
        html_issues = [
            i for i in result.issues
            if i.rule.startswith("description_html")
        ]
        assert len(html_issues) == 0

    def test_script_tag_error(self, scanner: ComplianceScanner):
        req = _make_request(description="<p>Hello</p><script>alert('xss')</script>")
        result = scanner.scan(req)
        errors = [i for i in result.issues if i.rule == "description_html_disallowed"]
        assert len(errors) > 0
        assert errors[0].severity == Severity.ERROR

    def test_iframe_error(self, scanner: ComplianceScanner):
        req = _make_request(description="<iframe src='evil.com'></iframe>")
        result = scanner.scan(req)
        errors = [i for i in result.issues if i.rule == "description_html_disallowed"]
        assert len(errors) > 0

    def test_onclick_error(self, scanner: ComplianceScanner):
        req = _make_request(description='<p onclick="alert()">Click me</p>')
        result = scanner.scan(req)
        errors = [i for i in result.issues if i.rule == "description_html_disallowed"]
        assert len(errors) > 0

    def test_style_tag_error(self, scanner: ComplianceScanner):
        req = _make_request(description="<style>body{color:red}</style><p>Text</p>")
        result = scanner.scan(req)
        errors = [i for i in result.issues if i.rule == "description_html_disallowed"]
        assert len(errors) > 0

    def test_disallowed_html_tags_warning(self, scanner: ComplianceScanner):
        req = _make_request(description="<div>Text</div><span>More</span>")
        result = scanner.scan(req)
        tag_warnings = [i for i in result.issues if i.rule == "description_html_tag"]
        # div and span are not in allowed list
        assert len(tag_warnings) >= 2

    def test_allowed_tags_no_warning(self, scanner: ComplianceScanner):
        req = _make_request(
            description="<h1>Title</h1><p>Text with <b>bold</b> and <i>italic</i>.</p><ul><li>Item</li></ul>"
        )
        result = scanner.scan(req)
        tag_warnings = [i for i in result.issues if i.rule == "description_html_tag"]
        assert len(tag_warnings) == 0

    def test_empty_description_skips(self, scanner: ComplianceScanner):
        req = _make_request(description="")
        result = scanner.scan(req)
        html_issues = [i for i in result.issues if i.rule.startswith("description_html")]
        assert len(html_issues) == 0


# ===================================================================
# Keyword checks
# ===================================================================

class TestKeywords:
    def test_valid_keywords(self, scanner: ComplianceScanner):
        req = _make_request(keywords=["fiction", "adventure", "romance"])
        result = scanner.scan(req)
        kw_issues = [i for i in result.issues if i.rule.startswith("keyword_")]
        assert len(kw_issues) == 0

    def test_too_many_keywords(self, scanner: ComplianceScanner):
        req = _make_request(keywords=["a", "b", "c", "d", "e", "f", "g", "h"])
        result = scanner.scan(req)
        warnings = [i for i in result.issues if i.rule == "keyword_count"]
        assert len(warnings) == 1
        assert warnings[0].severity == Severity.WARNING

    def test_exactly_seven_keywords(self, scanner: ComplianceScanner):
        req = _make_request(keywords=["a", "b", "c", "d", "e", "f", "g"])
        result = scanner.scan(req)
        warnings = [i for i in result.issues if i.rule == "keyword_count"]
        assert len(warnings) == 0

    def test_long_keyword(self, scanner: ComplianceScanner):
        req = _make_request(keywords=["x" * 60])
        result = scanner.scan(req)
        warnings = [i for i in result.issues if i.rule == "keyword_length"]
        assert len(warnings) == 1

    def test_duplicate_keywords(self, scanner: ComplianceScanner):
        req = _make_request(keywords=["fiction", "Fiction", "adventure"])
        result = scanner.scan(req)
        infos = [i for i in result.issues if i.rule == "keyword_duplicate"]
        assert len(infos) == 1
        assert infos[0].severity == Severity.INFO

    def test_empty_keywords(self, scanner: ComplianceScanner):
        req = _make_request(keywords=[])
        result = scanner.scan(req)
        kw_issues = [i for i in result.issues if i.rule.startswith("keyword_")]
        assert len(kw_issues) == 0


# ===================================================================
# Overall status
# ===================================================================

class TestOverallStatus:
    def test_passes_when_clean(self, scanner: ComplianceScanner):
        req = _make_request()
        result = scanner.scan(req)
        assert result.status == ValidationStatus.PASSED

    def test_fails_with_disallowed_html(self, scanner: ComplianceScanner):
        req = _make_request(description="<script>evil()</script>")
        result = scanner.scan(req)
        assert result.status == ValidationStatus.FAILED

    def test_warnings_status(self, scanner: ComplianceScanner):
        req = _make_request(keywords=["a"] * 8)
        result = scanner.scan(req)
        # Too many keywords is a warning; check no errors
        has_error = any(i.severity == Severity.ERROR for i in result.issues)
        if not has_error:
            assert result.status == ValidationStatus.WARNINGS

    def test_metadata_populated(self, scanner: ComplianceScanner):
        req = _make_request()
        result = scanner.scan(req)
        assert "title_length" in result.metadata
        assert "description_length" in result.metadata
        assert "keyword_count" in result.metadata
