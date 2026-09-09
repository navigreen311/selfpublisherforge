"""Tests for Series Branding, Bundles, ISBN, Back Matter, and Multi-Distributor.

15+ tests covering:
- Series creation with branding config
- Branding lock prevents changes
- Coherence check detects inconsistencies
- Coherence check passes for consistent series
- Back matter generates all template types
- QR code generates from URL
- Bundle combines volumes correctly
- Bundle generates section dividers
- ISBN add to pool and assignment
- ISBN validation (valid and invalid)
- Barcode generation with placement guide
- KDP preflight validates correctly
- KDP preflight fails for low page count
- IngramSpark preflight includes PDF/X-1a checks
- B&N Press preflight includes ISBN check
- Review feedback maps complaints correctly
- Review feedback handles unknown complaints
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.specialty_books.service_series import (
    _find_best_complaint_match,
    _isbn_generate_barcode,
    _validate_isbn13,
    check_series_coherence,
    create_bundle,
    create_series,
    generate_back_matter,
    generate_qr_code,
    manage_isbn,
    process_review_feedback,
    run_distributor_preflight,
    update_series_branding,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────

ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
SERIES_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
BOOK_ID_1 = uuid.UUID("00000000-0000-0000-0000-000000000100")
BOOK_ID_2 = uuid.UUID("00000000-0000-0000-0000-000000000200")
BUNDLE_ID = uuid.UUID("00000000-0000-0000-0000-000000000300")
ISBN_ID = uuid.UUID("00000000-0000-0000-0000-000000000400")


def _make_mock_db():
    """Create a mock async session with flush support."""
    db = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


def _make_series_obj(
    series_id=SERIES_ID,
    org_id=ORG_ID,
    name="Animal Adventures",
    book_type="coloring",
    naming_format="{Series Name} Vol. {N}: {Subtitle}",
    branding_config=None,
    branding_locked=False,
    volume_count=0,
):
    obj = MagicMock()
    obj.id = series_id
    obj.org_id = org_id
    obj.name = name
    obj.book_type = book_type
    obj.naming_format = naming_format
    obj.branding_config = branding_config or {
        "title_font": "Montserrat",
        "title_position": "top_center",
        "author_position": "bottom_center",
        "volume_badge_style": "circle",
        "spine_layout": "horizontal",
    }
    obj.branding_locked = branding_locked
    obj.volume_count = volume_count
    obj.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    obj.deleted_at = None
    return obj


def _mock_scalar_one_or_none(obj):
    """Return a mock result whose scalar_one_or_none() returns obj."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = obj
    return result


# ── 1. Series Creation with Branding Config ──────────────────────────────────


@pytest.mark.asyncio
async def test_create_series_with_branding():
    db = _make_mock_db()

    with patch("app.modules.specialty_books.service_series.BookSeries") as MockSeries:
        mock_instance = _make_series_obj()
        MockSeries.return_value = mock_instance

        result = await create_series(
            db,
            ORG_ID,
            {
                "name": "Animal Adventures",
                "book_type": "coloring",
                "naming_format": "{Series Name} Vol. {N}: {Subtitle}",
                "branding_config": {
                    "title_font": "Montserrat",
                    "volume_badge_style": "circle",
                    "spine_layout": "horizontal",
                },
                "branding_locked": False,
            },
        )

    assert result["name"] == "Animal Adventures"
    assert result["branding_config"]["title_font"] == "Montserrat"
    assert result["branding_locked"] is False
    assert result["id"] == SERIES_ID
    db.add.assert_called_once()
    db.flush.assert_awaited_once()


# ── 2. Branding Lock Prevents Changes ────────────────────────────────────────


@pytest.mark.asyncio
async def test_branding_lock_prevents_changes():
    db = _make_mock_db()
    locked_series = _make_series_obj(branding_locked=True)
    db.execute = AsyncMock(return_value=_mock_scalar_one_or_none(locked_series))

    with pytest.raises(ValueError, match="Branding is locked"):
        await update_series_branding(
            db,
            SERIES_ID,
            ORG_ID,
            {
                "title_font": "NewFont",
            },
        )


