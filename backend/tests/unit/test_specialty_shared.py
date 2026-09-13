"""Unit tests for all specialty shared systems.

Blueprint Section 17.4 -- 21 test cases covering preflight, pricing,
color management, fingerprinting, spam detection, safety, font licensing,
metadata, review feedback, accessibility, device preview, and distributor.
"""

from __future__ import annotations

import pytest

from app.modules.specialty.shared.accessibility import (
    DYSLEXIA_SETTINGS,
    LARGE_PRINT_SETTINGS,
    generate_dyslexia_variant,
)
from app.modules.specialty.shared.color_management import (
    _is_out_of_gamut,
    calculate_ink_density,
    check_gamut,
    rgb_to_cmyk,
)
from app.modules.specialty.shared.device_preview import (
    DEVICE_SPECS,
    generate_all_previews,
    generate_preview,
)
from app.modules.specialty.shared.distributor import (
    _run_bn_checks,
    _run_ingram_checks,
    _run_kdp_checks,
)
from app.modules.specialty.shared.fingerprinting import (
    compare_fingerprints,
    generate_fingerprint,
)
from app.modules.specialty.shared.font_licensing import (
    check_font_license,
)
from app.modules.specialty.shared.metadata_advisor import (
    check_metadata_compliance,
)

# ---------------------------------------------------------------------------
# Imports under test
# ---------------------------------------------------------------------------
from app.modules.specialty.shared.preflight import (
    SPINE_WIDTH_PER_PAGE_BW,
    SPINE_WIDTH_PER_PAGE_COLOR,
    calculate_spine_width,
    run_preflight,
)
from app.modules.specialty.shared.print_pricing import (
    KDP_ROYALTY_RATE,
    calculate_print_cost,
    generate_price_scenarios,
)
from app.modules.specialty.shared.review_feedback import (
    analyze_feedback,
)
from app.modules.specialty.shared.safety import (
    scan_content_sensitivity,
    scan_text_for_trademarks,
)
from app.modules.specialty.shared.spam_detector import (
    _INTERIOR_SIMILARITY_THRESHOLD,
    _check_metadata_quality,
)

# ===================================================================
# 1. Preflight: DPI check catches <300 DPI
# ===================================================================


class TestPreflightDPI:
    def test_low_dpi_flagged_as_blocker(self):
        book_data = {
            "page_count": 32,
            "pages": [
                {"page_number": 1, "dpi": 200},
                {"page_number": 2, "dpi": 300},
            ],
        }
        report = run_preflight("childrens", book_data)
        dpi_checks = [c for c in report["checks"] if c["name"] == "dpi_check"]
        assert len(dpi_checks) == 1
        assert dpi_checks[0]["status"] == "failed"
        assert dpi_checks[0]["severity"] == "blocker"
        assert 1 in eval(dpi_checks[0]["details"].split(": ")[1])
        assert report["passed"] is False

    def test_all_pages_at_300_dpi_pass(self):
        book_data = {
            "page_count": 32,
            "pages": [
                {"page_number": 1, "dpi": 300},
                {"page_number": 2, "dpi": 350},
            ],
        }
        report = run_preflight("childrens", book_data)
        dpi_checks = [c for c in report["checks"] if c["name"] == "dpi_check"]
        assert dpi_checks[0]["status"] == "passed"


# ===================================================================
# 2. Preflight: Margin check catches insufficient bleed
# ===================================================================


class TestPreflightMargins:
    def test_insufficient_bleed_flagged(self):
        book_data = {
            "page_count": 32,
            "pages": [
                {
                    "page_number": 1,
                    "margins": {"top": 0.1, "bottom": 0.125, "left": 0.125, "right": 0.125},
                },
            ],
        }
        report = run_preflight("childrens", book_data)
        margin_checks = [c for c in report["checks"] if c["name"] == "margin_bleed_check"]
        assert margin_checks[0]["status"] == "failed"
        assert margin_checks[0]["severity"] == "blocker"

    def test_sufficient_bleed_passes(self):
        book_data = {
            "page_count": 32,
            "pages": [
                {
                    "page_number": 1,
                    "margins": {"top": 0.125, "bottom": 0.125, "left": 0.125, "right": 0.125},
                },
            ],
        }
        report = run_preflight("childrens", book_data)
        margin_checks = [c for c in report["checks"] if c["name"] == "margin_bleed_check"]
        assert margin_checks[0]["status"] == "passed"


