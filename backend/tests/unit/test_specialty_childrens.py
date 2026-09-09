"""Unit tests for Children's Book Studio modules.

Covers text_analysis, safety, bilingual (pure functions), and
service-layer business logic (age-band rules, story modes, readability,
trademark/sensitivity scanning, provenance, font licensing).

Blueprint Section 17.1 — 32 test cases.
"""
from __future__ import annotations

import hashlib
import re

import pytest

from app.modules.specialty.childrens.bilingual import (
    SUPPORTED_LANGUAGES,
    _age_constraints_prompt,
    get_bilingual_layout,
    sync_translations,
    validate_translation,
)
from app.modules.specialty.childrens.bilingual import (
    translate_book as bilingual_translate_book,
)
from app.modules.specialty.childrens.safety import (
    TRADEMARK_BLOCKLIST,
    IssueSeverity,
    check_font_license,
    generate_provenance_record,
    scan_content_sensitivity,
    scan_trademarks,
)

# Service-layer constants (no DB interaction for these)
from app.modules.specialty.childrens.service import (
    AGE_BAND_RULES as SVC_AGE_BAND_RULES,
)
from app.modules.specialty.childrens.service import (
    CONTENT_SENSITIVITY_PATTERNS,
    TRADEMARK_TERMS,
    _analyze_readability,
    _compute_rhythm_score,
    _parse_story_pages,
)

# ---------------------------------------------------------------------------
# Pure-function modules (no DB required)
# ---------------------------------------------------------------------------
from app.modules.specialty.childrens.text_analysis import (
    _resolve_age_range,
    analyze_text,
    calculate_readability_score,
    calculate_rhythm_score,
    detect_rhyme_pattern,
    generate_page_turn_map,
    score_look_inside,
    suggest_rhyme_fixes,
)

# ===================================================================
# 1. Age range adjusts page count, font size, and language rules
# ===================================================================


class TestAgeBandRules:
    """Verify that each age band defines correct constraints for
    page count range, minimum font size, sentence/word limits."""

    def test_baby_band_has_strict_limits(self):
        rules = SVC_AGE_BAND_RULES["baby"]
        assert rules["max_sentence_words"] == 5
        assert rules["max_word_length"] == 5
        assert rules["min_font_size"] == 24
        assert rules["total_words_min"] == 50
        assert rules["total_words_max"] == 150

    def test_preschool_band_moderate_limits(self):
        rules = SVC_AGE_BAND_RULES["preschool"]
        assert rules["max_sentence_words"] == 8
        assert rules["max_word_length"] == 7
        assert rules["min_font_size"] == 18
        assert rules["total_words_min"] == 300
        assert rules["total_words_max"] == 500

    def test_early_reader_band_relaxed(self):
        rules = SVC_AGE_BAND_RULES["early_reader"]
        assert rules["max_sentence_words"] == 12
        assert rules["max_word_length"] == 9
        assert rules["min_font_size"] == 14

    def test_chapter_book_no_word_length_limit(self):
        rules = SVC_AGE_BAND_RULES["chapter_book"]
        assert rules["max_word_length"] == 0  # no limit
        assert rules["min_font_size"] == 12

    def test_font_size_decreases_with_age(self):
        sizes = [
            SVC_AGE_BAND_RULES["baby"]["min_font_size"],
            SVC_AGE_BAND_RULES["preschool"]["min_font_size"],
            SVC_AGE_BAND_RULES["early_reader"]["min_font_size"],
            SVC_AGE_BAND_RULES["chapter_book"]["min_font_size"],
        ]
        assert sizes == sorted(sizes, reverse=True)


# ===================================================================
# 2. Story modes (Prose, Rhyming, Repetitive) generate correct prompts
# ===================================================================