# ── 3. Coherence Check Detects Inconsistencies ──────────────────────────────


@pytest.mark.asyncio
async def test_coherence_check_detects_naming_issue():
    db = _make_mock_db()
    series = _make_series_obj(
        branding_locked=True,
        branding_config={
            "title_font": "Montserrat",
            "spine_layout": "horizontal",
        },
    )
    db.execute = AsyncMock(return_value=_mock_scalar_one_or_none(series))

    volumes = [
        {
            "title": "Animal Adventures Vol. 1: Cats",
            "volume_number": 1,
            "metadata": {"branding": {"title_font": "Montserrat", "spine_layout": "horizontal"}},
        },
        {
            "title": "Cute Dogs Coloring",  # Missing series name
            "volume_number": 2,
            "metadata": {"branding": {"title_font": "Arial", "spine_layout": "vertical"}},
        },
    ]

    result = await check_series_coherence(db, SERIES_ID, ORG_ID, volumes=volumes)

    assert result["score"] < 100
    assert len(result["issues"]) > 0
    issue_types = {i["issue_type"] for i in result["issues"]}
    assert len(issue_types & {"naming", "cover_template", "spine"}) > 0


# ── 4. Coherence Check Passes for Consistent Series ─────────────────────────


@pytest.mark.asyncio
async def test_coherence_check_passes_consistent():
    db = _make_mock_db()
    series = _make_series_obj(
        branding_locked=True,
        branding_config={
            "title_font": "Montserrat",
            "spine_layout": "horizontal",
        },
    )
    db.execute = AsyncMock(return_value=_mock_scalar_one_or_none(series))

    volumes = [
        {
            "title": "Animal Adventures Vol. 1",
            "volume_number": 1,
            "metadata": {"branding": {"title_font": "Montserrat", "spine_layout": "horizontal"}},
        },
        {
            "title": "Animal Adventures Vol. 2",
            "volume_number": 2,
            "metadata": {"branding": {"title_font": "Montserrat", "spine_layout": "horizontal"}},
        },
    ]

    result = await check_series_coherence(db, SERIES_ID, ORG_ID, volumes=volumes)

    assert result["score"] == 100
    assert result["issues"] == []


# ── 5. Back Matter Generates All Template Types ──────────────────────────────


@pytest.mark.asyncio
async def test_back_matter_generates_all_types():
    db = _make_mock_db()

    with patch("app.modules.specialty_books.service_series.BackMatterTemplate") as MockBM:
        mock_record = MagicMock()
        mock_record.id = uuid.uuid4()
        MockBM.return_value = mock_record

        templates = [
            {
                "template_type": "also_in_series",
                "series_name": "My Series",
                "volumes": [
                    {"title": "Vol 1"},
                    {"title": "Vol 2"},
                ],
            },
            {
                "template_type": "about_series",
                "series_name": "My Series",
                "series_description": "A great series about animals.",
            },
            {"template_type": "email_cta", "cta_url": "https://example.com/signup"},
            {"template_type": "review_request"},
            {"template_type": "about_author", "author_name": "Jane Doe", "author_bio": "Jane writes coloring books."},
        ]

        result = await generate_back_matter(db, "coloring", BOOK_ID_1, ORG_ID, templates)

    assert len(result) == 5
    types_generated = [p["template_type"] for p in result]
    assert "also_in_series" in types_generated
    assert "about_series" in types_generated
    assert "email_cta" in types_generated
    assert "review_request" in types_generated
    assert "about_author" in types_generated

    # Email CTA should have QR code
    email_page = next(p for p in result if p["template_type"] == "email_cta")
    assert email_page["qr_code_url"] is not None
    assert "data:image/png;base64," in email_page["qr_code_url"]


# ── 6. QR Code Generates From URL ───────────────────────────────────────────


