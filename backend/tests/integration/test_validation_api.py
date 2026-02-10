"""Integration tests for KDP validation API endpoints.

Tests all endpoints end-to-end using FastAPI's TestClient.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.modules.kdp_validation.rules import (
    PaperType,
    calculate_spine_width,
    expected_print_cover_height,
    expected_print_cover_width,
)


@pytest.fixture
def client():
    """Create a TestClient that bypasses the database lifespan."""
    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from app.modules.kdp_validation.router import router

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


# ===================================================================
# POST /api/v1/publishing/validate — Full validation
# ===================================================================

class TestFullValidation:
    def test_full_validation_all_pass(self, client: TestClient):
        spine = calculate_spine_width(200, PaperType.WHITE)
        exp_w = round(expected_print_cover_width(6.0, spine), 4)
        exp_h = round(expected_print_cover_height(9.0), 4)

        payload = {
            "print_validation": {
                "trim_size": "6x9",
                "page_count": 200,
                "paper_type": "white",
                "has_bleed": False,
                "inside_margin": 0.625,
                "outside_margin": 0.5,
                "top_margin": 0.5,
                "bottom_margin": 0.5,
                "image_dpi": 300,
                "fonts_embedded": True,
                "color_space": "RGB",
            },
            "ebook_validation": {
                "has_ncx_toc": True,
                "has_html_toc": True,
                "images": [],
                "links": [],
                "has_javascript": False,
                "has_external_resources": False,
                "min_font_size_pt": 12.0,
                "file_size_bytes": 5000000,
            },
            "cover_validation": {
                "cover_type": "print",
                "width_inches": exp_w,
                "height_inches": exp_h,
                "dpi": 300,
                "file_format": "TIFF",
                "color_space": "CMYK",
                "trim_size": "6x9",
                "page_count": 200,
                "paper_type": "white",
                "has_text_in_bleed": False,
            },
            "compliance_scan": {
                "title": "My Great Book",
                "subtitle": "A Novel",
                "description": "<p>A wonderful story.</p>",
                "keywords": ["fiction", "adventure"],
            },
        }

        resp = client.post("/api/v1/publishing/validate", json=payload)
        assert resp.status_code == 200

        data = resp.json()
        assert data["overall_status"] == "passed"
        assert data["total_errors"] == 0
        assert len(data["results"]) == 4

    def test_full_validation_with_errors(self, client: TestClient):
        payload = {
            "print_validation": {
                "trim_size": "6x9",
                "page_count": 10,  # Below minimum
                "paper_type": "white",
                "has_bleed": False,
                "inside_margin": 0.1,  # Too small
                "outside_margin": 0.1,
                "top_margin": 0.1,
                "bottom_margin": 0.1,
                "fonts_embedded": False,
            },
        }

        resp = client.post("/api/v1/publishing/validate", json=payload)
        assert resp.status_code == 200

        data = resp.json()
        assert data["overall_status"] == "failed"
        assert data["total_errors"] > 0

    def test_full_validation_empty_request(self, client: TestClient):
        """All fields are optional — empty request should pass."""
        resp = client.post("/api/v1/publishing/validate", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_status"] == "passed"
        assert data["total_errors"] == 0
        assert len(data["results"]) == 0

    def test_full_validation_partial(self, client: TestClient):
        """Only some validators provided."""
        payload = {
            "compliance_scan": {
                "title": "Clean Title",
                "description": "<p>Good description</p>",
            },
        }
        resp = client.post("/api/v1/publishing/validate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["validation_type"] == "compliance"

    def test_full_validation_returns_id(self, client: TestClient):
        payload = {
            "compliance_scan": {"title": "Test"},
        }
        resp = client.post("/api/v1/publishing/validate", json=payload)
        data = resp.json()
        assert "id" in data
        # Should be a valid UUID
        uuid.UUID(data["id"])


# ===================================================================
# POST /api/v1/publishing/validate/print
# ===================================================================

class TestPrintEndpoint:
    def test_valid_print(self, client: TestClient):
        payload = {
            "trim_size": "6x9",
            "page_count": 200,
            "paper_type": "white",
            "has_bleed": False,
            "inside_margin": 0.625,
            "outside_margin": 0.5,
            "top_margin": 0.5,
            "bottom_margin": 0.5,
            "image_dpi": 300,
            "fonts_embedded": True,
            "color_space": "RGB",
        }
        resp = client.post("/api/v1/publishing/validate/print", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["validation_type"] == "print"
        assert data["status"] == "passed"
        assert "spine_width_inches" in data["metadata"]

    def test_invalid_print(self, client: TestClient):
        payload = {
            "trim_size": "invalid",
            "page_count": 5,
            "inside_margin": 0.1,
            "outside_margin": 0.1,
            "top_margin": 0.1,
            "bottom_margin": 0.1,
            "fonts_embedded": False,
        }
        resp = client.post("/api/v1/publishing/validate/print", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert len(data["issues"]) > 0


# ===================================================================
# POST /api/v1/publishing/validate/ebook
# ===================================================================

class TestEbookEndpoint:
    def test_valid_ebook(self, client: TestClient):
        payload = {
            "has_ncx_toc": True,
            "has_html_toc": True,
            "images": [
                {"filename": "cover.jpg", "format": "JPEG", "size_bytes": 500000, "dpi": 150},
            ],
            "links": [
                {"href": "#ch1", "is_internal": True, "is_valid": True},
            ],
            "has_javascript": False,
            "has_external_resources": False,
            "min_font_size_pt": 12.0,
            "file_size_bytes": 5000000,
        }
        resp = client.post("/api/v1/publishing/validate/ebook", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["validation_type"] == "ebook"
        assert data["status"] == "passed"

    def test_ebook_with_issues(self, client: TestClient):
        payload = {
            "has_ncx_toc": False,
            "has_html_toc": False,
            "images": [
                {"filename": "bad.bmp", "format": "BMP", "size_bytes": 6000000},
            ],
            "links": [
                {"href": "#broken", "is_internal": True, "is_valid": False},
            ],
            "has_javascript": True,
            "has_external_resources": True,
            "min_font_size_pt": 3.0,
            "file_size_bytes": 700000000,
        }
        resp = client.post("/api/v1/publishing/validate/ebook", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert len(data["issues"]) >= 6


# ===================================================================
# POST /api/v1/publishing/validate/cover
# ===================================================================

class TestCoverEndpoint:
    def test_valid_print_cover(self, client: TestClient):
        spine = calculate_spine_width(200, PaperType.WHITE)
        exp_w = round(expected_print_cover_width(6.0, spine), 4)
        exp_h = round(expected_print_cover_height(9.0), 4)

        payload = {
            "cover_type": "print",
            "width_inches": exp_w,
            "height_inches": exp_h,
            "dpi": 300,
            "file_format": "TIFF",
            "color_space": "CMYK",
            "trim_size": "6x9",
            "page_count": 200,
            "paper_type": "white",
            "has_text_in_bleed": False,
        }
        resp = client.post("/api/v1/publishing/validate/cover", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["validation_type"] == "cover"
        assert data["status"] == "passed"

    def test_valid_ebook_cover(self, client: TestClient):
        payload = {
            "cover_type": "ebook",
            "width_inches": 6.0,
            "height_inches": 9.0,
            "dpi": 72,
            "file_format": "JPEG",
            "color_space": "RGB",
            "has_text_in_bleed": False,
        }
        resp = client.post("/api/v1/publishing/validate/cover", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "passed"

    def test_invalid_cover(self, client: TestClient):
        payload = {
            "cover_type": "print",
            "width_inches": 5.0,
            "height_inches": 5.0,
            "dpi": 72,
            "file_format": "JPEG",
            "trim_size": "6x9",
            "page_count": 200,
            "has_text_in_bleed": True,
        }
        resp = client.post("/api/v1/publishing/validate/cover", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"


# ===================================================================
# GET /api/v1/publishing/validate/{id}/results
# ===================================================================

class TestGetResults:
    def test_retrieve_results(self, client: TestClient):
        # First, run a validation
        payload = {
            "compliance_scan": {"title": "Test Book"},
        }
        create_resp = client.post("/api/v1/publishing/validate", json=payload)
        assert create_resp.status_code == 200
        validation_id = create_resp.json()["id"]

        # Now retrieve results
        get_resp = client.get(f"/api/v1/publishing/validate/{validation_id}/results")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == validation_id

    def test_not_found(self, client: TestClient):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/publishing/validate/{fake_id}/results")
        assert resp.status_code == 404


# ===================================================================
# POST /api/v1/publishing/compliance-scan
# ===================================================================

class TestComplianceScanEndpoint:
    def test_clean_scan(self, client: TestClient):
        payload = {
            "title": "My Book",
            "subtitle": "A Novel",
            "description": "<p>Great content.</p>",
            "keywords": ["fiction"],
        }
        resp = client.post("/api/v1/publishing/compliance-scan", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["validation_type"] == "compliance"
        assert data["status"] == "passed"

    def test_trademark_violation(self, client: TestClient):
        payload = {
            "title": "Kindle Unlimited Guide",
            "description": "<p>How to succeed.</p>",
        }
        resp = client.post("/api/v1/publishing/compliance-scan", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        tm_issues = [i for i in data["issues"] if i["rule"] == "trademark_violation"]
        assert len(tm_issues) > 0

    def test_html_violation(self, client: TestClient):
        payload = {
            "title": "Good Title",
            "description": "<script>alert('bad')</script><p>Text</p>",
        }
        resp = client.post("/api/v1/publishing/compliance-scan", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"

    def test_empty_scan(self, client: TestClient):
        resp = client.post("/api/v1/publishing/compliance-scan", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["validation_type"] == "compliance"


# ===================================================================
# Edge cases & validation
# ===================================================================

class TestEdgeCases:
    def test_invalid_json_returns_422(self, client: TestClient):
        resp = client.post(
            "/api/v1/publishing/validate/print",
            json={"trim_size": "6x9"},  # Missing required fields
        )
        assert resp.status_code == 422

    def test_negative_margin_returns_422(self, client: TestClient):
        resp = client.post(
            "/api/v1/publishing/validate/print",
            json={
                "trim_size": "6x9",
                "page_count": 200,
                "inside_margin": -0.5,
                "outside_margin": 0.5,
                "top_margin": 0.5,
                "bottom_margin": 0.5,
            },
        )
        assert resp.status_code == 422

    def test_all_endpoints_return_json(self, client: TestClient):
        """Verify all endpoints consistently return JSON."""
        endpoints = [
            ("/api/v1/publishing/validate", "POST", {}),
            ("/api/v1/publishing/compliance-scan", "POST", {}),
        ]
        for path, method, body in endpoints:
            resp = client.request(method, path, json=body)
            assert resp.headers["content-type"] == "application/json"