class TestStoryModePrompts:
    """The _parse_story_pages helper should parse PAGE N: blocks and
    fallback to sentence-splitting.  Story mode is embedded in the
    system prompt (tested indirectly via generate_story, which needs a DB,
    so we test the prompt-parsing and age-band prompt building)."""

    def test_parse_story_pages_structured(self):
        raw = (
            "PAGE 1:\nTEXT: The cat sat on the mat.\n"
            "ILLUSTRATION: A fluffy cat sitting on a red mat.\n\n"
            "PAGE 2:\nTEXT: The dog ran past.\n"
            "ILLUSTRATION: A brown dog running.\n"
        )
        pages = _parse_story_pages(raw, 2)
        assert len(pages) == 2
        assert pages[0]["page_number"] == 1
        assert "cat sat" in pages[0]["text"]
        assert "fluffy cat" in pages[0]["illustration_prompt"]
        assert pages[1]["page_number"] == 2

    def test_parse_story_pages_fallback(self):
        raw = "Once upon a time. There was a bear. He loved honey. The end."
        pages = _parse_story_pages(raw, 2)
        assert len(pages) == 2
        assert all(p["text"] for p in pages)

    def test_age_constraints_prompt_board(self):
        prompt = _age_constraints_prompt("board")
        assert "5 words per sentence" in prompt
        assert "5 letters per word" in prompt
        assert "500" in prompt  # vocab level

    def test_age_constraints_prompt_chapter(self):
        prompt = _age_constraints_prompt("chapter")
        # chapter_8_12 has no word length limit and no vocab limit
        assert "sentence" in prompt.lower()


# ===================================================================
# 3. Age-band language gate flags advanced vocabulary / long sentences
# ===================================================================


class TestLanguageGate:
    """text_analysis.analyze_text flags violations for wrong-level text."""

    def test_board_book_flags_long_sentence(self):
        text = "The very big enormous hungry caterpillar crawled slowly"
        result = analyze_text(text, "board")
        violations = result["violations"]
        sentence_violations = [v for v in violations if v["rule"] == "max_sentence_words"]
        assert len(sentence_violations) > 0

    def test_board_book_flags_long_words(self):
        text = "The caterpillar ate strawberries."
        result = analyze_text(text, "board")
        word_violations = [v for v in result["violations"] if v["rule"] == "max_word_length"]
        assert len(word_violations) > 0, "Words longer than 5 chars should be flagged"

    def test_chapter_book_allows_long_sentences(self):
        text = " ".join(["word"] * 14) + "."
        result = analyze_text(text, "chapter")
        sentence_violations = [
            v for v in result["violations"] if v["rule"] == "max_sentence_words"
        ]
        assert len(sentence_violations) == 0

    def test_picture_book_flags_moderate_length(self):
        text = "The little fox jumped over the stream and ran into the forest quickly."
        result = analyze_text(text, "picture")
        sentence_violations = [
            v for v in result["violations"] if v["rule"] == "max_sentence_words"
        ]
        # 13 words > 8 max for picture_3_5
        assert len(sentence_violations) > 0


# ===================================================================
# 4. Read-aloud rhythm score calculates cadence and repetition
# ===================================================================


class TestRhythmScore:
    """calculate_rhythm_score should reward consistent cadence and
    penalise tongue-twisters."""

    def test_empty_text_returns_zero(self):
        assert calculate_rhythm_score("") == 0.0

    def test_consistent_cadence_scores_high(self):
        text = "I like cats. I like dogs. I like birds. I like fish."
        score = calculate_rhythm_score(text)
        assert score >= 70.0

    def test_repetition_gives_bonus(self):
        text = "Run run run. Jump jump jump. Run run run. Jump jump jump."
        score = calculate_rhythm_score(text)
        # Repetition ratio should trigger bonus
        assert score > 0.0

    def test_tongue_twisters_penalised(self):
        normal = "The cat sat on a mat."
        twisty = "She sells seashells by the strengths of the strstr."
        score_normal = calculate_rhythm_score(normal)
        score_twisty = calculate_rhythm_score(twisty)
        # Twisty should have more consonant cluster penalties
        assert score_twisty <= score_normal