# ===================================================================
# 3. Preflight: Gutter safety check works
# ===================================================================


class TestPreflightGutter:
    def test_content_in_gutter_zone_flagged(self):
        book_data = {
            "page_count": 32,
            "pages": [
                {"page_number": 1, "gutter_clearance_inches": 0.3},
            ],
        }
        report = run_preflight("childrens", book_data)
        gutter_checks = [c for c in report["checks"] if c["name"] == "gutter_safety_check"]
        assert gutter_checks[0]["status"] == "failed"
        assert gutter_checks[0]["severity"] == "blocker"

    def test_sufficient_gutter_clearance_passes(self):
        book_data = {
            "page_count": 32,
            "pages": [
                {"page_number": 1, "gutter_clearance_inches": 0.75},
            ],
        }
        report = run_preflight("childrens", book_data)
        gutter_checks = [c for c in report["checks"] if c["name"] == "gutter_safety_check"]
        assert gutter_checks[0]["status"] == "passed"


# ===================================================================
# 4. Preflight: Spine width calculation correct
# ===================================================================


class TestSpineWidth:
    def test_bw_spine_width(self):
        # 200 pages B&W: 200 * 0.0025 = 0.5
        result = calculate_spine_width(200, "bw")
        assert result == round(200 * SPINE_WIDTH_PER_PAGE_BW, 4)
        assert result == 0.5

    def test_color_spine_width(self):
        # 200 pages color: 200 * 0.002252 = 0.4504
        result = calculate_spine_width(200, "color")
        assert result == round(200 * SPINE_WIDTH_PER_PAGE_COLOR, 4)
        assert result == 0.4504

    def test_premium_color_uses_color_multiplier(self):
        result = calculate_spine_width(100, "premium_color")
        expected = round(100 * SPINE_WIDTH_PER_PAGE_COLOR, 4)
        assert result == expected

    def test_standard_color_uses_color_multiplier(self):
        result = calculate_spine_width(100, "standard_color")
        expected = round(100 * SPINE_WIDTH_PER_PAGE_COLOR, 4)
        assert result == expected


# ===================================================================
# 5. Print cost: B&W ($0.012/page + $0.85)
# ===================================================================


class TestPrintCostBW:
    def test_bw_100_pages(self):
        cost = calculate_print_cost(page_count=100, interior_type="bw")
        expected = round(0.012 * 100 + 0.85, 2)
        assert cost == expected  # 2.05

    def test_bw_32_pages(self):
        cost = calculate_print_cost(page_count=32, interior_type="bw")
        expected = round(0.012 * 32 + 0.85, 2)
        assert cost == expected  # 1.23


# ===================================================================
# 6. Print cost: Premium color ($0.07/page + $0.85)
# ===================================================================


class TestPrintCostColor:
    def test_premium_color_32_pages(self):
        cost = calculate_print_cost(page_count=32, interior_type="premium_color")
        expected = round(0.07 * 32 + 0.85, 2)
        assert cost == expected  # 3.09

    def test_premium_color_100_pages(self):
        cost = calculate_print_cost(page_count=100, interior_type="premium_color")
        expected = round(0.07 * 100 + 0.85, 2)
        assert cost == expected  # 7.85


# ===================================================================
# 7. Price scenarios: correct royalty calculations (60% rate)
# ===================================================================


