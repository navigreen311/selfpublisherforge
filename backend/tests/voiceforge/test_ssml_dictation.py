"""Unit tests for SSMLGenerator and DictationRefiner services.

Mocks the broken app.models import chain before importing the services
so tests can run independently of database model registration.
"""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Pre-seed broken model modules so the voiceforge package __init__ can load.
# The import chain app.services.voiceforge → voice_manager → app.models
# fails due to a missing re-export in app.models.agent.
# ---------------------------------------------------------------------------
_STUBS = [
    "app.models",
    "app.models.agent",
    "app.models.audiobook",
    "app.modules.agent_system",
    "app.modules.agent_system.models",
]
for _path in _STUBS:
    if _path not in sys.modules:
        _mod = types.ModuleType(_path)
        # Provide common attribute names that the import chain expects
        _mod.__dict__.setdefault("Agent", type("Agent", (), {}))
        _mod.__dict__.setdefault("AgentBudget", type("AgentBudget", (), {}))
        _mod.__dict__.setdefault("AgentTask", type("AgentTask", (), {}))
        _mod.__dict__.setdefault("AgentWorkflow", type("AgentWorkflow", (), {}))
        _mod.__dict__.setdefault("AuditTrail", type("AuditTrail", (), {}))
        _mod.__dict__.setdefault("AudiobookVoice", type("AudiobookVoice", (), {}))
        _mod.__dict__.setdefault("AudiobookProject", type("AudiobookProject", (), {}))
        _mod.__dict__.setdefault("AudiobookChapter", type("AudiobookChapter", (), {}))
        _mod.__dict__.setdefault("AudiobookPronunciation", type("AudiobookPronunciation", (), {}))
        _mod.__dict__.setdefault("AudiobookGenerationJob", type("AudiobookGenerationJob", (), {}))
        sys.modules[_path] = _mod

import pytest