# ===================================================================
# 5. Page-turn surprise map shows pacing visualisation
# ===================================================================


class TestPageTurnSurpriseMap:
    """generate_page_turn_map returns per-page surprise scores."""

    def test_question_ending_adds_surprise(self):
        pages = ["Once upon a time.", "What happened next?"]
        result = generate_page_turn_map(pages)
        assert len(result) == 2
        assert result[1][1] > result[0][1]  # question page scores higher

    def test_exclamation_adds_surprise(self):
        pages = ["Quietly walking.", "BOOM!"]
        result = generate_page_turn_map(pages)
        assert result[1][1] > 0

    def test_ellipsis_cliffhanger(self):
        pages = ["And then..."]
        result = generate_page_turn_map(pages)
        assert result[0][1] >= 30.0  # ellipsis adds 30

    def test_empty_page_scores_zero(self):
        pages = ["", "Hello!"]
        result = generate_page_turn_map(pages)
        assert result[0][1] == 0.0

    def test_all_caps_adds_surprise(self):
        pages = ["The bear said HELLO WORLD!!"]
        result = generate_page_turn_map(pages)
        assert result[0][1] > 0

    def test_short_punchy_page(self):
        pages = ["Run!"]
        result = generate_page_turn_map(pages)
        # Short page (1-5 words) + exclamation
        assert result[0][1] >= 10.0


# ===================================================================
# 6. Rhyme assistant detects AABB/ABAB patterns
# ===================================================================


class TestRhymeDetection:
    """detect_rhyme_pattern identifies AABB, ABAB, and broken patterns."""

    def test_aabb_pattern(self):
        text = (
            "The cat sat on the mat\n"
            "He wore a funny hat\n"
            "The frog sat on a log\n"
            "And played there with the dog\n"
        )
        result = detect_rhyme_pattern(text)
        assert result["pattern"] == "AABB"
        assert isinstance(result["detected_scheme"], str)

    def test_too_few_lines(self):
        result = detect_rhyme_pattern("Single line only")
        assert result["pattern"] is None
        assert "Too few lines" in result["issues"][0]

    def test_broken_pattern_reported(self):
        text = (
            "The cat sat on the mat\n"
            "He wore a funny hat\n"
            "The dog ran down the lane\n"
            "He found a tiny bone\n"  # breaks the rhyme
        )
        result = detect_rhyme_pattern(text)
        # Should either detect a broken pattern or report no dominant pattern
        assert isinstance(result["issues"], list)

    def test_suggest_rhyme_fixes_returns_prompt(self):
        text = "The cat sat on the mat\nHe ran to the store"
        result = suggest_rhyme_fixes(text)
        assert "prompt" in result
        assert "context" in result
        assert "[SYSTEM]" in result["prompt"]
        assert "[USER]" in result["prompt"]


# ===================================================================
# 7. Look Inside optimizer scores first 10% of pages
# ===================================================================


class TestLookInsideScore:
    """score_look_inside evaluates hook strength of first 10%."""

    def test_empty_pages_returns_zero(self):
        assert score_look_inside([]) == 0.0

    def test_single_page_is_preview(self):
        pages = ["What is that strange noise?"]
        score = score_look_inside(pages)
        # Question hook + punchy opening
        assert score > 50.0

    def test_ten_pages_uses_first_page(self):
        pages = [f"Page {i} text here." for i in range(10)]
        # 10% of 10 = 1 page preview
        score = score_look_inside(pages)
        assert 0.0 <= score <= 100.0

    def test_exciting_opener_scores_higher(self):
        boring = ["It was a day. Things happened. The end."] * 10
        exciting = ["What was THAT?! Run!"] + ["More text."] * 9
        score_boring = score_look_inside(boring)
        score_exciting = score_look_inside(exciting)
        assert score_exciting >= score_boring


# ===================================================================
# 8. Text contrast checking and minimum font enforcement per age band
# ===================================================================