class TestPriceScenarios:
    def test_royalty_rate_is_60_percent(self):
        assert KDP_ROYALTY_RATE == 0.60

    def test_30_percent_margin_scenario(self):
        cost = 2.05  # e.g. 100-page B&W
        scenarios = generate_price_scenarios(cost, target_margins=[30])
        assert len(scenarios) == 1
        s = scenarios[0]
        assert s["royalty_rate"] == 0.60
        # list_price = cost / (0.6 - 0.3) = 2.05 / 0.3 = 6.83
        expected_price = round(cost / 0.30, 2)
        assert s["list_price"] == expected_price
        # royalty = list_price * 0.6 - cost
        expected_royalty = round(expected_price * 0.60 - cost, 2)
        assert s["royalty_amount"] == expected_royalty

    def test_impossible_margin_returns_none(self):
        # 70% margin is impossible with 60% royalty rate
        cost = 2.05
        scenarios = generate_price_scenarios(cost, target_margins=[70])
        s = scenarios[0]
        assert s["list_price"] is None
        assert s["royalty_amount"] is None
        assert "not achievable" in s["note"]


# ===================================================================
# 8. RGB to CMYK: red (255,0,0) -> (0,100,100,0)
# ===================================================================


class TestRgbToCmyk:
    def test_pure_red(self):
        c, m, y, k = rgb_to_cmyk(255, 0, 0)
        assert c == 0.0
        assert m == 100.0
        assert y == 100.0
        assert k == 0.0

    def test_pure_black(self):
        c, m, y, k = rgb_to_cmyk(0, 0, 0)
        assert (c, m, y, k) == (0.0, 0.0, 0.0, 100.0)

    def test_pure_white(self):
        c, m, y, k = rgb_to_cmyk(255, 255, 255)
        assert (c, m, y, k) == (0.0, 0.0, 0.0, 0.0)

    def test_pure_green(self):
        c, m, y, k = rgb_to_cmyk(0, 255, 0)
        assert c == 100.0
        assert m == 0.0
        assert y == 100.0
        assert k == 0.0


# ===================================================================
# 9. Ink density: sum of CMYK channels
# ===================================================================


class TestInkDensity:
    def test_basic_density(self):
        density = calculate_ink_density(50.0, 30.0, 20.0, 10.0)
        assert density == 110.0

    def test_red_ink_density(self):
        # Pure red: C=0, M=100, Y=100, K=0 -> density=200
        c, m, y, k = rgb_to_cmyk(255, 0, 0)
        density = calculate_ink_density(c, m, y, k)
        assert density == 200.0

    def test_zero_density(self):
        density = calculate_ink_density(0, 0, 0, 0)
        assert density == 0.0


# ===================================================================
# 10. Out-of-gamut detection works
# ===================================================================


class TestGamutDetection:
    def test_vivid_blue_is_out_of_gamut(self):
        # Vivid blue: R=0, G=0, B=255
        assert _is_out_of_gamut(0, 0, 255) is True

    def test_electric_green_is_out_of_gamut(self):
        # Electric green: R=0, G=255, B=0
        assert _is_out_of_gamut(0, 255, 0) is True

    def test_safe_grey_is_in_gamut(self):
        # Mid-grey: should not be out of gamut
        assert _is_out_of_gamut(128, 128, 128) is False

    def test_check_gamut_returns_alternatives(self):
        colors = [(0, 0, 255), (128, 128, 128), (0, 255, 0)]
        results = check_gamut(colors)
        # Two out of gamut, one safe
        assert len(results) >= 2
        for r in results:
            assert "original_rgb" in r
            assert "adjusted_rgb" in r
            assert "cmyk" in r


# ===================================================================
# 11. Fingerprint generation: consistent hashes
# ===================================================================