def test_qr_code_generates_from_url():
    result = generate_qr_code("https://example.com/my-book")

    assert result["url_encoded"] == "https://example.com/my-book"
    assert result["size_px"] == 300
    assert result["qr_code_data_uri"].startswith("data:image/png;base64,")
    assert len(result["qr_code_data_uri"]) > 30

    # Different URLs produce different QR data
    result2 = generate_qr_code("https://example.com/different-book")
    assert result["qr_code_data_uri"] != result2["qr_code_data_uri"]


# ── 7. Bundle Combines Volumes Correctly ─────────────────────────────────────


@pytest.mark.asyncio
async def test_bundle_combines_volumes():
    db = _make_mock_db()

    with patch("app.modules.specialty_books.service_series.BookBundle") as MockBundle:
        mock_bundle = MagicMock()
        mock_bundle.id = BUNDLE_ID
        mock_bundle.org_id = ORG_ID
        mock_bundle.title = "Animals Complete Collection"
        mock_bundle.book_type = "coloring"
        mock_bundle.volume_ids = [str(BOOK_ID_1), str(BOOK_ID_2)]
        mock_bundle.series_id = None
        mock_bundle.config = {
            "combined_toc": [
                {"volume_index": 1, "volume_title": "Animals Vol. 1", "start_page": 1, "page_count": 30},
                {"volume_index": 2, "volume_title": "Animals Vol. 2", "start_page": 31, "page_count": 30},
            ],
            "section_dividers": [{"after_page": 30, "title": "Animals Vol. 2"}],
            "combined_answer_key": False,
        }
        mock_bundle.total_pages = 61  # 30 + 30 + 1 divider
        mock_bundle.created_at = datetime(2026, 1, 1, tzinfo=UTC)
        MockBundle.return_value = mock_bundle

        result = await create_bundle(
            db,
            ORG_ID,
            {
                "title": "Animals Complete Collection",
                "book_type": "coloring",
                "volume_ids": [BOOK_ID_1, BOOK_ID_2],
                "volume_page_counts": [
                    {"title": "Animals Vol. 1", "page_count": 30},
                    {"title": "Animals Vol. 2", "page_count": 30},
                ],
            },
        )

    assert result["title"] == "Animals Complete Collection"
    assert result["total_pages"] == 61
    db.add.assert_called_once()


# ── 8. Bundle Generates Section Dividers ─────────────────────────────────────


@pytest.mark.asyncio
async def test_bundle_section_dividers():
    db = _make_mock_db()

    with patch("app.modules.specialty_books.service_series.BookBundle") as MockBundle:
        captured_config = {}

        def capture_init(**kwargs):
            captured_config.update(kwargs.get("config", {}))
            mock = MagicMock()
            mock.id = BUNDLE_ID
            mock.org_id = ORG_ID
            mock.title = kwargs.get("title", "")
            mock.book_type = kwargs.get("book_type", "")
            mock.volume_ids = kwargs.get("volume_ids", [])
            mock.series_id = kwargs.get("series_id")
            mock.config = kwargs.get("config")
            mock.total_pages = kwargs.get("total_pages", 0)
            mock.created_at = datetime(2026, 1, 1, tzinfo=UTC)
            return mock

        MockBundle.side_effect = capture_init

        await create_bundle(
            db,
            ORG_ID,
            {
                "title": "Big Bundle",
                "book_type": "puzzle",
                "volume_ids": [BOOK_ID_1, BOOK_ID_2],
                "volume_page_counts": [
                    {"title": "Puzzles Vol. 1", "page_count": 50},
                    {"title": "Puzzles Vol. 2", "page_count": 50},
                ],
                "config": {"combined_answers": True},
            },
        )

    assert len(captured_config["section_dividers"]) == 1
    assert captured_config["section_dividers"][0]["title"] == "Puzzles Vol. 2"
    assert captured_config["combined_answer_key"] is True
    assert len(captured_config["combined_toc"]) == 2


# ── 9. ISBN Add to Pool and Assignment ───────────────────────────────────────