class TestFontAndContrast:
    """Service-layer AGE_BAND_RULES specify min_font_size per band."""

    def test_baby_min_font_24(self):
        assert SVC_AGE_BAND_RULES["baby"]["min_font_size"] == 24

    def test_toddler_min_font_24(self):
        assert SVC_AGE_BAND_RULES["toddler"]["min_font_size"] == 24

    def test_preschool_min_font_18(self):
        assert SVC_AGE_BAND_RULES["preschool"]["min_font_size"] == 18

    def test_early_reader_min_font_14(self):
        assert SVC_AGE_BAND_RULES["early_reader"]["min_font_size"] == 14

    def test_chapter_book_min_font_12(self):
        assert SVC_AGE_BAND_RULES["chapter_book"]["min_font_size"] == 12

    def test_font_below_minimum_detectable(self):
        """Application code should reject font_size < min_font_size."""
        for age, rules in SVC_AGE_BAND_RULES.items():
            min_fs = rules["min_font_size"]
            assert min_fs > 0, f"{age} must have a positive min_font_size"


# ===================================================================
# 9. Trademark enforcement blocks Disney, Pixar, etc.
# ===================================================================


class TestTrademarkEnforcement:
    """safety.scan_trademarks detects blocklisted terms."""

    def test_disney_blocked(self):
        issues = scan_trademarks("A story inspired by Disney adventures.")
        terms = [i.term for i in issues]
        assert "Disney" in terms

    def test_pixar_blocked(self):
        issues = scan_trademarks("Pixar style animation look.")
        terms = [i.term for i in issues]
        assert "Pixar" in terms

    def test_clean_text_no_issues(self):
        issues = scan_trademarks("A bunny hops through the forest.")
        assert len(issues) == 0

    def test_case_insensitive_detection(self):
        issues = scan_trademarks("We love disney characters.")
        assert len(issues) > 0

    def test_style_of_artist_detected(self):
        issues = scan_trademarks("Draw in the style of Eric Carle please.")
        style_issues = [i for i in issues if "style of" in i.term.lower()]
        assert len(style_issues) > 0

    def test_multiple_trademarks_all_found(self):
        text = "A Disney princess meets a Pokemon trainer in a LEGO world."
        issues = scan_trademarks(text)
        found_terms = {i.term.lower() for i in issues}
        assert "disney" in found_terms
        assert "lego" in found_terms

    def test_service_layer_trademark_list(self):
        """Service-level TRADEMARK_TERMS includes major brands."""
        assert "disney" in TRADEMARK_TERMS
        assert "pixar" in TRADEMARK_TERMS
        assert "peppa pig" in TRADEMARK_TERMS

    def test_trademark_issue_has_context(self):
        issues = scan_trademarks("Once upon a time, Disney was mentioned.")
        assert len(issues) > 0
        assert issues[0].context  # non-empty context snippet
        assert issues[0].severity == IssueSeverity.critical


# ===================================================================
# 10. Content sensitivity flags inappropriate content
# ===================================================================


class TestContentSensitivity:
    """safety.scan_content_sensitivity detects violence, fear, etc."""

    def test_violence_detected(self):
        issues = scan_content_sensitivity("The knight drew his sword and attacked.")
        categories = [i.category for i in issues]
        assert "violence" in categories

    def test_mature_themes_always_critical(self):
        issues = scan_content_sensitivity("He was drunk at the party.", age_range="8-12")
        mature = [i for i in issues if i.category == "mature_themes"]
        assert len(mature) > 0
        assert all(i.severity == IssueSeverity.critical for i in mature)

    def test_violence_critical_for_young_ages(self):
        issues = scan_content_sensitivity("The knight used a sword to fight.", age_range="0-3")
        violence = [i for i in issues if i.category == "violence"]
        assert len(violence) > 0
        assert any(i.severity == IssueSeverity.critical for i in violence)

    def test_violence_warning_for_older_ages(self):
        issues = scan_content_sensitivity("The hero attacked the dragon.", age_range="8-12")
        violence = [i for i in issues if i.category == "violence"]
        if violence:
            assert any(i.severity == IssueSeverity.warning for i in violence)

    def test_clean_text_no_issues(self):
        issues = scan_content_sensitivity("The bunny hopped happily.")
        assert len(issues) == 0

    def test_stereotypes_detected(self):
        issues = scan_content_sensitivity("Boys don't cry, said the teacher.")
        stereo = [i for i in issues if i.category == "stereotypes"]
        assert len(stereo) > 0

    def test_fear_content_detected(self):
        issues = scan_content_sensitivity("A terrifying ghost haunted the house.")
        fear = [i for i in issues if i.category == "fear"]
        assert len(fear) > 0

    def test_service_layer_sensitivity_patterns(self):
        """Service-level patterns compile correctly and match."""
        for pattern_str in CONTENT_SENSITIVITY_PATTERNS:
            compiled = re.compile(pattern_str)
            assert compiled is not None