class TestFingerprinting:
    def test_image_fingerprint_consistent(self):
        data = bytes(range(64))
        fp1 = generate_fingerprint("images", data)
        fp2 = generate_fingerprint("images", data)
        assert fp1.fingerprint == fp2.fingerprint
        assert fp1.method == "average_hash"

    def test_puzzle_grid_fingerprint_consistent(self):
        grid = [[1, 2, 3], [4, 5, 6]]
        fp1 = generate_fingerprint("puzzle_grids", grid)
        fp2 = generate_fingerprint("puzzle_grids", grid)
        assert fp1.fingerprint == fp2.fingerprint
        assert fp1.method == "sha256_grid"

    def test_text_fingerprint_consistent(self):
        text = "The quick brown fox jumps over the lazy dog"
        fp1 = generate_fingerprint("text", text)
        fp2 = generate_fingerprint("text", text)
        assert fp1.fingerprint == fp2.fingerprint
        assert fp1.method == "ngram_3"

    def test_word_list_fingerprint_consistent(self):
        words = ["apple", "banana", "cherry"]
        fp1 = generate_fingerprint("word_lists", words)
        fp2 = generate_fingerprint("word_lists", words)
        assert fp1.fingerprint == fp2.fingerprint
        assert fp1.method == "jaccard"


# ===================================================================
# 12. Fingerprint comparison: correct similarity scores
# ===================================================================


class TestFingerprintComparison:
    def test_identical_images_score_1(self):
        data = bytes(range(64))
        fp1 = generate_fingerprint("images", data)
        fp2 = generate_fingerprint("images", data)
        score = compare_fingerprints(fp1, fp2)
        assert score == 1.0

    def test_identical_puzzle_grids_score_1(self):
        grid = [[1, 2], [3, 4]]
        fp1 = generate_fingerprint("puzzle_grids", grid)
        fp2 = generate_fingerprint("puzzle_grids", grid)
        assert compare_fingerprints(fp1, fp2) == 1.0

    def test_different_puzzle_grids_score_0(self):
        fp1 = generate_fingerprint("puzzle_grids", [[1, 2], [3, 4]])
        fp2 = generate_fingerprint("puzzle_grids", [[5, 6], [7, 8]])
        assert compare_fingerprints(fp1, fp2) == 0.0

    def test_identical_word_lists_score_1(self):
        words = ["alpha", "beta", "gamma"]
        fp1 = generate_fingerprint("word_lists", words)
        fp2 = generate_fingerprint("word_lists", words)
        assert compare_fingerprints(fp1, fp2) == 1.0

    def test_overlapping_word_lists_partial_score(self):
        fp1 = generate_fingerprint("word_lists", ["apple", "banana", "cherry"])
        fp2 = generate_fingerprint("word_lists", ["apple", "banana", "date"])
        score = compare_fingerprints(fp1, fp2)
        # Jaccard: intersection=2, union=4 -> 0.5
        assert score == 0.5

    def test_identical_text_score_1(self):
        text = "The quick brown fox jumps over the lazy dog"
        fp1 = generate_fingerprint("text", text)
        fp2 = generate_fingerprint("text", text)
        score = compare_fingerprints(fp1, fp2)
        assert score == pytest.approx(1.0)


# ===================================================================
# 13. Spam risk: >60% similarity flagged
# ===================================================================


class TestSpamDetector:
    def test_threshold_is_60_percent(self):
        assert _INTERIOR_SIMILARITY_THRESHOLD == 0.60

    def test_keyword_stuffed_title_flagged(self):
        # Title with >4 keyword segments
        penalty, factors, recs = _check_metadata_quality(
            title="Coloring Book | Animals | Kids | Fun | Activity | Games",
        )
        assert penalty > 0
        assert any(f["check"] == "metadata_keyword_stuffing" for f in factors)

    def test_clean_title_no_penalty(self):
        penalty, factors, recs = _check_metadata_quality(
            title="My Wonderful Animal Adventures",
            description="A delightful collection of animal stories for young readers aged 3-7.",
        )
        assert penalty == 0.0
        assert len(factors) == 0


# ===================================================================
# 14. Trademark scanner: finds blocked terms with positions
# ===================================================================


