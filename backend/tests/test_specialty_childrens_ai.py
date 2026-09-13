"""Tests for Children's Books AI Story Generation & Text Analysis.

Covers:
  - Story generation respects age-band word limits
  - Text analysis detects vocabulary violations
  - Rhyme pattern detection for AABB/ABAB
  - Continuity check finds inconsistencies
  - Auto-fix updates prompts correctly
  - Translation generates bilingual content
"""

from __future__ import annotations

import uuid

import pytest

from app.modules.specialty_books.service_childrens_ai import (
    AGE_BAND_CONSTRAINTS,
    AgeBand,
    AutoFixResponse,
    BilingualLayout,
    CharacterSheet,
    ContinuityCheckResponse,
    RhymeCheckResult,
    StoryGenerateRequest,
    StoryGenerateResponse,
    StoryMode,
    TextAnalysisResponse,
    Tone,
    TranslateRequest,
    TranslateResponse,
    _check_age_band_compliance,
    _check_word_in_vocabulary,
    _compute_hook_strength,
    _compute_rhythm_score,
    _near_rhyme,
    _words_rhyme,
    analyze_text,
    auto_fix_prompts,
    check_continuity,
    check_rhyme_patterns,
    generate_story,
    translate_book,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOOK_ID = uuid.uuid4()
ORG_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# Story Generation Tests
# ---------------------------------------------------------------------------


class TestStoryGeneration:
    """Tests for generate_story()."""

    @pytest.mark.asyncio
    async def test_generate_story_returns_correct_page_count(self):
        request = StoryGenerateRequest(
            story_prompt="A kitten explores a magical garden",
            age_band=AgeBand.PICTURE,
            page_count=24,
            story_mode=StoryMode.PROSE,
            tone=Tone.WARM,
        )
        result = await generate_story(None, BOOK_ID, ORG_ID, request)
        assert isinstance(result, StoryGenerateResponse)
        assert len(result.pages) == 24
        assert result.age_band == AgeBand.PICTURE

    @pytest.mark.asyncio
    async def test_generate_story_board_book_constraints(self):
        request = StoryGenerateRequest(
            story_prompt="A baby duck says quack",
            age_band=AgeBand.BOARD,
            page_count=12,
            story_mode=StoryMode.REPETITIVE,
        )
        result = await generate_story(None, BOOK_ID, ORG_ID, request)
        assert len(result.pages) == 12

    @pytest.mark.asyncio
    async def test_generate_story_invalid_page_count_raises(self):
        request = StoryGenerateRequest(
            story_prompt="A kitten explores",
            age_band=AgeBand.BOARD,
            page_count=30,  # Board max is 16
        )
        with pytest.raises(Exception) as exc_info:
            await generate_story(None, BOOK_ID, ORG_ID, request)
        assert "outside" in str(exc_info.value).lower() or "range" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generate_story_creates_character_sheet(self):
        request = StoryGenerateRequest(
            story_prompt="Luna explores the forest",
            main_character="Luna - a small orange tabby kitten",
            setting="A cozy village with gardens",
            age_band=AgeBand.PICTURE,
            page_count=24,
        )
        result = await generate_story(None, BOOK_ID, ORG_ID, request)
        assert len(result.character_sheets) >= 1
        assert result.character_sheets[0].name == "Luna"

    @pytest.mark.asyncio
    async def test_generate_story_includes_illustration_prompts(self):
        request = StoryGenerateRequest(
            story_prompt="A bear goes fishing",
            age_band=AgeBand.PICTURE,
            page_count=24,
        )
        result = await generate_story(None, BOOK_ID, ORG_ID, request)
        for page in result.pages:
            assert page.illustration_prompt

    @pytest.mark.asyncio
    async def test_generate_story_chapter_book(self):
        request = StoryGenerateRequest(
            story_prompt="A young wizard discovers hidden powers at school",
            age_band=AgeBand.CHAPTER,
            page_count=48,
            story_mode=StoryMode.PROSE,
        )
        result = await generate_story(None, BOOK_ID, ORG_ID, request)
        assert len(result.pages) == 48
        assert result.age_band == AgeBand.CHAPTER


# ---------------------------------------------------------------------------
# Text Analysis Tests
# ---------------------------------------------------------------------------


class TestTextAnalysis:
    """Tests for analyze_text()."""

    @pytest.mark.asyncio
    async def test_analyze_detects_sentence_too_long(self):
        pages = ["The very big enormous gigantic cat sat on the extremely comfortable mat."]
        result = await analyze_text(None, BOOK_ID, ORG_ID, pages_text=pages, age_band=AgeBand.BOARD)
        assert isinstance(result, TextAnalysisResponse)
        sentence_issues = [i for i in result.issues if i.issue_type == "sentence_too_long"]
        assert len(sentence_issues) > 0

    @pytest.mark.asyncio
    async def test_analyze_detects_word_too_long(self):
        pages = ["The elephant walked slowly."]
        result = await analyze_text(None, BOOK_ID, ORG_ID, pages_text=pages, age_band=AgeBand.BOARD)
        word_issues = [i for i in result.issues if i.issue_type == "word_too_long"]
        assert len(word_issues) > 0

    @pytest.mark.asyncio
    async def test_analyze_detects_vocabulary_violations(self):
        pages = ["The metamorphosis was extraordinary."]
        result = await analyze_text(None, BOOK_ID, ORG_ID, pages_text=pages, age_band=AgeBand.BOARD)
        vocab_issues = [i for i in result.issues if i.issue_type == "vocabulary_violation"]
        assert len(vocab_issues) > 0

    @pytest.mark.asyncio
    async def test_analyze_word_count_out_of_range(self):
        pages = [" ".join(["word"] * 200)]
        result = await analyze_text(None, BOOK_ID, ORG_ID, pages_text=pages, age_band=AgeBand.BOARD)
        wc_issues = [i for i in result.issues if i.issue_type == "word_count_out_of_range"]
        assert len(wc_issues) > 0
        assert result.word_count_valid is False

    @pytest.mark.asyncio
    async def test_analyze_valid_board_book(self):
        pages = ["The cat sat.", "The dog ran.", "The bird flew.", "The fish swam."]
        result = await analyze_text(None, BOOK_ID, ORG_ID, pages_text=pages, age_band=AgeBand.BOARD)
        sentence_issues = [i for i in result.issues if i.issue_type == "sentence_too_long"]
        word_issues = [i for i in result.issues if i.issue_type == "word_too_long"]
        assert len(sentence_issues) == 0
        assert len(word_issues) == 0

    @pytest.mark.asyncio
    async def test_analyze_rhythm_score_computed(self):
        pages = [
            "The cat sat on the mat.",
            "Then the cat went to play.",
            "And the cat came back home.",
        ]
        result = await analyze_text(None, BOOK_ID, ORG_ID, pages_text=pages, age_band=AgeBand.PICTURE)
        assert result.rhythm_score is not None
        assert 0 <= result.rhythm_score.overall <= 100

    @pytest.mark.asyncio
    async def test_analyze_hook_strength_computed(self):
        pages = ["Who is hiding behind the door?", "It was a big red bear!"]
        result = await analyze_text(None, BOOK_ID, ORG_ID, pages_text=pages, age_band=AgeBand.PICTURE)
        assert result.hook_strength_score >= 0

    @pytest.mark.asyncio
    async def test_analyze_page_turn_surprises(self):
        pages = [
            "Luna walked down the path.",
            "Suddenly, a surprise appeared!",
            "Oh wow, look at that!",
        ]
        result = await analyze_text(None, BOOK_ID, ORG_ID, pages_text=pages, age_band=AgeBand.PICTURE)
        assert len(result.page_turn_surprises) == 3
        assert result.page_turn_surprises[1].surprise_score > result.page_turn_surprises[0].surprise_score

    @pytest.mark.asyncio
    async def test_analyze_chapter_book_no_word_length_limit(self):
        pages = ["The extraordinary metamorphosis was unprecedented."]
        result = await analyze_text(None, BOOK_ID, ORG_ID, pages_text=pages, age_band=AgeBand.CHAPTER)
        word_issues = [i for i in result.issues if i.issue_type == "word_too_long"]
        assert len(word_issues) == 0


# ---------------------------------------------------------------------------
# Rhyme Pattern Detection Tests
# ---------------------------------------------------------------------------


class TestRhymePatterns:
    """Tests for check_rhyme_patterns()."""

    def test_detect_aabb_pattern(self):
        text = (
            "The cat sat on the mat\n" "And then he saw a bat\n" "He ran across the floor\n" "And out the open door\n"
        )
        result = check_rhyme_patterns(text, StoryMode.RHYMING)
        assert isinstance(result, RhymeCheckResult)
        assert result.pattern_detected == "AABB"

    def test_detect_abab_pattern(self):
        text = (
            "The sun shines bright today\n"
            "The birds sing in the tree\n"
            "Come out and let us play\n"
            "As happy as can be\n"
        )
        result = check_rhyme_patterns(text, StoryMode.RHYMING)
        assert result.pattern_detected == "ABAB"

    def test_no_rhyme_pattern(self):
        text = "The dog walked around\n" "Trees were very tall\n" "Water flowed gently\n" "Mountains stood above\n"
        result = check_rhyme_patterns(text, StoryMode.RHYMING)
        assert result.pattern_detected in ("NONE", "MIXED")

    def test_near_rhymes_detected(self):
        text = (
            "The cat sat on the mat\n"
            "He walked along the path\n"
            "He played upon the grass\n"
            "And took a little bath\n"
        )
        result = check_rhyme_patterns(text, StoryMode.RHYMING)
        assert isinstance(result.near_rhymes, list)

    def test_meter_consistency_checked(self):
        text = "Cat\n" "The very long sentence about the extraordinary adventure of the little cat\n" "Dog\n" "Run\n"
        result = check_rhyme_patterns(text, StoryMode.RHYMING)
        assert result.meter_consistent is False
        assert len(result.meter_issues) > 0

    def test_prose_mode_skips_rhyme_check(self):
        result = check_rhyme_patterns("Any text here.", StoryMode.PROSE)
        assert result.pattern_detected == "N/A"

    def test_insufficient_lines(self):
        result = check_rhyme_patterns("Just one line.", StoryMode.RHYMING)
        assert result.pattern_detected == "INSUFFICIENT"


# ---------------------------------------------------------------------------
# Continuity Check Tests
# ---------------------------------------------------------------------------


class TestContinuityCheck:
    """Tests for check_continuity()."""

    @pytest.mark.asyncio
    async def test_detects_missing_clothing(self):
        sheets = [
            CharacterSheet(
                name="Luna",
                species_type="orange tabby kitten",
                description="A small orange tabby kitten",
                clothing_accessories=[
                    "red collar with gold bell",
                    "blue bow",
                ],
            ),
        ]
        prompts = [
            {
                "page_number": "1",
                "prompt": "Luna the orange tabby kitten playing in garden",
            },
            {
                "page_number": "2",
                "prompt": ("Luna the orange tabby kitten with " "red collar with gold bell"),
            },
        ]
        result = await check_continuity(None, BOOK_ID, ORG_ID, sheets, prompts)
        assert isinstance(result, ContinuityCheckResponse)
        assert result.total_issues > 0
        clothing_issues = [i for i in result.issues if i.issue_type == "clothing"]
        assert len(clothing_issues) >= 2

    @pytest.mark.asyncio
    async def test_detects_time_of_day_inconsistency(self):
        prompts = [
            {
                "page_number": "1",
                "prompt": "Luna playing in the evening sunset",
            },
            {
                "page_number": "2",
                "prompt": ("Luna eating breakfast at sunrise in the morning"),
            },
        ]
        result = await check_continuity(None, BOOK_ID, ORG_ID, [], prompts)
        time_issues = [i for i in result.issues if i.issue_type == "time_of_day"]
        assert len(time_issues) > 0

    @pytest.mark.asyncio
    async def test_no_issues_when_consistent(self):
        sheets = [
            CharacterSheet(
                name="Bear",
                species_type="brown bear",
                description="A friendly brown bear",
                clothing_accessories=["red scarf"],
            ),
        ]
        prompts = [
            {
                "page_number": "1",
                "prompt": ("Bear the brown bear wearing red scarf " "in morning garden"),
            },
            {
                "page_number": "2",
                "prompt": ("Bear the brown bear wearing red scarf " "at afternoon picnic"),
            },
        ]
        result = await check_continuity(None, BOOK_ID, ORG_ID, sheets, prompts)
        clothing_issues = [i for i in result.issues if i.issue_type == "clothing"]
        assert len(clothing_issues) == 0

    @pytest.mark.asyncio
    async def test_consistency_score_calculated(self):
        result = await check_continuity(None, BOOK_ID, ORG_ID, [], [])
        assert 0 <= result.consistency_score <= 100


# ---------------------------------------------------------------------------
# Auto-Fix Prompts Tests
# ---------------------------------------------------------------------------


class TestAutoFixPrompts:
    """Tests for auto_fix_prompts()."""

    @pytest.mark.asyncio
    async def test_adds_missing_accessories(self):
        sheets = [
            CharacterSheet(
                name="Luna",
                species_type="orange tabby kitten",
                description="A small orange tabby kitten",
                clothing_accessories=["red collar", "blue bow"],
            ),
        ]
        prompts = [
            {
                "page_number": "1",
                "prompt": "Luna the orange tabby kitten in the garden",
            },
        ]
        result = await auto_fix_prompts(None, BOOK_ID, ORG_ID, sheets, prompts)
        assert isinstance(result, AutoFixResponse)
        assert result.total_fixes >= 1
        fix = result.fixes[0]
        assert "red collar" in fix.fixed_prompt.lower()
        assert "blue bow" in fix.fixed_prompt.lower()

    @pytest.mark.asyncio
    async def test_no_fix_when_already_correct(self):
        sheets = [
            CharacterSheet(
                name="Bear",
                species_type="brown bear",
                description="A brown bear",
                clothing_accessories=["red scarf"],
            ),
        ]
        prompts = [
            {
                "page_number": "1",
                "prompt": "Bear the brown bear wearing red scarf",
            },
        ]
        result = await auto_fix_prompts(None, BOOK_ID, ORG_ID, sheets, prompts)
        clothing_fixes = [f for f in result.fixes if any("accessory" in c.lower() for c in f.changes)]
        assert len(clothing_fixes) == 0

    @pytest.mark.asyncio
    async def test_fix_returns_change_list(self):
        sheets = [
            CharacterSheet(
                name="Luna",
                species_type="kitten",
                description="A small kitten",
                clothing_accessories=["hat"],
            ),
        ]
        prompts = [
            {"page_number": "1", "prompt": "Luna the kitten playing"},
        ]
        result = await auto_fix_prompts(None, BOOK_ID, ORG_ID, sheets, prompts)
        if result.fixes:
            assert len(result.fixes[0].changes) > 0


# ---------------------------------------------------------------------------
# Translation Tests
# ---------------------------------------------------------------------------


class TestTranslation:
    """Tests for translate_book()."""

    @pytest.mark.asyncio
    async def test_translate_generates_bilingual_content(self):
        pages = [
            "The cat sat on the mat.",
            "Then the cat went to play.",
        ]
        req = TranslateRequest(
            target_language="Spanish",
            layout_mode=BilingualLayout.SIDE_BY_SIDE,
        )
        result = await translate_book(
            None,
            BOOK_ID,
            ORG_ID,
            req,
            pages_text=pages,
            age_band=AgeBand.PICTURE,
        )
        assert isinstance(result, TranslateResponse)
        assert result.target_language == "Spanish"
        assert len(result.pages) == 2
        for page in result.pages:
            assert page.original_text
            assert page.translated_text
            assert page.original_text != page.translated_text

    @pytest.mark.asyncio
    async def test_translate_respects_layout_mode(self):
        pages = ["Hello world."]
        req = TranslateRequest(
            target_language="French",
            layout_mode=BilingualLayout.ALTERNATING,
        )
        result = await translate_book(None, BOOK_ID, ORG_ID, req, pages_text=pages)
        assert result.layout_mode == BilingualLayout.ALTERNATING

    @pytest.mark.asyncio
    async def test_translate_back_section_mode(self):
        pages = ["Once upon a time.", "The end."]
        req = TranslateRequest(
            target_language="German",
            layout_mode=BilingualLayout.BACK_SECTION,
        )
        result = await translate_book(None, BOOK_ID, ORG_ID, req, pages_text=pages)
        assert result.layout_mode == BilingualLayout.BACK_SECTION
        assert result.source_language == "English"

    @pytest.mark.asyncio
    async def test_translate_validates_target_readability(self):
        pages = ["Simple text."]
        req = TranslateRequest(target_language="Japanese")
        result = await translate_book(
            None,
            BOOK_ID,
            ORG_ID,
            req,
            pages_text=pages,
            age_band=AgeBand.BOARD,
        )
        assert isinstance(result.target_language_readable, bool)


# ---------------------------------------------------------------------------
# Helper Function Unit Tests
# ---------------------------------------------------------------------------


class TestHelpers:
    """Tests for internal helper functions."""

    def test_words_rhyme_basic(self):
        assert _words_rhyme("cat", "mat") is True
        assert _words_rhyme("cat", "dog") is False
        assert _words_rhyme("play", "day") is True
        assert _words_rhyme("tree", "free") is True

    def test_words_rhyme_same_word(self):
        assert _words_rhyme("cat", "cat") is False

    def test_near_rhyme_detection(self):
        assert _near_rhyme("cat", "cut") is True
        assert _near_rhyme("cat", "cat") is False

    def test_vocabulary_check_board_level(self):
        assert _check_word_in_vocabulary("cat", 500) is True
        assert _check_word_in_vocabulary("metamorphosis", 500) is False

    def test_vocabulary_check_no_limit(self):
        assert _check_word_in_vocabulary("antidisestablishmentarianism", None) is True

    def test_age_band_compliance_check(self):
        issues = _check_age_band_compliance("The cat sat.", AgeBand.BOARD)
        sentence_issues = [i for i in issues if "sentence" in i.lower()]
        word_length_issues = [i for i in issues if "letters" in i.lower()]
        assert len(sentence_issues) == 0
        assert len(word_length_issues) == 0

    def test_rhythm_score_computation(self):
        pages = ["The cat sat.", "Then he ran.", "And he played."]
        score = _compute_rhythm_score(pages)
        assert 0 <= score.overall <= 100
        assert 0 <= score.cadence <= 100

    def test_rhythm_score_empty(self):
        score = _compute_rhythm_score([])
        assert score.overall == 0

    def test_hook_strength_with_question(self):
        score_with = _compute_hook_strength(["Who is hiding behind the door?"])
        score_without = _compute_hook_strength(["The cat sat on the mat."])
        assert score_with > score_without

    def test_age_band_constraints_defined(self):
        for band in AgeBand:
            assert band in AGE_BAND_CONSTRAINTS
            c = AGE_BAND_CONSTRAINTS[band]
            assert "max_sentence_words" in c
            assert "total_words_min" in c
            assert "total_words_max" in c
            assert c["total_words_min"] < c["total_words_max"]