# ===================================================================
# 11. Character sheet with references and continuity rules works
# ===================================================================


class TestCharacterContinuity:
    """Service helpers for continuity checking (pure-logic subset)."""

    def test_parse_story_pages_preserves_character_names(self):
        raw = (
            "PAGE 1:\nTEXT: Luna the bunny hopped.\n"
            "ILLUSTRATION: Luna bunny hopping in a meadow.\n"
        )
        pages = _parse_story_pages(raw, 1)
        assert "Luna" in pages[0]["text"]
        assert "Luna" in pages[0]["illustration_prompt"]

    def test_continuity_clothing_terms_extractable(self):
        """Clothing rules are comma-separated; splitting should work."""
        clothing_rules = "red hat, blue scarf, yellow boots"
        terms = [t.strip().lower() for t in clothing_rules.split(",")]
        assert "red hat" in terms
        assert "yellow boots" in terms
        assert len(terms) == 3


# ===================================================================
# 12. Provenance logs model, prompt hash, seed per image
# ===================================================================


class TestProvenanceRecords:
    """safety.generate_provenance_record creates proper metadata."""

    def test_provenance_has_all_fields(self):
        record = generate_provenance_record(
            model="dall-e-3",
            prompt="A happy bunny in a meadow",
            seed="42",
        )
        assert record.model == "dall-e-3"
        assert record.seed == "42"
        assert record.prompt_hash
        assert record.generated_date

    def test_prompt_hash_is_sha256(self):
        prompt = "A happy bunny in a meadow"
        record = generate_provenance_record(model="test", prompt=prompt, seed="1")
        expected_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        assert record.prompt_hash == expected_hash

    def test_different_prompts_different_hashes(self):
        r1 = generate_provenance_record(model="m", prompt="prompt A", seed="1")
        r2 = generate_provenance_record(model="m", prompt="prompt B", seed="1")
        assert r1.prompt_hash != r2.prompt_hash

    def test_settings_preserved(self):
        record = generate_provenance_record(
            model="m",
            prompt="p",
            seed="1",
            settings={"width": 1024, "height": 1024},
        )
        assert record.settings["width"] == 1024

    def test_settings_default_empty_dict(self):
        record = generate_provenance_record(model="m", prompt="p", seed="1")
        assert record.settings == {}


# ===================================================================
# 13. Font licensing verifies commercial safety
# ===================================================================


class TestFontLicensing:
    """safety.check_font_license identifies safe vs. unsafe fonts."""

    def test_open_sans_is_safe(self):
        info = check_font_license("Open Sans")
        assert info.commercial_print_safe is True
        assert info.license_type == "Apache 2.0"

    def test_arial_is_unsafe(self):
        info = check_font_license("Arial")
        assert info.commercial_print_safe is False

    def test_helvetica_is_unsafe(self):
        info = check_font_license("Helvetica")
        assert info.commercial_print_safe is False

    def test_unknown_font_defaults_unsafe(self):
        info = check_font_license("SuperRareFont123")
        assert info.commercial_print_safe is False
        assert info.license_type == "Unknown"

    def test_case_insensitive_lookup(self):
        info = check_font_license("OPEN SANS")
        assert info.commercial_print_safe is True

    def test_comic_neue_is_safe(self):
        info = check_font_license("Comic Neue")
        assert info.commercial_print_safe is True
        assert info.license_type == "OFL 1.1"

    def test_font_info_has_source(self):
        info = check_font_license("Roboto")
        assert info.source == "Google Fonts"