class TestTrademarkScanner:
    def test_finds_disney_with_position(self):
        text = "A story about Disney characters"
        results = scan_text_for_trademarks(text)
        disney_hits = [r for r in results if r["term"] == "disney"]
        assert len(disney_hits) >= 1
        assert disney_hits[0]["position"] == text.lower().find("disney")

    def test_finds_multiple_trademarks(self):
        text = "A Pokemon and Marvel adventure"
        results = scan_text_for_trademarks(text)
        terms_found = {r["term"] for r in results}
        assert "pokemon" in terms_found
        assert "marvel" in terms_found

    def test_clean_text_returns_empty(self):
        text = "A lovely story about a friendly cat and a curious dog"
        results = scan_text_for_trademarks(text)
        assert len(results) == 0

    def test_artist_style_reference_flagged(self):
        text = "Draw this in the style of Pablo Picasso"
        results = scan_text_for_trademarks(text)
        style_hits = [r for r in results if "artist style reference" in r["term"]]
        assert len(style_hits) >= 1


# ===================================================================
# 15. Content sensitivity: categorizes issues correctly
# ===================================================================


class TestContentSensitivity:
    def test_violence_category_detected(self):
        text = "The hero used a gun to fight the enemy"
        results = scan_content_sensitivity(text, audience="kids")
        categories = {r["category"] for r in results}
        assert "violence" in categories

    def test_substance_reference_detected(self):
        text = "The character was drinking beer at the bar"
        results = scan_content_sensitivity(text, audience="kids")
        categories = {r["category"] for r in results}
        assert "substance_references" in categories

    def test_adults_audience_only_flags_high_severity(self):
        # "gun" is medium severity, should not be flagged for adults
        text = "The character held a gun"
        results = scan_content_sensitivity(text, audience="adults")
        gun_hits = [r for r in results if "gun" in r["text"].lower()]
        # For adults, medium-severity items should be filtered out
        assert len(gun_hits) == 0

    def test_clean_text_no_flags(self):
        text = "The bunny hopped through the meadow"
        results = scan_content_sensitivity(text, audience="kids")
        assert len(results) == 0


# ===================================================================
# 16. Font licensing: safe vs unsafe
# ===================================================================


class TestFontLicensing:
    def test_known_safe_font(self):
        result = check_font_license("Open Sans")
        assert result["safe"] is True
        assert result["license_type"] == "sil_ofl"

    def test_unknown_font_unsafe(self):
        result = check_font_license("SomeProprietaryFont")
        assert result["safe"] is False
        assert result["license_type"] == "unknown"

    def test_case_insensitive_match(self):
        result = check_font_license("open sans")
        assert result["safe"] is True

    def test_opendyslexic_is_safe(self):
        result = check_font_license("OpenDyslexic")
        assert result["safe"] is True


# ===================================================================
# 17. Metadata compliance: catches keyword stuffing
# ===================================================================


class TestMetadataCompliance:
    def test_too_many_keywords(self):
        result = check_metadata_compliance(
            title="My Book",
            keywords=["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7", "kw8"],
        )
        kw_issues = [i for i in result["issues"] if "Too many keywords" in i]
        assert len(kw_issues) == 1

    def test_trademark_in_title(self):
        result = check_metadata_compliance(title="My Disney Adventure")
        tm_issues = [i for i in result["issues"] if "trademarked" in i.lower()]
        assert len(tm_issues) >= 1

    def test_restricted_phrase_in_title(self):
        result = check_metadata_compliance(title="Best Seller Coloring Book")
        restricted = [i for i in result["issues"] if "restricted" in i.lower()]
        assert len(restricted) >= 1

    def test_clean_metadata_no_issues(self):
        result = check_metadata_compliance(
            title="Wonderful Animal Adventures",
            description="A delightful collection of stories for children aged 3-7, featuring colorful illustrations and fun activities.",
            keywords=["animals", "children", "adventure", "coloring", "activity", "bedtime", "learning"],
        )
        assert len(result["issues"]) == 0


# ===================================================================
# 18. Review feedback: maps complaints to fixes
# ===================================================================