from app.services.voiceforge.ssml_generator import (
    SSMLGenerator,
    SSMLResult,
    DialogueSegment,
    EmotionSegment,
)
from app.services.voiceforge.dictation_refiner import (
    DictationRefiner,
    DiffSegment,
    RefinedText,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

DIALOGUE_TEXT = '''
"I can't believe it," Sarah whispered.
John replied, "Neither can I."
"What do we do now?" she asked.
'''

UNPUNCTUATED_TEXT = (
    "the quick brown fox jumps over the lazy dog it was a sunny day"
)

FILLER_TEXT = (
    "so um I was thinking you know that maybe we should uh go to the "
    "store like tomorrow"
)


# ===================================================================
# SSMLGenerator Tests
# ===================================================================


class TestSSMLGeneratorInit:
    """test_ssml_generator_init — Can be instantiated."""

    def test_default_init(self):
        gen = SSMLGenerator()
        assert gen is not None
        assert gen._orchestrator is None

    def test_init_with_orchestrator(self):
        fake_orch = object()
        gen = SSMLGenerator(orchestrator=fake_orch)
        assert gen._orchestrator is fake_orch

    def test_init_with_custom_abbreviations(self):
        custom = {"Capt.": "Captain"}
        gen = SSMLGenerator(abbreviations=custom)
        assert gen._abbreviations["Capt."] == "Captain"
        # defaults are still present
        assert gen._abbreviations["Dr."] == "Doctor"


class TestDetectDialogue:
    """test_detect_dialogue — Detects quoted dialogue with character attribution."""

    @pytest.mark.asyncio
    async def test_detect_dialogue_basic(self):
        gen = SSMLGenerator()  # no orchestrator → regex fallback
        segments = await gen.detect_dialogue(DIALOGUE_TEXT)

        assert isinstance(segments, list)
        assert len(segments) >= 2  # at least Sarah + she

        # Verify character names are detected
        characters = [s.character for s in segments]
        assert "Sarah" in characters or "Narrator" in characters

    @pytest.mark.asyncio
    async def test_detect_dialogue_returns_dataclass(self):
        gen = SSMLGenerator()
        segments = await gen.detect_dialogue(DIALOGUE_TEXT)
        for seg in segments:
            assert isinstance(seg, DialogueSegment)
            assert isinstance(seg.text, str)
            assert isinstance(seg.character, str)

    @pytest.mark.asyncio
    async def test_detect_dialogue_empty_text(self):
        gen = SSMLGenerator()
        segments = await gen.detect_dialogue("")
        assert segments == []


class TestDetectEmotions:
    """test_detect_emotions — Detects emotional tone in passages."""

    @pytest.mark.asyncio
    async def test_detect_sadness(self):
        gen = SSMLGenerator()
        text = "She was devastated by the loss, tears streaming down her face."
        segments = await gen.detect_emotions(text)

        assert len(segments) >= 1
        emotions = [s.emotion for s in segments]
        assert "sad" in emotions

    @pytest.mark.asyncio
    async def test_detect_anger(self):
        gen = SSMLGenerator()
        text = "He was furious, seething with rage as he slammed the door."
        segments = await gen.detect_emotions(text)

        assert len(segments) >= 1
        emotions = [s.emotion for s in segments]
        assert "angry" in emotions

    @pytest.mark.asyncio
    async def test_detect_emotions_returns_dataclass(self):
        gen = SSMLGenerator()
        text = "She laughed with delight, thrilled and overjoyed at the news."
        segments = await gen.detect_emotions(text)

        for seg in segments:
            assert isinstance(seg, EmotionSegment)
            assert 0.0 <= seg.intensity <= 1.0

    @pytest.mark.asyncio
    async def test_no_emotion_in_neutral_text(self):
        gen = SSMLGenerator()
        text = "The table had four legs."
        segments = await gen.detect_emotions(text)
        assert segments == []


class TestExpandAbbreviations:
    """test_expand_abbreviations — Expands abbreviations to spoken form."""

    def test_expand_dr(self):
        gen = SSMLGenerator()
        assert gen.expand_abbreviations("Dr. Smith") == "Doctor Smith"

    def test_expand_st(self):
        gen = SSMLGenerator()
        result = gen.expand_abbreviations("St. Patrick")
        assert result == "Saint Patrick"

    def test_expand_multiple(self):
        gen = SSMLGenerator()
        text = "Dr. Jones lives on Ave. and works with Prof. Lee"
        result = gen.expand_abbreviations(text)
        assert "Doctor" in result
        assert "Avenue" in result
        assert "Professor" in result

    def test_expand_preserves_unknown(self):
        gen = SSMLGenerator()
        text = "Hello world"
        assert gen.expand_abbreviations(text) == "Hello world"

    def test_custom_abbreviation(self):
        gen = SSMLGenerator(abbreviations={"Capt.": "Captain"})
        assert gen.expand_abbreviations("Capt. Hook") == "Captain Hook"


class TestValidateSSML:
    """test_validate_ssml_valid / test_validate_ssml_invalid."""

    def test_validate_ssml_valid(self):
        gen = SSMLGenerator()
        ssml = (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis">'
            "<p>Hello world.</p>"
            '<break time="500ms"/>'
            "</speak>"
        )
        result = gen.validate_ssml(ssml)
        assert result["valid"] is True
        assert result["errors"] == []
        assert "speak" in result["tag_counts"]

    def test_validate_ssml_with_prosody(self):
        gen = SSMLGenerator()
        ssml = (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis">'
            '<prosody rate="slow" pitch="low">Dramatic pause.</prosody>'
            "</speak>"
        )
        result = gen.validate_ssml(ssml)
        assert result["valid"] is True

    def test_validate_ssml_invalid_xml(self):
        gen = SSMLGenerator()
        ssml = "<speak><p>Unclosed paragraph"
        result = gen.validate_ssml(ssml)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_ssml_missing_speak(self):
        gen = SSMLGenerator()
        ssml = "<p>No speak wrapper.</p>"
        result = gen.validate_ssml(ssml)
        # Should still parse, but produce a warning
        assert "SSML should start with a <speak> element." in result["warnings"]

    def test_validate_ssml_non_standard_tag(self):
        gen = SSMLGenerator()
        ssml = "<speak><custom>hello</custom></speak>"
        result = gen.validate_ssml(ssml)
        assert result["valid"] is True
        assert any("Non-standard" in w for w in result["warnings"])


class TestApplyPronunciationDict:
    """test_apply_pronunciation_dict — Applies custom pronunciation rules."""

    def test_single_word(self):
        gen = SSMLGenerator()
        result = gen.apply_pronunciation_dict(
            "Hermione walked in.",
            {"Hermione": "hɜːrˈmaɪ.ə.niː"},
        )
        assert "<phoneme" in result
        assert 'ph="hɜːrˈmaɪ.ə.niː"' in result
        assert "Hermione" in result

    def test_multiple_words(self):
        gen = SSMLGenerator()
        result = gen.apply_pronunciation_dict(
            "Nguyen and Siobhan met.",
            {"Nguyen": "wɪn", "Siobhan": "ʃɪˈvɔːn"},
        )
        assert result.count("<phoneme") == 2

    def test_no_dict_entries(self):
        gen = SSMLGenerator()
        text = "Hello world."
        result = gen.apply_pronunciation_dict(text, {})
        assert result == text


class TestGenerateSSMLBasic:
    """test_generate_ssml_basic — Generates basic SSML from plain text."""

    @pytest.mark.asyncio
    async def test_generate_ssml_wraps_in_speak(self):
        gen = SSMLGenerator()  # regex fallback
        result = await gen.generate_ssml("Hello world. How are you?")

        assert isinstance(result, SSMLResult)
        assert result.ssml_text.startswith("<speak")
        assert result.ssml_text.endswith("</speak>")
        assert result.original_text == "Hello world. How are you?"

    @pytest.mark.asyncio
    async def test_generate_ssml_contains_paragraph_tags(self):
        gen = SSMLGenerator()
        text = "First paragraph here.\n\nSecond paragraph here."
        result = await gen.generate_ssml(text)
        assert "<p>" in result.ssml_text

    @pytest.mark.asyncio
    async def test_generate_ssml_expands_abbreviations(self):
        gen = SSMLGenerator()
        result = await gen.generate_ssml("Dr. Smith arrived.")
        assert "Doctor" in result.ssml_text
        assert "Dr." not in result.ssml_text

    @pytest.mark.asyncio
    async def test_generate_ssml_applies_pronunciation(self):
        gen = SSMLGenerator()
        result = await gen.generate_ssml(
            "Hermione spoke.",
            pronunciation_dict={"Hermione": "hɜːrˈmaɪ.ə.niː"},
        )
        assert "<phoneme" in result.ssml_text


# ===================================================================
# DictationRefiner Tests
# ===================================================================


class TestDictationRefinerInit:
    """test_dictation_refiner_init — Can be instantiated."""

    def test_default_init(self):
        refiner = DictationRefiner()
        assert refiner is not None

    def test_has_fillers_list(self):
        refiner = DictationRefiner()
        assert len(refiner.FILLERS) > 0
        assert "um" in refiner.FILLERS
        assert "uh" in refiner.FILLERS


class TestRestorePunctuation:
    """test_restore_punctuation — Adds periods, commas to unpunctuated text."""

    def test_capitalizes_first_word(self):
        refiner = DictationRefiner()
        result = refiner.restore_punctuation("hello world")
        assert result[0].isupper()

    def test_processes_voice_commands(self):
        refiner = DictationRefiner()
        result = refiner.restore_punctuation("hello world period how are you")
        assert "." in result

    def test_spoken_comma(self):
        refiner = DictationRefiner()
        result = refiner.restore_punctuation("first comma second")
        assert "," in result

    def test_question_mark(self):
        refiner = DictationRefiner()
        result = refiner.restore_punctuation(
            "how are you question mark fine thanks"
        )
        assert "?" in result


class TestRemoveFillers:
    """test_remove_fillers — Removes 'um', 'uh', 'like', 'you know'."""

    def test_removes_um(self):
        refiner = DictationRefiner()
        result = refiner.remove_fillers("I was um thinking about it")
        assert "um" not in result.lower().split()
        assert "thinking" in result

    def test_removes_uh(self):
        refiner = DictationRefiner()
        result = refiner.remove_fillers("we should uh go now")
        assert "uh" not in result.lower().split()
        assert "go" in result

    def test_removes_you_know(self):
        refiner = DictationRefiner()
        result = refiner.remove_fillers("it was you know really great")
        assert "you know" not in result.lower()
        assert "really" in result

    def test_removes_like_filler(self):
        refiner = DictationRefiner()
        result = refiner.remove_fillers("so like we went there")
        assert result.lower().count("like") == 0
        assert "went" in result

    def test_full_filler_text(self):
        refiner = DictationRefiner()
        result = refiner.remove_fillers(FILLER_TEXT)
        assert "um" not in result.lower().split()
        assert "uh" not in result.lower().split()
        # Core content preserved
        assert "thinking" in result
        assert "store" in result
        assert "tomorrow" in result

    def test_no_fillers(self):
        refiner = DictationRefiner()
        text = "The dog sat on the mat"
        result = refiner.remove_fillers(text)
        assert result == text


class TestStructureParagraphs:
    """test_structure_paragraphs — Groups sentences into paragraphs."""

    def test_groups_sentences(self):
        refiner = DictationRefiner()
        sentences = ". ".join(f"Sentence {i}" for i in range(8)) + "."
        result = refiner.structure_paragraphs(sentences)
        # Should have at least one paragraph break
        assert "\n\n" in result

    def test_short_text_no_split(self):
        refiner = DictationRefiner()
        text = "One sentence. Two sentence. Three."
        result = refiner.structure_paragraphs(text)
        # Fewer than 4 sentences: should be a single paragraph
        assert "\n\n" not in result

    def test_preserves_content(self):
        refiner = DictationRefiner()
        text = "First. Second. Third. Fourth. Fifth."
        result = refiner.structure_paragraphs(text)
        assert "First" in result
        assert "Fifth" in result


class TestDiffHighlight:
    """test_diff_highlight — Produces correct diff between original and refined."""

    def test_identical_text(self):
        refiner = DictationRefiner()
        diff = refiner.diff_highlight("hello world", "hello world")
        assert len(diff) == 1
        assert diff[0].type == "unchanged"
        assert diff[0].original_text == "hello world"

    def test_word_removed(self):
        refiner = DictationRefiner()
        diff = refiner.diff_highlight("I um went home", "I went home")
        types = [s.type for s in diff]
        assert "removed" in types or "changed" in types

    def test_word_added(self):
        refiner = DictationRefiner()
        diff = refiner.diff_highlight("went home", "I went home")
        types = [s.type for s in diff]
        assert "added" in types or "changed" in types

    def test_returns_diff_segments(self):
        refiner = DictationRefiner()
        diff = refiner.diff_highlight("old text", "new text")
        for seg in diff:
            assert isinstance(seg, DiffSegment)
            assert seg.type in ("added", "removed", "unchanged", "changed")


class TestRefineTranscriptFull:
    """test_refine_transcript_full — Full pipeline with LLM mocked out."""

    @pytest.mark.asyncio
    async def test_full_pipeline_fallback(self, monkeypatch):
        """Full pipeline uses regex fallback when LLM is unavailable."""
        refiner = DictationRefiner()

        # Monkeypatch _claude_cleanup to use the regex fallback directly
        async def _fake_cleanup(self, raw_text):
            return self._regex_cleanup(raw_text)

        monkeypatch.setattr(DictationRefiner, "_claude_cleanup", _fake_cleanup)

        result = await refiner.refine_transcript(FILLER_TEXT)

        assert isinstance(result, RefinedText)
        assert result.raw_text == FILLER_TEXT
        # Fillers should be removed
        assert "um" not in result.refined_text.lower().split()
        assert "uh" not in result.refined_text.lower().split()
        # Content preserved
        assert "store" in result.refined_text.lower()
        # Diff should have segments
        assert len(result.diff) >= 1
        # Changes summary present
        assert "original_word_count" in result.changes_summary

    @pytest.mark.asyncio
    async def test_full_pipeline_with_style(self, monkeypatch):
        """Pipeline with style_profile_id invokes apply_style."""
        refiner = DictationRefiner()

        async def _fake_cleanup(self, raw_text):
            return self._regex_cleanup(raw_text)

        async def _fake_style(self, text, profile_id):
            return text  # passthrough

        monkeypatch.setattr(DictationRefiner, "_claude_cleanup", _fake_cleanup)
        monkeypatch.setattr(DictationRefiner, "apply_style", _fake_style)

        result = await refiner.refine_transcript(
            FILLER_TEXT, style_profile_id="test-profile"
        )

        assert isinstance(result, RefinedText)
        # style_match_score is set when style_profile_id is provided
        assert result.style_match_score is not None

    @pytest.mark.asyncio
    async def test_changes_summary_counts(self, monkeypatch):
        """Verify changes_summary has correct word count fields."""
        refiner = DictationRefiner()

        async def _fake_cleanup(self, raw_text):
            return self._regex_cleanup(raw_text)

        monkeypatch.setattr(DictationRefiner, "_claude_cleanup", _fake_cleanup)

        result = await refiner.refine_transcript(FILLER_TEXT)

        summary = result.changes_summary
        assert summary["original_word_count"] == len(FILLER_TEXT.split())
        assert summary["refined_word_count"] == len(
            result.refined_text.split()
        )
        assert summary["paragraphs"] >= 1