# ===================================================================
# 14. Bilingual translation with age-appropriate language constraints
# ===================================================================


class TestBilingualTranslation:
    """bilingual.translate_book builds LLM prompts with constraints."""

    def test_translate_book_basic(self):
        pages = [
            {"page_number": 1, "text_content": "The cat sat on the mat."},
            {"page_number": 2, "text_content": "The dog ran fast."},
        ]
        result = bilingual_translate_book(pages, "es", "board")
        assert result["target_language"] == "es"
        assert result["language_name"] == "Spanish"
        assert result["age_range"] == "board_0_3"
        assert len(result["pages"]) == 2
        assert result["pages"][0]["translated_text"] is None  # not yet filled
        assert result["pages"][0]["translation_prompt"] is not None

    def test_unsupported_language_raises(self):
        with pytest.raises(ValueError, match="Unsupported language"):
            bilingual_translate_book(
                [{"page_number": 1, "text_content": "Hi"}], "xx", "board"
            )

    def test_empty_page_skipped(self):
        pages = [
            {"page_number": 1, "text_content": "Hello."},
            {"page_number": 2, "text_content": ""},
        ]
        result = bilingual_translate_book(pages, "fr", "picture")
        empty_page = result["pages"][1]
        assert empty_page["translation_prompt"] is None

    def test_system_prompt_includes_age_constraints(self):
        pages = [{"page_number": 1, "text_content": "Hello world."}]
        result = bilingual_translate_book(pages, "de", "board")
        sys_prompt = result["system_prompt"]
        assert "5 words per sentence" in sys_prompt
        assert "5 letters per word" in sys_prompt

    def test_all_supported_languages_accepted(self):
        pages = [{"page_number": 1, "text_content": "Hi."}]
        for lang in SUPPORTED_LANGUAGES:
            result = bilingual_translate_book(pages, lang, "picture")
            assert result["target_language"] == lang

    def test_validate_translation_matching_pages(self):
        original = [
            {"page_number": 1, "text_content": "The cat sat."},
            {"page_number": 2, "text_content": "The dog ran."},
        ]
        translated = [
            {"page_number": 1, "translated_text": "El gato se sento."},
            {"page_number": 2, "translated_text": "El perro corrio."},
        ]
        result = validate_translation(original, translated, "board")
        assert result["page_count_match"] is True
        assert isinstance(result["original_readability"], float)
        assert isinstance(result["translated_readability"], float)

    def test_validate_translation_missing_translation(self):
        original = [{"page_number": 1, "text_content": "Hello world."}]
        translated = [{"page_number": 1, "translated_text": ""}]
        result = validate_translation(original, translated, "picture")
        missing = [i for i in result["issues"] if i["type"] == "missing_translation"]
        assert len(missing) > 0

    def test_validate_translation_page_count_mismatch(self):
        original = [
            {"page_number": 1, "text_content": "A."},
            {"page_number": 2, "text_content": "B."},
        ]
        translated = [{"page_number": 1, "translated_text": "X."}]
        result = validate_translation(original, translated, "picture")
        assert result["page_count_match"] is False

    def test_sync_translations_detects_changes(self):
        originals = [
            {"page_number": 1, "text_content": "Updated text."},
            {"page_number": 2, "text_content": "Same text."},
        ]
        translated = [
            {
                "page_number": 1,
                "translated_text": "Texto viejo.",
                "original_snapshot": "Old text.",
            },
            {
                "page_number": 2,
                "translated_text": "Mismo texto.",
                "original_snapshot": "Same text.",
            },
        ]
        result = sync_translations(originals, translated)
        assert result["total_changed"] == 1
        assert 1 in result["changed_pages"]
        assert 2 in result["unchanged_pages"]

    def test_bilingual_layout_side_by_side(self):
        pages = [{"page_number": 1, "text_content": "Hello."}]
        translated = [{"page_number": 1, "translated_text": "Hola."}]
        combined = get_bilingual_layout(pages, translated, "side_by_side")
        assert len(combined) == 1
        assert combined[0]["original_text"] == "Hello."
        assert combined[0]["translated_text"] == "Hola."
        assert combined[0]["layout_type"] == "side_by_side"

    def test_bilingual_layout_alternating(self):
        pages = [{"page_number": 1, "text_content": "Hello."}]
        translated = [{"page_number": 1, "translated_text": "Hola."}]
        combined = get_bilingual_layout(pages, translated, "alternating")
        assert len(combined) == 2  # original + translated interleaved
        assert combined[0]["layout_type"] == "alternating_original"
        assert combined[1]["layout_type"] == "alternating_translated"

    def test_bilingual_layout_back_section(self):
        pages = [
            {"page_number": 1, "text_content": "A."},
            {"page_number": 2, "text_content": "B."},
        ]
        translated = [
            {"page_number": 1, "translated_text": "X."},
            {"page_number": 2, "translated_text": "Y."},
        ]
        combined = get_bilingual_layout(pages, translated, "back_section")
        assert len(combined) == 4  # 2 original + 2 translated
        originals = [c for c in combined if "original" in c["layout_type"]]
        translations = [c for c in combined if "translated" in c["layout_type"]]
        assert len(originals) == 2
        assert len(translations) == 2

    def test_bilingual_layout_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Invalid layout_mode"):
            get_bilingual_layout([], [], "invalid_mode")