class TestReviewFeedback:
    def test_pages_thin_maps_to_print_quality(self):
        results = analyze_feedback(["pages thin"])
        assert len(results) == 1
        assert results[0].category == "print_quality"
        assert results[0].action == "change_paper_type"

    def test_too_easy_maps_to_difficulty(self):
        results = analyze_feedback(["too easy"])
        assert len(results) == 1
        assert results[0].category == "difficulty"
        assert results[0].action == "adjust_difficulty_up"

    def test_alias_maps_correctly(self):
        results = analyze_feedback(["blurry"])
        assert len(results) == 1
        assert results[0].category == "image_quality"
        assert results[0].action == "check_image_dpi"

    def test_unknown_complaint_gets_manual_review(self):
        results = analyze_feedback(["completely unique complaint xyz123"])
        assert len(results) == 1
        assert results[0].category == "unknown"
        assert results[0].action == "manual_review"

    def test_multiple_complaints(self):
        results = analyze_feedback(["pages thin", "answers wrong", "too hard"])
        assert len(results) == 3
        categories = [r.category for r in results]
        assert "print_quality" in categories
        assert "answer_keys" in categories
        assert "difficulty" in categories


# ===================================================================
# 19. Accessibility: dyslexia variant settings correct
# ===================================================================


class TestAccessibility:
    def test_dyslexia_settings_font(self):
        assert DYSLEXIA_SETTINGS["font_family"] == "OpenDyslexic"

    def test_dyslexia_settings_line_spacing(self):
        assert DYSLEXIA_SETTINGS["line_spacing_multiplier"] == 1.5

    def test_dyslexia_variant_applies_settings(self):
        book_data = {
            "pages": [
                {
                    "page_number": 1,
                    "text_content": "Hello world",
                    "font_family": "Arial",
                    "line_spacing": 1.0,
                    "text_align": "justify",
                },
            ],
        }
        variant = generate_dyslexia_variant(book_data)
        page = variant["pages"][0]
        assert page["font_family"] == "OpenDyslexic"
        assert page["line_spacing"] == 1.5  # 1.0 * 1.5
        assert page["text_align"] == "left"
        assert page["background_color"] == "#FFFDF5"
        assert page["text_color"] == "#333333"
        assert page["letter_spacing_pct"] == 15

    def test_dyslexia_variant_metadata(self):
        book_data = {"pages": [{"page_number": 1, "text_content": "Test"}]}
        variant = generate_dyslexia_variant(book_data)
        assert variant["variant_metadata"]["variant_type"] == "dyslexia_friendly"

    def test_large_print_settings(self):
        assert LARGE_PRINT_SETTINGS["min_body_font_pt"] == 18
        assert LARGE_PRINT_SETTINGS["contrast_ratio_min"] == 7.0


# ===================================================================
# 20. Device preview: correct specs for all 6 devices
# ===================================================================


class TestDevicePreview:
    def test_all_six_devices_present(self):
        expected = {
            "kindle_fire_hd_10",
            "kindle_fire_hd_8",
            "kindle_paperwhite",
            "ipad_10_2",
            "ipad_mini_8_3",
            "iphone_15",
        }
        assert set(DEVICE_SPECS.keys()) == expected

    @pytest.mark.parametrize("device_key", list(DEVICE_SPECS.keys()))
    def test_device_has_required_fields(self, device_key):
        spec = DEVICE_SPECS[device_key]
        assert "name" in spec
        assert "width" in spec
        assert "height" in spec
        assert "dpi" in spec
        assert isinstance(spec["width"], int)
        assert isinstance(spec["height"], int)
        assert isinstance(spec["dpi"], int)

    def test_kindle_fire_hd_10_specs(self):
        spec = DEVICE_SPECS["kindle_fire_hd_10"]
        assert spec["width"] == 1920
        assert spec["height"] == 1200
        assert spec["dpi"] == 224

    def test_kindle_paperwhite_is_grayscale(self):
        spec = DEVICE_SPECS["kindle_paperwhite"]
        assert spec.get("grayscale") is True
        assert spec["dpi"] == 300

    def test_iphone_15_has_notch(self):
        spec = DEVICE_SPECS["iphone_15"]
        assert spec.get("has_notch") is True
        assert spec["dpi"] == 460

    def test_generate_preview_returns_correct_structure(self):
        page_data = {"width": 2550, "height": 3300, "text_font_size": 18}
        preview = generate_preview(page_data, "kindle_fire_hd_10")
        assert preview["device"] == "kindle_fire_hd_10"
        assert preview["device_name"] == "Kindle Fire HD 10"
        assert "scaling" in preview
        assert "text_readability" in preview
        assert "device_frame" in preview

    def test_generate_all_previews_covers_all_devices(self):
        page_data = {"width": 2550, "height": 3300, "text_font_size": 18}
        result = generate_all_previews(page_data)
        assert result["summary"]["total_devices"] == 6
        assert len(result["previews"]) == 6

    def test_unknown_device_raises(self):
        with pytest.raises(ValueError, match="Unknown device"):
            generate_preview({}, "nonexistent_device")