@pytest.mark.asyncio
async def test_isbn_add_to_pool():
    db = _make_mock_db()

    with patch("app.modules.specialty_books.service_series.ISBNPool") as MockISBN:
        mock_record = MagicMock()
        mock_record.id = ISBN_ID
        mock_record.isbn = "9781234567897"
        mock_record.status = "available"
        MockISBN.return_value = mock_record

        result = await manage_isbn(
            db,
            ORG_ID,
            "add_to_pool",
            {
                "isbns": ["9781234567897"],
                "publisher_name": "Green Companies LLC",
            },
        )

    assert result["count"] == 1
    assert result["added"][0]["isbn"] == "9781234567897"


@pytest.mark.asyncio
async def test_isbn_assignment():
    db = _make_mock_db()

    isbn_record = MagicMock()
    isbn_record.id = ISBN_ID
    isbn_record.isbn = "9781234567897"
    isbn_record.status = "available"
    isbn_record.publisher_name = "Green Companies LLC"
    isbn_record.assigned_to_book_type = None
    isbn_record.assigned_to_book_id = None
    isbn_record.barcode_url = None

    db.execute = AsyncMock(return_value=_mock_scalar_one_or_none(isbn_record))

    result = await manage_isbn(
        db,
        ORG_ID,
        "assign",
        {
            "isbn": "9781234567897",
            "book_type": "coloring",
            "book_id": BOOK_ID_1,
        },
    )

    assert result["isbn"] == "9781234567897"
    assert result["status"] == "assigned"
    assert isbn_record.status == "assigned"
    assert isbn_record.assigned_to_book_id == BOOK_ID_1


# ── 10. ISBN Validation ──────────────────────────────────────────────────────


def test_isbn13_validation_valid():
    assert _validate_isbn13("9780306406157") is True
    assert _validate_isbn13("9781234567897") is True


def test_isbn13_validation_invalid():
    assert _validate_isbn13("9780306406158") is False
    assert _validate_isbn13("978030640615") is False
    assert _validate_isbn13("978030640615X") is False
    assert _validate_isbn13("") is False


# ── 11. Barcode Generation ───────────────────────────────────────────────────


def test_barcode_generation():
    result = _isbn_generate_barcode("9780306406157")

    assert result["isbn"] == "9780306406157"
    assert result["format"] == "EAN-13"
    assert result["valid"] is True
    assert result["barcode_data_uri"].startswith("data:image/png;base64,")
    assert result["placement_guide"]["position"] == "back_cover_bottom_right"
    assert result["placement_guide"]["min_width_mm"] == 36
    assert result["placement_guide"]["min_height_mm"] == 26
    assert result["placement_guide"]["quiet_zone_mm"] == 5


# ── 12. KDP Preflight Validates Correctly ────────────────────────────────────


@pytest.mark.asyncio
async def test_kdp_preflight_pass():
    db = _make_mock_db()

    with patch("app.modules.specialty_books.service_series.DistributorPreflight") as MockPF:
        mock_pf = MagicMock()
        mock_pf.id = uuid.uuid4()
        MockPF.return_value = mock_pf

        result = await run_distributor_preflight(
            db,
            "coloring",
            BOOK_ID_1,
            ORG_ID,
            "kdp",
            page_count=30,
        )

    assert result["distributor"] == "kdp"
    assert result["status"] == "PASSED"
    assert result["all_passed"] is True
    for check in result["checks"]:
        assert check["passed"] is True


@pytest.mark.asyncio
async def test_kdp_preflight_fail_page_count():
    db = _make_mock_db()

    with patch("app.modules.specialty_books.service_series.DistributorPreflight") as MockPF:
        mock_pf = MagicMock()
        mock_pf.id = uuid.uuid4()
        MockPF.return_value = mock_pf

        result = await run_distributor_preflight(
            db,
            "coloring",
            BOOK_ID_1,
            ORG_ID,
            "kdp",
            page_count=10,
        )

    assert result["status"] == "FAILED"
    assert result["all_passed"] is False
    page_check = next(c for c in result["checks"] if c["name"] == "page_count")
    assert page_check["passed"] is False
    assert "10" in page_check["details"]


# ── 13. IngramSpark Preflight Includes PDF/X-1a ─────────────────────────────