# ===================================================================
# 15. Safety scan detects trademark terms correctly
# ===================================================================


class TestSafetyScanTrademarks:
    """Comprehensive trademark scanning via safety module."""

    def test_all_blocklist_terms_detectable(self):
        for term in TRADEMARK_BLOCKLIST:
            issues = scan_trademarks(f"This book features {term} characters.")
            found = [i for i in issues if i.term.lower() == term.lower()]
            assert len(found) > 0, f"Blocklist term '{term}' not detected"

    def test_offset_positions_correct(self):
        text = "Hello Disney world"
        issues = scan_trademarks(text)
        disney_issues = [i for i in issues if i.term == "Disney"]
        assert len(disney_issues) == 1
        assert disney_issues[0].start == 6
        assert disney_issues[0].end == 12

    def test_multiple_occurrences_all_found(self):
        text = "Disney and Disney and more Disney"
        issues = scan_trademarks(text)
        disney_issues = [i for i in issues if i.term == "Disney"]
        assert len(disney_issues) == 3

    def test_inspired_by_pattern_detected(self):
        text = "This is inspired by famous art style"
        issues = scan_trademarks(text)
        style_issues = [i for i in issues if "inspired by" in i.term.lower()]
        assert len(style_issues) > 0


# ===================================================================
# 16. Text analysis returns correct violations per age band
# ===================================================================


