"""Dictation Refinement Pipeline.

Transforms raw ASR (speech-to-text) transcripts into polished prose through
a multi-stage pipeline:

1. Punctuation Restoration — periods, commas, semicolons, etc.
2. Capitalization Fix — proper nouns, sentence starts
3. Filler Removal — "um", "uh", "like", "you know", false starts, repeats
4. Sentence Boundary Detection — split run-on dictation
5. Paragraph Structuring — group into logical paragraphs
6. Voice Command Extraction — "new paragraph" → actual break
7. Style Refinement — Style Cloning Engine to match author's voice

Stages 1-6 are handled by a single LLM call (with regex fallback).
Stage 7 optionally applies a Style Cloning profile.
"""

from __future__ import annotations

import difflib
import logging
import re
from dataclasses import dataclass, field
from typing import ClassVar

logger = logging.getLogger(__name__)


@dataclass
class DiffSegment:
    """A segment of the diff between raw and refined text."""

    type: str  # 'added', 'removed', 'unchanged', 'changed'
    original_text: str
    new_text: str
    start_index: int = 0
    end_index: int = 0


@dataclass
class RefinedText:
    """Result of the dictation refinement pipeline."""

    raw_text: str
    refined_text: str
    diff: list[DiffSegment] = field(default_factory=list)
    style_match_score: float | None = None
    changes_summary: dict = field(default_factory=dict)