@pytest.mark.asyncio
async def test_ingram_preflight_has_pdfx1a_check():
    db = _make_mock_db()

    with patch("app.modules.specialty_books.service_series.DistributorPreflight") as MockPF:
        mock_pf = MagicMock()
        mock_pf.id = uuid.uuid4()
        MockPF.return_value = mock_pf

        result = await run_distributor_preflight(
            db,
            "coloring",
            BOOK_ID_1,
            ORG_ID,
            "ingram_spark",
            page_count=50,
        )

    check_names = [c["name"] for c in result["checks"]]
    assert "pdf_x1a" in check_names
    assert "icc_profile" in check_names
    assert "ink_density" in check_names
    assert len(result["checks"]) > 7
    assert result["status"] == "PASSED"


# ── 14. B&N Press Preflight Includes ISBN Check ──────────────────────────────


@pytest.mark.asyncio
async def test_bn_preflight_has_isbn_check():
    db = _make_mock_db()

    with patch("app.modules.specialty_books.service_series.DistributorPreflight") as MockPF:
        mock_pf = MagicMock()
        mock_pf.id = uuid.uuid4()
        MockPF.return_value = mock_pf

        result = await run_distributor_preflight(
            db,
            "coloring",
            BOOK_ID_1,
            ORG_ID,
            "bn_press",
            page_count=50,
        )

    check_names = [c["name"] for c in result["checks"]]
    assert "isbn" in check_names
    assert "cover_format" in check_names
    assert result["status"] == "PASSED"


# ── 15. Review Feedback Maps Complaints ──────────────────────────────────────


@pytest.mark.asyncio
async def test_review_feedback_maps_complaints():
    db = _make_mock_db()

    result = await process_review_feedback(
        db,
        "coloring",
        BOOK_ID_1,
        ORG_ID,
        ["pages thin", "colors washed", "text too small"],
    )

    assert len(result["mappings"]) == 3

    thin = result["mappings"][0]
    assert thin["complaint"] == "pages thin"
    assert "paper" in thin["suggested_fix"].lower()
    assert thin["automated_action_available"] is True

    washed = result["mappings"][1]
    assert washed["complaint"] == "colors washed"
    assert "cmyk" in washed["suggested_fix"].lower()

    small = result["mappings"][2]
    assert small["complaint"] == "text too small"
    assert "font" in small["suggested_fix"].lower() or "large" in small["suggested_fix"].lower()


@pytest.mark.asyncio
async def test_review_feedback_handles_unknown_complaint():
    db = _make_mock_db()

    result = await process_review_feedback(
        db,
        "puzzle",
        BOOK_ID_1,
        ORG_ID,
        ["completely random nonsensical complaint xyz"],
    )

    assert len(result["mappings"]) == 1
    assert result["mappings"][0]["automated_action_available"] is False
    assert "manual" in result["mappings"][0]["suggested_fix"].lower()


@pytest.mark.asyncio
async def test_review_feedback_puzzle_complaints():
    db = _make_mock_db()

    result = await process_review_feedback(
        db,
        "puzzle",
        BOOK_ID_1,
        ORG_ID,
        ["puzzles too easy", "answers wrong"],
    )

    easy = result["mappings"][0]
    assert "difficulty" in easy["suggested_fix"].lower()
    assert easy["automated_action_available"] is True

    wrong = result["mappings"][1]
    assert "answer" in wrong["suggested_fix"].lower() or "verify" in wrong["suggested_fix"].lower()
    assert wrong["automated_action_available"] is True


# ── 16. Complaint Matcher Unit Tests ─────────────────────────────────────────


def test_complaint_matcher_exact():
    match = _find_best_complaint_match("pages thin")
    assert match is not None
    assert "paper" in match["suggested_fix"].lower()


def test_complaint_matcher_partial():
    match = _find_best_complaint_match("the pages are thin and flimsy")
    assert match is not None
    assert "paper" in match["suggested_fix"].lower()


def test_complaint_matcher_no_match():
    match = _find_best_complaint_match("xyz abc definitely no match")
    assert match is None