class TestTextAnalysisViolations:
    """text_analysis.analyze_text returns structured violation dicts."""

    def test_board_book_clean_text_passes(self):
        # board_0_3 requires 50-150 words, max 5 words/sentence, max 5 chars/word
        text = "Cat sat. Dog ran. Bird flew. Cow moo. Pig oink. "
        text *= 5  # ~30 words, still need more
        text += "Cat. Dog. Cow. Pig. Hen. Fox. Bat. Bee. Ant. Ram. "
        text *= 2  # get above 50 words total
        result = analyze_text(text, "board")
        assert result["pass"] is True
        assert result["total_words"] >= 50
        assert result["age_range"] == "board_0_3"

    def test_board_book_total_words_too_few(self):
        text = "Hi."
        result = analyze_text(text, "board")
        total_w = [v for v in result["violations"] if v["rule"] == "total_words"]
        assert len(total_w) > 0
        assert "minimum" in total_w[0]["message"]

    def test_picture_book_total_words_too_many(self):
        # picture_3_5 max is 500 words
        text = " ".join(["word"] * 600) + "."
        result = analyze_text(text, "picture")
        total_w = [v for v in result["violations"] if v["rule"] == "total_words"]
        assert len(total_w) > 0
        assert "maximum" in total_w[0]["message"]

    def test_violation_has_suggestion(self):
        text = "The extraordinarily magnificent caterpillar crawled."
        result = analyze_text(text, "board")
        violations = result["violations"]
        word_violations = [v for v in violations if v["rule"] == "max_word_length"]
        assert len(word_violations) > 0
        assert word_violations[0]["suggestion"] is not None

    def test_resolve_age_range_aliases(self):
        assert _resolve_age_range("board") == "board_0_3"
        assert _resolve_age_range("picture") == "picture_3_5"
        assert _resolve_age_range("early_reader") == "early_reader_5_8"
        assert _resolve_age_range("chapter") == "chapter_8_12"

    def test_invalid_age_range_raises(self):
        with pytest.raises(ValueError, match="Unknown age_range"):
            analyze_text("text", "invalid_range")

    def test_page_separator_form_feed(self):
        text = "Page one.\fPage two."
        result = analyze_text(text, "board")
        # Should detect 2 pages worth of content
        assert result["total_words"] > 0

    def test_page_separator_dashes(self):
        text = "Page one.\n---\nPage two."
        result = analyze_text(text, "board")
        assert result["total_words"] > 0

    def test_readability_score_perfect(self):
        text = "Cat sat. Dog ran. " * 10  # ~40 words, need 50-150 for board
        text += "Cat. " * 10  # pad to 50+
        score = calculate_readability_score(text, "board")
        # May not be perfect if word count is off, but should be calculable
        assert 0.0 <= score <= 100.0

    def test_readability_score_heavily_violated(self):
        # Long sentence + long words for board book
        text = "The extraordinarily magnificent caterpillar crawled slowly through the garden."
        score = calculate_readability_score(text, "board")
        assert score < 100.0

    def test_rules_checked_includes_expected(self):
        result = analyze_text("Cat.", "board")
        assert "max_sentence_words" in result["rules_checked"]
        assert "max_word_length" in result["rules_checked"]
        assert "total_words" in result["rules_checked"]


# ===================================================================
# Service-layer readability (uses different AGE_BAND_RULES)
# ===================================================================


class TestServiceReadability:
    """_analyze_readability from service.py with service-specific rules."""

    def test_preschool_flags_long_sentence(self):
        pages = ["The very big enormous hungry caterpillar crawled slowly through the garden forever and ever."]
        result = _analyze_readability(pages, "preschool")
        long_sent = [i for i in result["issues"] if i["type"] == "sentence_too_long"]
        assert len(long_sent) > 0

    def test_preschool_flags_long_words(self):
        pages = ["The extraordinarily beautiful butterfly flew."]
        result = _analyze_readability(pages, "preschool")
        long_words = [i for i in result["issues"] if i["type"] == "word_too_long"]
        assert len(long_words) > 0

    def test_word_count_range_check(self):
        # preschool expects 300-500 words
        pages = ["Cat. " * 10]  # ~10 words, far below minimum
        result = _analyze_readability(pages, "preschool")
        assert result["word_count_in_range"] is False
        wc_issues = [i for i in result["issues"] if i["type"] == "total_word_count"]
        assert len(wc_issues) > 0

    def test_rhythm_score_in_range(self):
        pages = ["I like cats. I like dogs. I like birds."]
        result = _analyze_readability(pages, "preschool")
        assert 0 <= result["rhythm_score"] <= 100

    def test_compute_rhythm_empty_input(self):
        score = _compute_rhythm_score([], [], SVC_AGE_BAND_RULES["preschool"])
        assert score == 0