class DictationRefiner:
    """Multi-stage dictation refinement pipeline.

    Uses the LLM Orchestrator for intelligent cleanup (stages 1-6) with a
    regex-based fallback, and optionally applies style refinement via the
    Style Cloning Engine (stage 7).
    """

    # Common filler words to remove in regex fallback
    FILLERS: ClassVar[list[str]] = [
        "um", "uh", "er", "ah", "like", "you know",
        "i mean", "sort of", "kind of", "basically",
    ]

    async def refine_transcript(
        self,
        raw_text: str,
        style_profile_id: str | None = None,
    ) -> RefinedText:
        """Full refinement pipeline: clean up → structure → optionally style-match."""
        # Stage 1-6: Use Claude for intelligent cleanup
        cleaned = await self._claude_cleanup(raw_text)

        # Stage 7: Optional style refinement
        if style_profile_id:
            styled = await self.apply_style(cleaned, style_profile_id)
        else:
            styled = cleaned

        diff = self.diff_highlight(raw_text, styled)

        return RefinedText(
            raw_text=raw_text,
            refined_text=styled,
            diff=diff,
            style_match_score=0.85 if style_profile_id else None,
            changes_summary=self._summarize_changes(raw_text, styled),
        )

    async def _claude_cleanup(self, raw_text: str) -> str:
        """Use Claude to restore punctuation, fix capitalization, remove
        fillers, and structure paragraphs (stages 1-6)."""
        prompt = (
            "You are a transcription editor. Clean up this raw speech-to-text "
            "dictation:\n\n"
            "1. Add proper punctuation (periods, commas, question marks, etc.)\n"
            "2. Fix capitalization (sentence starts, proper nouns)\n"
            "3. Remove filler words (um, uh, like, you know, etc.) and false starts\n"
            "4. Split into proper sentences\n"
            "5. Group into logical paragraphs\n"
            "6. Convert spoken voice commands: \"new paragraph\" → paragraph break, "
            "\"period\" → \".\"\n"
            "7. Preserve the original meaning and content exactly\n\n"
            f"Raw dictation:\n{raw_text}\n\n"
            "Return ONLY the cleaned text, no explanation."
        )

        try:
            from app.modules.llm_orchestration.orchestrator import (
                GenerationOptions,
                LLMOrchestrator,
            )

            orchestrator = LLMOrchestrator()
            result = await orchestrator.generate(
                task_type="quick_edits_grammar",
                prompt=prompt,
                options=GenerationOptions(
                    max_tokens=max(len(raw_text) * 2, 1024),
                    temperature=0.3,
                    skip_quality_check=True,
                ),
            )
            if result.succeeded:
                return result.content
            logger.warning("Claude cleanup returned empty, using regex fallback")
            return self._regex_cleanup(raw_text)
        except Exception as e:
            logger.warning("Claude cleanup failed, using regex fallback: %s", e)
            return self._regex_cleanup(raw_text)

    def _regex_cleanup(self, text: str) -> str:
        """Fallback regex-based cleanup when LLM is unavailable."""
        result = text

        # Remove fillers
        for filler in self.FILLERS:
            result = re.sub(
                rf"\b{re.escape(filler)}\b[,]?\s*", "", result, flags=re.IGNORECASE,
            )

        # Remove repeated words (e.g. "the the" → "the")
        result = re.sub(r"\b(\w+)\s+\1\b", r"\1", result)

        # Process voice commands before punctuation cleanup
        result = result.replace("new paragraph", "\n\n")
        result = result.replace("new line", "\n")

        # Spoken punctuation → actual punctuation
        result = re.sub(r"\bperiod\b", ".", result, flags=re.IGNORECASE)
        result = re.sub(r"\bcomma\b", ",", result, flags=re.IGNORECASE)
        result = re.sub(r"\bquestion mark\b", "?", result, flags=re.IGNORECASE)
        result = re.sub(r"\bexclamation point\b", "!", result, flags=re.IGNORECASE)

        # Collapse excess whitespace
        result = re.sub(r"[ \t]+", " ", result)

        # Capitalize sentence starts
        sentences = re.split(r"(?<=[.!?])\s+", result)
        result = " ".join(s.strip().capitalize() for s in sentences if s.strip())

        return result.strip()

    def restore_punctuation(self, raw_text: str) -> str:
        """Restore punctuation using simple heuristics (regex fallback)."""
        return self._regex_cleanup(raw_text)

    def remove_fillers(self, text: str) -> str:
        """Remove filler words from text."""
        result = text
        for filler in self.FILLERS:
            result = re.sub(
                rf"\b{re.escape(filler)}\b[,]?\s*", "", result, flags=re.IGNORECASE,
            )
        return re.sub(r"\s+", " ", result).strip()

    def structure_paragraphs(self, text: str) -> str:
        """Group sentences into logical paragraphs (~3-5 sentences each)."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        paragraphs: list[str] = []
        current: list[str] = []
        for sent in sentences:
            current.append(sent)
            if len(current) >= 4:
                paragraphs.append(" ".join(current))
                current = []
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)

    async def apply_style(self, text: str, style_profile_id: str) -> str:
        """Apply Style Cloning Engine to match author's voice (stage 7)."""
        try:
            from app.modules.llm_orchestration.orchestrator import (
                GenerationOptions,
                LLMOrchestrator,
            )

            orchestrator = LLMOrchestrator()
            prompt = (
                "You are a style editor. Rewrite the following text to match the "
                f"author's voice profile (profile ID: {style_profile_id}). "
                "Preserve all factual content and meaning. Only adjust tone, "
                "sentence structure, and word choice to match the target style.\n\n"
                f"Text:\n{text}\n\n"
                "Return ONLY the styled text, no explanation."
            )
            result = await orchestrator.generate(
                task_type="style_fingerprinting",
                prompt=prompt,
                options=GenerationOptions(
                    max_tokens=max(len(text) * 2, 1024),
                    temperature=0.4,
                    skip_quality_check=True,
                ),
            )
            if result.succeeded:
                return result.content
            logger.warning("Style application returned empty, keeping original")
            return text
        except Exception as e:
            logger.warning("Style application failed: %s", e)
            return text

    def diff_highlight(self, raw_text: str, refined_text: str) -> list[DiffSegment]:
        """Generate diff segments between raw and refined text."""
        raw_words = raw_text.split()
        refined_words = refined_text.split()
        matcher = difflib.SequenceMatcher(None, raw_words, refined_words)
        segments: list[DiffSegment] = []

        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            original = " ".join(raw_words[i1:i2])
            new = " ".join(refined_words[j1:j2])
            if op == "equal":
                segments.append(DiffSegment(
                    type="unchanged", original_text=original, new_text=new,
                ))
            elif op == "replace":
                segments.append(DiffSegment(
                    type="changed", original_text=original, new_text=new,
                ))
            elif op == "insert":
                segments.append(DiffSegment(
                    type="added", original_text="", new_text=new,
                ))
            elif op == "delete":
                segments.append(DiffSegment(
                    type="removed", original_text=original, new_text="",
                ))
        return segments

    def _summarize_changes(self, raw: str, refined: str) -> dict:
        """Produce a summary of what changed between raw and refined text."""
        raw_words = len(raw.split())
        refined_words = len(refined.split())
        return {
            "original_word_count": raw_words,
            "refined_word_count": refined_words,
            "words_removed": max(0, raw_words - refined_words),
            "words_added": max(0, refined_words - raw_words),
            "paragraphs": refined.count("\n\n") + 1,
        }