# ===================================================================
# 21. Distributor preflight: correct checks per distributor
# ===================================================================


class TestDistributorPreflight:
    def test_kdp_checks_page_count(self):
        book_data = {"page_count": 10, "interior_type": "bw"}
        checks = _run_kdp_checks(book_data)
        page_checks = [c for c in checks if "page_count" in c.name]
        assert len(page_checks) >= 1
        failed = [c for c in page_checks if not c.passed]
        assert len(failed) >= 1  # 10 pages < 24 minimum

    def test_kdp_checks_file_size(self):
        book_data = {"page_count": 100, "file_size_mb": 700}
        checks = _run_kdp_checks(book_data)
        size_checks = [c for c in checks if "file_size" in c.name]
        assert len(size_checks) == 1
        assert size_checks[0].passed is False  # 700 > 650 limit

    def test_kdp_valid_book_passes(self):
        book_data = {
            "page_count": 100,
            "interior_type": "bw",
            "file_size_mb": 50,
            "cover_dpi": 300,
            "trim_size": "6x9",
        }
        checks = _run_kdp_checks(book_data)
        failures = [c for c in checks if not c.passed]
        assert len(failures) == 0

    def test_ingram_requires_pdfx1a(self):
        book_data = {"page_count": 100, "pdf_standard": "standard PDF"}
        checks = _run_ingram_checks(book_data)
        pdf_checks = [c for c in checks if "pdf_standard" in c.name]
        assert len(pdf_checks) == 1
        assert pdf_checks[0].passed is False

    def test_ingram_requires_cmyk(self):
        book_data = {"page_count": 100, "color_space": "RGB"}
        checks = _run_ingram_checks(book_data)
        color_checks = [c for c in checks if "color_space" in c.name]
        assert len(color_checks) == 1
        assert color_checks[0].passed is False

    def test_ingram_requires_icc_profile(self):
        book_data = {"page_count": 100, "icc_profile_embedded": False}
        checks = _run_ingram_checks(book_data)
        icc_checks = [c for c in checks if "icc_profile" in c.name]
        assert len(icc_checks) == 1
        assert icc_checks[0].passed is False

    def test_bn_press_checks_cover_dimensions(self):
        book_data = {"cover_width_px": 800, "cover_height_px": 800}
        checks = _run_bn_checks(book_data)
        cover_checks = [c for c in checks if "cover_dimensions" in c.name]
        assert len(cover_checks) == 1
        assert cover_checks[0].passed is False  # 800 < 1400

    def test_bn_press_valid_cover_passes(self):
        book_data = {
            "cover_width_px": 2000,
            "cover_height_px": 2000,
            "page_count": 100,
            "interior_type": "bw",
        }
        checks = _run_bn_checks(book_data)
        cover_checks = [c for c in checks if "cover_dimensions" in c.name]
        assert cover_checks[0].passed is True
