# VF13: Dictation Refiner Service

## Task
Create the dictation refinement pipeline that transforms raw ASR transcript into polished prose.

## Files to Create

### `backend/app/services/voiceforge/dictation_refiner.py`

**Pipeline stages:**
1. Punctuation Restoration — restore periods, commas, semicolons, etc.
2. Capitalization Fix — proper nouns, sentence starts
3. Filler Removal — "um", "uh", "like", "you know", false starts, repeats
4. Sentence Boundary Detection — split run-on dictation
5. Paragraph Structuring — group into logical paragraphs
6. Voice Command Extraction — "new paragraph" → actual break
7. Style Refinement — Style Cloning Engine to match author's voice

Uses Claude for stages 1-6 (single prompt), then Style Cloning Engine for stage 7.

```python
"""Dictation Refinement Pipeline."""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class DiffSegment:
    type: str  # 'added', 'removed', 'unchanged', 'changed'
    original_text: str
    new_text: str
    start_index: int = 0
    end_index: int = 0

@dataclass
class RefinedText:
    raw_text: str
    refined_text: str
    diff: list[DiffSegment] = field(default_factory=list)
    style_match_score: float | None = None
    changes_summary: dict = field(default_factory=dict)

class DictationRefiner:
    # Common fillers to remove
    FILLERS = ["um", "uh", "er", "ah", "like", "you know", "i mean", "sort of", "kind of", "basically"]

    async def refine_transcript(self, raw_text: str, style_profile_id: str | None = None) -> RefinedText:
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
        """Use Claude to restore punctuation, fix capitalization, remove fillers, structure paragraphs."""
        # Build prompt for Claude
        prompt = f"""You are a transcription editor. Clean up this raw speech-to-text dictation:

1. Add proper punctuation (periods, commas, question marks, etc.)
2. Fix capitalization (sentence starts, proper nouns)
3. Remove filler words (um, uh, like, you know, etc.) and false starts
4. Split into proper sentences
5. Group into logical paragraphs
6. Convert spoken voice commands: "new paragraph" → paragraph break, "period" → "."
7. Preserve the original meaning and content exactly

Raw dictation:
{raw_text}

Return ONLY the cleaned text, no explanation."""

        try:
            from app.modules.llm_orchestration.orchestrator import LLMOrchestrator
            orchestrator = LLMOrchestrator()
            result = await orchestrator.generate(prompt=prompt, max_tokens=len(raw_text) * 2)
            return result.get("content", raw_text)
        except Exception as e:
            logger.warning("Claude cleanup failed, using regex fallback: %s", e)
            return self._regex_cleanup(raw_text)

    def _regex_cleanup(self, text: str) -> str:
        """Fallback regex-based cleanup when LLM is unavailable."""
        # Remove fillers
        result = text
        for filler in self.FILLERS:
            result = re.sub(rf'\b{filler}\b\s*', '', result, flags=re.IGNORECASE)
        # Remove repeated words
        result = re.sub(r'\b(\w+)\s+\1\b', r'\1', result)
        # Capitalize sentence starts
        result = '. '.join(s.strip().capitalize() for s in result.split('. ') if s.strip())
        # Process voice commands
        result = result.replace("new paragraph", "\n\n")
        result = result.replace("new line", "\n")
        result = result.replace("period", ".")
        result = result.replace("comma", ",")
        result = result.replace("question mark", "?")
        return result.strip()

    def restore_punctuation(self, raw_text: str) -> str:
        """Restore punctuation using simple heuristics."""
        # This is the regex fallback — Claude does this better
        return self._regex_cleanup(raw_text)

    def remove_fillers(self, text: str) -> str:
        """Remove filler words."""
        result = text
        for filler in self.FILLERS:
            result = re.sub(rf'\b{filler}\b[,]?\s*', '', result, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', result).strip()

    def structure_paragraphs(self, text: str) -> str:
        """Group sentences into logical paragraphs (~3-5 sentences each)."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        paragraphs = []
        current = []
        for sent in sentences:
            current.append(sent)
            if len(current) >= 4:
                paragraphs.append(' '.join(current))
                current = []
        if current:
            paragraphs.append(' '.join(current))
        return '\n\n'.join(paragraphs)

    async def apply_style(self, text: str, style_profile_id: str) -> str:
        """Apply Style Cloning Engine to match author's voice."""
        try:
            from app.modules.style_cloning.service import StyleCloningService
            service = StyleCloningService()
            # Use the conformity checker to adapt text to profile
            result = await service.apply_style_profile(text, style_profile_id)
            return result.get("styled_text", text)
        except Exception as e:
            logger.warning("Style application failed: %s", e)
            return text

    def diff_highlight(self, raw_text: str, refined_text: str) -> list[DiffSegment]:
        """Generate diff segments between raw and refined text."""
        import difflib
        raw_words = raw_text.split()
        refined_words = refined_text.split()
        matcher = difflib.SequenceMatcher(None, raw_words, refined_words)
        segments = []
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            original = ' '.join(raw_words[i1:i2])
            new = ' '.join(refined_words[j1:j2])
            if op == 'equal':
                segments.append(DiffSegment(type='unchanged', original_text=original, new_text=new))
            elif op == 'replace':
                segments.append(DiffSegment(type='changed', original_text=original, new_text=new))
            elif op == 'insert':
                segments.append(DiffSegment(type='added', original_text='', new_text=new))
            elif op == 'delete':
                segments.append(DiffSegment(type='removed', original_text=original, new_text=''))
        return segments

    def _summarize_changes(self, raw: str, refined: str) -> dict:
        raw_words = len(raw.split())
        refined_words = len(refined.split())
        return {
            "original_word_count": raw_words,
            "refined_word_count": refined_words,
            "words_removed": max(0, raw_words - refined_words),
            "words_added": max(0, refined_words - raw_words),
            "paragraphs": refined.count('\n\n') + 1,
        }
```

## Conventions
- Use existing LLM orchestration via `app.modules.llm_orchestration`
- Use existing Style Cloning via `app.modules.style_cloning`
- Always have regex fallback when LLM is unavailable
- Diff uses standard difflib
