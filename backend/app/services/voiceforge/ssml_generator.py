"""Intelligent SSML Generator using Claude for text analysis.

Converts plain manuscript text into SSML-annotated text for natural narration.
Uses the project's LLM orchestration layer for AI-powered text analysis
(dialogue detection, emotion analysis, emphasis) with regex-based fallbacks
when the LLM is unavailable.

SSML enhancements applied:
  1. Paragraph breaks           — ``<break time="500ms"/>`` between paragraphs
  2. Chapter transitions        — ``<break time="1500ms"/>`` with tone shift
  3. Dialogue detection         — quoted speech → character voice switching
  4. Emphasis                   — contextual emphasis via ``<emphasis>``
  5. Pronunciation              — custom dictionary via ``<phoneme>``
  6. Numbers & dates            — ``<say-as>`` for spoken form
  7. Abbreviations              — expand to spoken form ("Dr." → "Doctor")
  8. Pace variation             — ``<prosody rate="...">`` for drama/action
  9. Emotional tone             — ``<prosody>`` hints for emotional passages
 10. Lists                      — pauses between items
 11. Headings                   — stronger break + pitch change
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, cast

from defusedxml import ElementTree  # hardened parser: SSML can be user-submitted

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class DialogueSegment:
    """A detected span of quoted dialogue with optional character and emotion."""

    character: str
    text: str
    emotion: str | None = None
    start_index: int = 0
    end_index: int = 0


@dataclass
class EmotionSegment:
    """A detected emotional passage with intensity."""

    text: str
    emotion: str
    intensity: float = 0.5
    start_index: int = 0
    end_index: int = 0


@dataclass
class SSMLResult:
    """Complete result of SSML generation."""

    original_text: str
    ssml_text: str
    dialogue_segments: list[DialogueSegment] = field(default_factory=list)
    emotion_segments: list[EmotionSegment] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Abbreviation dictionary (extensible)
# ---------------------------------------------------------------------------

DEFAULT_ABBREVIATIONS: dict[str, str] = {
    "Dr.": "Doctor",
    "Mr.": "Mister",
    "Mrs.": "Missus",
    "Ms.": "Miss",
    "Prof.": "Professor",
    "St.": "Saint",
    "Jr.": "Junior",
    "Sr.": "Senior",
    "Ave.": "Avenue",
    "Blvd.": "Boulevard",
    "Dept.": "Department",
    "Est.": "Established",
    "Fig.": "Figure",
    "Gen.": "General",
    "Gov.": "Governor",
    "Inc.": "Incorporated",
    "Lt.": "Lieutenant",
    "Mt.": "Mount",
    "No.": "Number",
    "Rev.": "Reverend",
    "Sgt.": "Sergeant",
    "Vol.": "Volume",
    "vs.": "versus",
    "etc.": "et cetera",
    "approx.": "approximately",
    "dept.": "department",
    "govt.": "government",
    "est.": "established",
}

# ---------------------------------------------------------------------------
# Regex patterns for fallback detection
# ---------------------------------------------------------------------------

# Matches "quoted text" followed by optional dialogue tag (she said, he whispered)
_DIALOGUE_PATTERN = re.compile(
    r'"([^"]+)"\s*'
    r"(?:,?\s*(?:said|whispered|shouted|exclaimed|asked|replied|muttered|"
    r"cried|yelled|murmured|stammered|gasped|sighed|laughed|snapped|"
    r"growled|hissed|pleaded|demanded|insisted|suggested|announced|"
    r"declared|continued|added|interrupted|called|screamed|sobbed)"
    r"(?:\s+(\w+))?)?",
    re.IGNORECASE,
)

# Matches common heading patterns (all-caps lines, "Chapter N", etc.)
_HEADING_PATTERN = re.compile(
    r"^(?:"
    r"(?:CHAPTER|PART|SECTION|BOOK|PROLOGUE|EPILOGUE|INTRODUCTION|CONCLUSION)"
    r"(?:\s+[\dIVXLCDM]+)?(?:\s*[:\-—]\s*.*)?"
    r"|[A-Z][A-Z\s]{4,}"  # all-caps line of 5+ chars
    r")$",
    re.MULTILINE,
)

# Matches numbered/bulleted list items
_LIST_ITEM_PATTERN = re.compile(
    r"^(?:\s*(?:\d+[.)]\s+|[-•*]\s+))(.+)$",
    re.MULTILINE,
)

# Matches 4-digit years
_YEAR_PATTERN = re.compile(r"\b(\d{4})\b")

# Matches dates like "January 5, 2024" or "05/12/2024"
_DATE_PATTERN = re.compile(
    r"\b(?:"
    r"(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2}(?:,\s*\d{4})?"
    r"|\d{1,2}/\d{1,2}/\d{2,4}"
    r")\b",
    re.IGNORECASE,
)

# Matches standalone numbers (currency, quantities, etc.)
_NUMBER_PATTERN = re.compile(r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\b")

# Matches emphasis cues: *italic*, **bold**, ALL-CAPS words (3+ letters)
_EMPHASIS_PATTERN = re.compile(
    r"\*\*([^*]+)\*\*"  # **bold**
    r"|\*([^*]+)\*"  # *italic*
    r"|\b([A-Z]{3,})\b"  # ALL CAPS words (3+ chars, not headings)
)

# Emotion keywords mapped to prosody hints
_EMOTION_KEYWORDS: dict[str, list[str]] = {
    "sad": [
        "tears",
        "crying",
        "sobbed",
        "grief",
        "sorrow",
        "mourning",
        "heartbroken",
        "weeping",
        "devastated",
        "loss",
    ],
    "angry": [
        "furious",
        "rage",
        "slammed",
        "screamed",
        "yelled",
        "fury",
        "livid",
        "seething",
        "outraged",
        "wrath",
    ],
    "fear": [
        "terrified",
        "trembling",
        "shaking",
        "horror",
        "dread",
        "panic",
        "frightened",
        "scared",
        "alarmed",
        "petrified",
    ],
    "joy": [
        "laughed",
        "smiled",
        "grinned",
        "delighted",
        "ecstatic",
        "jubilant",
        "beaming",
        "elated",
        "thrilled",
        "overjoyed",
    ],
    "suspense": [
        "suddenly",
        "darkness",
        "silence",
        "shadow",
        "crept",
        "lurking",
        "whispered",
        "eerie",
        "ominous",
        "dread",
    ],
}

# Prosody settings per emotion
_EMOTION_PROSODY: dict[str, dict[str, str]] = {
    "sad": {"rate": "slow", "pitch": "low", "volume": "soft"},
    "angry": {"rate": "fast", "pitch": "high", "volume": "loud"},
    "fear": {"rate": "medium", "pitch": "low", "volume": "soft"},
    "joy": {"rate": "medium", "pitch": "high", "volume": "medium"},
    "suspense": {"rate": "slow", "pitch": "low", "volume": "soft"},
}

# Claude analysis prompt
_ANALYSIS_SYSTEM_PROMPT = """\
You are an expert text analyst for audiobook narration. Analyze the given text \
and return a JSON object with the following structure. Be precise with indices \
(character offsets from the start of the text).

{
  "dialogue_segments": [
    {
      "character": "character name or 'Narrator'",
      "text": "the quoted dialogue text",
      "emotion": "neutral|sad|angry|fear|joy|suspense",
      "start_index": 0,
      "end_index": 50
    }
  ],
  "emotion_segments": [
    {
      "text": "the emotional passage",
      "emotion": "sad|angry|fear|joy|suspense",
      "intensity": 0.7,
      "start_index": 100,
      "end_index": 200
    }
  ],
  "emphasis_words": [
    {
      "word": "never",
      "start_index": 55,
      "end_index": 60
    }
  ],
  "pace_suggestions": [
    {
      "text": "passage text",
      "pace": "slow|fast|medium",
      "reason": "dramatic tension",
      "start_index": 0,
      "end_index": 100
    }
  ]
}

Rules:
- Only include dialogue that is actually quoted speech (between quotation marks)
- Character names should be inferred from dialogue tags ("said John" → "John")
- Emotion intensity is 0.0 (subtle) to 1.0 (overwhelming)
- Emphasis words are contextually important — do NOT mark every capitalized word
- Pace "slow" for dramatic/emotional, "fast" for action/chase, "medium" for normal
- Return ONLY valid JSON, no markdown fences or explanation"""


# ---------------------------------------------------------------------------
# SSML Generator
# ---------------------------------------------------------------------------


def _xml_escape(text: str) -> str:
    """Escape XML special characters in text content."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text.replace("'", "&apos;")


class SSMLGenerator:
    """Convert plain manuscript text into SSML-annotated text.

    Uses the project's LLM orchestration layer for intelligent analysis
    (dialogue detection, emotion, emphasis, pace) with regex-based
    fallbacks when the LLM is unavailable.

    Parameters
    ----------
    orchestrator :
        An ``LLMOrchestrator`` instance (from ``app.modules.llm_orchestration``).
        If *None*, only regex-based fallback analysis is used.
    abbreviations :
        Additional abbreviation expansions merged with the defaults.
    """

    def __init__(
        self,
        orchestrator: Any | None = None,
        abbreviations: dict[str, str] | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._abbreviations = {**DEFAULT_ABBREVIATIONS}
        if abbreviations:
            self._abbreviations.update(abbreviations)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_ssml(
        self,
        text: str,
        project_config: dict | None = None,
        pronunciation_dict: dict | None = None,
    ) -> SSMLResult:
        """Convert plain text to SSML using Claude analysis.

        Parameters
        ----------
        text :
            Raw manuscript text.
        project_config :
            Optional project-level settings (e.g. default break durations).
        pronunciation_dict :
            Custom word → IPA pronunciation mappings applied via ``<phoneme>``.

        Returns
        -------
        SSMLResult
            Contains the original text, the SSML output, and detected segments.
        """
        config = project_config or {}
        para_break = config.get("paragraph_break_ms", 500)
        chapter_break = config.get("chapter_break_ms", 1500)

        # Step 1: Attempt LLM-based analysis; fall back to regex
        analysis = await self._analyze_text(text)

        dialogue_segments = analysis.get("dialogue_segments", [])
        emotion_segments = analysis.get("emotion_segments", [])
        emphasis_words = analysis.get("emphasis_words", [])
        pace_suggestions = analysis.get("pace_suggestions", [])

        # Convert raw dicts to dataclass instances
        dialogue_objs = [
            DialogueSegment(
                character=d.get("character", "Narrator"),
                text=d.get("text", ""),
                emotion=d.get("emotion"),
                start_index=d.get("start_index", 0),
                end_index=d.get("end_index", 0),
            )
            for d in dialogue_segments
        ]
        emotion_objs = [
            EmotionSegment(
                text=e.get("text", ""),
                emotion=e.get("emotion", "neutral"),
                intensity=e.get("intensity", 0.5),
                start_index=e.get("start_index", 0),
                end_index=e.get("end_index", 0),
            )
            for e in emotion_segments
        ]

        # Step 2: Build SSML from analysis
        ssml = self._build_ssml(
            text,
            dialogue_segments=dialogue_segments,
            emotion_segments=emotion_segments,
            emphasis_words=emphasis_words,
            pace_suggestions=pace_suggestions,
            para_break_ms=para_break,
            chapter_break_ms=chapter_break,
        )

        # Step 3: Post-processing passes
        ssml = self.expand_abbreviations(ssml)
        ssml = self._convert_numbers_and_dates(ssml)

        if pronunciation_dict:
            ssml = self.apply_pronunciation_dict(ssml, pronunciation_dict)

        # Wrap in root <speak> element
        ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis">\n{ssml}\n</speak>'

        return SSMLResult(
            original_text=text,
            ssml_text=ssml,
            dialogue_segments=dialogue_objs,
            emotion_segments=emotion_objs,
        )

    async def detect_dialogue(self, text: str) -> list[DialogueSegment]:
        """Detect dialogue segments with character attribution.

        Tries LLM analysis first; falls back to regex-based detection.
        """
        analysis = await self._analyze_text(text)
        segments = analysis.get("dialogue_segments", [])
        return [
            DialogueSegment(
                character=d.get("character", "Narrator"),
                text=d.get("text", ""),
                emotion=d.get("emotion"),
                start_index=d.get("start_index", 0),
                end_index=d.get("end_index", 0),
            )
            for d in segments
        ]

    async def detect_emotions(self, text: str) -> list[EmotionSegment]:
        """Detect emotional tone of text passages.

        Tries LLM analysis first; falls back to keyword-based detection.
        """
        analysis = await self._analyze_text(text)
        segments = analysis.get("emotion_segments", [])
        return [
            EmotionSegment(
                text=e.get("text", ""),
                emotion=e.get("emotion", "neutral"),
                intensity=e.get("intensity", 0.5),
                start_index=e.get("start_index", 0),
                end_index=e.get("end_index", 0),
            )
            for e in segments
        ]

    def expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations to spoken form.

        Performs whole-word boundary replacement so that "Dr." inside a
        larger word is not accidentally expanded.
        """
        result = text
        for abbr, expansion in self._abbreviations.items():
            # Use word-boundary-aware replacement
            # Escape the abbreviation for regex (dots are special)
            pattern = re.compile(r"(?<!\w)" + re.escape(abbr) + r"(?!\w)")
            result = pattern.sub(expansion, result)
        return result

    def apply_pronunciation_dict(self, ssml: str, dictionary: dict) -> str:
        """Apply custom pronunciation entries as SSML ``<phoneme>`` tags.

        Parameters
        ----------
        ssml :
            SSML text (may already contain tags).
        dictionary :
            Mapping of ``word`` → ``IPA pronunciation``.
            Example: ``{"Hermione": "her-MY-uh-nee"}``
        """
        result = ssml
        for word, ipa in dictionary.items():
            # Only replace text content, not inside existing XML tags
            # Use negative lookbehind/lookahead for < and >
            pattern = re.compile(
                r"(?<![<\w])" + re.escape(word) + r"(?![>\w])",
                re.IGNORECASE,
            )
            phoneme_tag = f'<phoneme alphabet="ipa" ph="{_xml_escape(ipa)}">' f"{_xml_escape(word)}</phoneme>"
            result = pattern.sub(phoneme_tag, result)
        return result

    def validate_ssml(self, ssml_text: str) -> dict:
        """Validate SSML syntax.

        Returns a dict with:
        - ``valid`` (bool): whether the SSML parses as valid XML.
        - ``errors`` (list[str]): any parse errors found.
        - ``warnings`` (list[str]): non-fatal issues.
        - ``tag_counts`` (dict[str, int]): count of each SSML tag used.
        """
        errors: list[str] = []
        warnings: list[str] = []
        tag_counts: dict[str, int] = {}

        # Check for root <speak> element
        if not ssml_text.strip().startswith("<speak"):
            warnings.append("SSML should start with a <speak> element.")

        # Attempt XML parse
        try:
            root = ElementTree.fromstring(ssml_text)
        except ElementTree.ParseError as exc:
            errors.append(f"XML parse error: {exc}")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings,
                "tag_counts": tag_counts,
            }

        # Walk the tree and count tags
        for elem in root.iter():
            tag = elem.tag
            # Strip namespace if present
            if "}" in tag:
                tag = tag.split("}", 1)[1]
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Validate known SSML tags
        valid_tags = {
            "speak",
            "break",
            "prosody",
            "emphasis",
            "phoneme",
            "say-as",
            "p",
            "s",
            "voice",
            "mark",
            "sub",
            "audio",
            "desc",
            "lang",
            "meta",
            "metadata",
        }
        for tag in tag_counts:
            if tag not in valid_tags:
                warnings.append(f"Non-standard SSML tag: <{tag}>")

        # Check for unclosed prosody nesting issues
        prosody_count = tag_counts.get("prosody", 0)
        if prosody_count > 50:
            warnings.append(
                f"High prosody tag count ({prosody_count}). " "Consider reducing nesting for TTS engine compatibility."
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "tag_counts": tag_counts,
        }

    # ------------------------------------------------------------------
    # LLM-based analysis (with fallback)
    # ------------------------------------------------------------------

    async def _analyze_text(self, text: str) -> dict:
        """Analyze text using Claude via the orchestrator.

        Falls back to regex-based analysis if the LLM call fails or
        no orchestrator is configured.
        """
        if self._orchestrator is not None:
            try:
                return await self._llm_analyze(text)
            except Exception:
                logger.warning(
                    "LLM analysis failed, falling back to regex-based detection",
                    exc_info=True,
                )

        return self._regex_analyze(text)

    async def _llm_analyze(self, text: str) -> dict:
        """Call Claude via the LLM orchestrator for text analysis."""
        from app.modules.llm_orchestration.orchestrator import GenerationOptions

        # Use a truncated version for very long texts to stay within token limits
        analysis_text = text[:15_000] if len(text) > 15_000 else text

        prompt = (
            "Analyze the following manuscript text for audiobook narration. "
            "Return ONLY a JSON object as specified in the system prompt.\n\n"
            f"TEXT:\n{analysis_text}"
        )

        # _analyze_text is the only caller and guards on this, but the
        # narrowing does not cross the method boundary — state it here.
        orchestrator = self._orchestrator
        if orchestrator is None:
            raise RuntimeError("_llm_analyze requires a configured orchestrator")

        result = await orchestrator.generate(
            task_type="long_form_writing",
            prompt=prompt,
            options=GenerationOptions(
                temperature=0.2,
                max_tokens=4096,
                system_prompt=_ANALYSIS_SYSTEM_PROMPT,
                skip_cache=True,
                skip_quality_check=True,
            ),
        )

        if not result.succeeded:
            msg = "LLM analysis returned empty result"
            raise RuntimeError(msg)

        # Parse the JSON response (strip markdown fences if present)
        content = result.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

        return cast("dict[Any, Any]", json.loads(content))

    def _regex_analyze(self, text: str) -> dict:
        """Regex-based fallback analysis when LLM is unavailable."""
        dialogue_segments = self._regex_detect_dialogue(text)
        emotion_segments = self._regex_detect_emotions(text)
        emphasis_words = self._regex_detect_emphasis(text)
        pace_suggestions = self._regex_detect_pace(text)

        return {
            "dialogue_segments": dialogue_segments,
            "emotion_segments": emotion_segments,
            "emphasis_words": emphasis_words,
            "pace_suggestions": pace_suggestions,
        }

    def _regex_detect_dialogue(self, text: str) -> list[dict]:
        """Detect dialogue using regex patterns."""
        segments: list[dict] = []
        for match in _DIALOGUE_PATTERN.finditer(text):
            dialogue_text = match.group(1)
            character = match.group(2) or "Narrator"
            segments.append(
                {
                    "character": character.capitalize() if character != "Narrator" else character,
                    "text": dialogue_text,
                    "emotion": "neutral",
                    "start_index": match.start(),
                    "end_index": match.end(),
                }
            )
        return segments

    def _regex_detect_emotions(self, text: str) -> list[dict]:
        """Detect emotions using keyword matching."""
        segments: list[dict] = []
        # Split into sentences for granular emotion detection
        sentences = re.split(r"(?<=[.!?])\s+", text)
        offset = 0

        for sentence in sentences:
            best_emotion: str | None = None
            best_score = 0

            for emotion, keywords in _EMOTION_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw.lower() in sentence.lower())
                if score > best_score:
                    best_score = score
                    best_emotion = emotion

            if best_emotion and best_score >= 1:
                start = text.find(sentence, offset)
                if start == -1:
                    start = offset
                segments.append(
                    {
                        "text": sentence,
                        "emotion": best_emotion,
                        "intensity": min(best_score * 0.3, 1.0),
                        "start_index": start,
                        "end_index": start + len(sentence),
                    }
                )

            offset = text.find(sentence, offset)
            if offset != -1:
                offset += len(sentence)

        return segments

    def _regex_detect_emphasis(self, text: str) -> list[dict]:
        """Detect emphasis using formatting patterns and caps."""
        words: list[dict] = []
        for match in _EMPHASIS_PATTERN.finditer(text):
            word = match.group(1) or match.group(2) or match.group(3)
            if word:
                words.append(
                    {
                        "word": word,
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )
        return words

    def _regex_detect_pace(self, text: str) -> list[dict]:
        """Detect pace using heuristics (sentence length, action verbs)."""
        suggestions: list[dict] = []
        paragraphs = text.split("\n\n")
        offset = 0

        action_verbs = {
            "ran",
            "sprinted",
            "dashed",
            "chased",
            "fled",
            "raced",
            "jumped",
            "crashed",
            "exploded",
            "fired",
            "dodged",
            "lunged",
            "slammed",
            "burst",
            "charged",
            "dove",
            "struck",
        }
        drama_words = {
            "silence",
            "stillness",
            "slowly",
            "carefully",
            "gently",
            "quietly",
            "softly",
            "tenderly",
            "moment",
            "pause",
            "breath",
            "whisper",
            "waited",
        }

        for para in paragraphs:
            para_stripped = para.strip()
            if not para_stripped:
                offset += len(para) + 2
                continue

            para_lower = para_stripped.lower()
            words_in_para = set(re.findall(r"\b\w+\b", para_lower))

            action_count = len(words_in_para & action_verbs)
            drama_count = len(words_in_para & drama_words)

            start = text.find(para_stripped, offset)
            if start == -1:
                start = offset

            if action_count >= 2:
                suggestions.append(
                    {
                        "text": para_stripped[:80] + ("..." if len(para_stripped) > 80 else ""),
                        "pace": "fast",
                        "reason": "action sequence",
                        "start_index": start,
                        "end_index": start + len(para_stripped),
                    }
                )
            elif drama_count >= 2:
                suggestions.append(
                    {
                        "text": para_stripped[:80] + ("..." if len(para_stripped) > 80 else ""),
                        "pace": "slow",
                        "reason": "dramatic tension",
                        "start_index": start,
                        "end_index": start + len(para_stripped),
                    }
                )

            offset = start + len(para_stripped)

        return suggestions

    # ------------------------------------------------------------------
    # SSML construction
    # ------------------------------------------------------------------

    def _build_ssml(
        self,
        text: str,
        *,
        dialogue_segments: list[dict],
        emotion_segments: list[dict],
        emphasis_words: list[dict],
        pace_suggestions: list[dict],
        para_break_ms: int = 500,
        chapter_break_ms: int = 1500,
    ) -> str:
        """Build SSML string from analysis results."""
        # Process paragraph by paragraph
        paragraphs = text.split("\n\n")
        ssml_parts: list[str] = []

        # Build lookup sets for quick matching
        emphasis_set = {w["word"].lower() for w in emphasis_words}
        emotion_lookup = self._build_range_lookup(emotion_segments)
        pace_lookup = self._build_range_lookup(pace_suggestions)
        dialogue_lookup = self._build_range_lookup(dialogue_segments)

        offset = 0
        for i, paragraph in enumerate(paragraphs):
            para_stripped = paragraph.strip()
            if not para_stripped:
                offset += len(paragraph) + 2  # +2 for \n\n
                continue

            para_start = text.find(para_stripped, offset)
            if para_start == -1:
                para_start = offset
            para_end = para_start + len(para_stripped)

            # Check if this is a heading / chapter transition
            is_heading = bool(_HEADING_PATTERN.match(para_stripped))

            if is_heading:
                ssml_parts.append(
                    f'<break time="{chapter_break_ms}ms"/>'
                    f'\n<prosody pitch="high" rate="slow">'
                    f"\n  {_xml_escape(para_stripped)}"
                    f"\n</prosody>"
                    f'\n<break time="{chapter_break_ms}ms"/>'
                )
            elif _LIST_ITEM_PATTERN.match(para_stripped):
                # List items: add pauses between items
                ssml_parts.append(self._process_list(para_stripped))
            else:
                # Normal paragraph: apply dialogue, emotion, pace, emphasis
                processed = self._process_paragraph(
                    para_stripped,
                    para_start=para_start,
                    para_end=para_end,
                    dialogue_lookup=dialogue_lookup,
                    emotion_lookup=emotion_lookup,
                    pace_lookup=pace_lookup,
                    emphasis_set=emphasis_set,
                )
                ssml_parts.append(f"<p>{processed}</p>")

            # Add paragraph break (unless it was a heading which has its own)
            if not is_heading and i < len(paragraphs) - 1:
                ssml_parts.append(f'<break time="{para_break_ms}ms"/>')

            offset = para_end

        return "\n".join(ssml_parts)

    def _process_paragraph(
        self,
        text: str,
        *,
        para_start: int,
        para_end: int,
        dialogue_lookup: list[dict],
        emotion_lookup: list[dict],
        pace_lookup: list[dict],
        emphasis_set: set[str],
    ) -> str:
        """Process a single paragraph with all SSML enhancements."""
        result = text

        # Apply emphasis to individual words
        result = self._apply_emphasis(result, emphasis_set)

        # Check for dialogue in this paragraph range
        for seg in dialogue_lookup:
            seg_start = seg.get("start_index", 0)
            seg_end = seg.get("end_index", 0)
            if seg_start >= para_start and seg_end <= para_end:
                quoted = seg.get("text", "")
                character = seg.get("character", "Narrator")
                emotion = seg.get("emotion", "neutral")

                # Build voice/prosody wrapper for dialogue
                voice_ssml = self._dialogue_to_ssml(quoted, character, emotion)

                # Replace the raw quoted text with SSML version
                escaped_quoted = _xml_escape(quoted)
                # Replace within already-processed text
                result = result.replace(f"&quot;{escaped_quoted}&quot;", voice_ssml, 1)
                # Also try with original quotes (if not yet escaped)
                result = result.replace(f'"{quoted}"', voice_ssml, 1)

        # Apply emotion prosody for the whole paragraph
        dominant_emotion = self._find_dominant(emotion_lookup, para_start, para_end)
        if dominant_emotion and dominant_emotion != "neutral":
            prosody_attrs = _EMOTION_PROSODY.get(dominant_emotion, {})
            if prosody_attrs:
                attrs_str = " ".join(f'{k}="{v}"' for k, v in prosody_attrs.items())
                result = f"<prosody {attrs_str}>{result}</prosody>"

        # Apply pace variation
        pace_seg = self._find_pace(pace_lookup, para_start, para_end)
        if pace_seg:
            pace = pace_seg.get("pace", "medium")
            if pace != "medium":
                rate = "slow" if pace == "slow" else "fast"
                result = f'<prosody rate="{rate}">{result}</prosody>'

        return result

    def _apply_emphasis(self, text: str, emphasis_set: set[str]) -> str:
        """Wrap emphasis words with ``<emphasis>`` tags."""
        if not emphasis_set:
            return _xml_escape(text)

        # Tokenize while preserving whitespace and punctuation
        tokens = re.split(r"(\s+)", text)
        result_parts: list[str] = []

        for token in tokens:
            # Strip punctuation to check the core word
            core = re.sub(r"[^\w]", "", token).lower()
            if core in emphasis_set:
                escaped = _xml_escape(token)
                result_parts.append(f'<emphasis level="strong">{escaped}</emphasis>')
            else:
                result_parts.append(_xml_escape(token))

        return "".join(result_parts)

    def _dialogue_to_ssml(self, text: str, character: str, emotion: str | None) -> str:
        """Convert a dialogue segment to SSML with voice and prosody hints."""
        escaped = _xml_escape(text)

        # Use a mark tag to annotate character (TTS engines can use this)
        parts = [f'<mark name="char:{_xml_escape(character)}"/>']

        if emotion and emotion in _EMOTION_PROSODY:
            prosody = _EMOTION_PROSODY[emotion]
            attrs = " ".join(f'{k}="{v}"' for k, v in prosody.items())
            parts.append(f"<prosody {attrs}>&quot;{escaped}&quot;</prosody>")
        else:
            parts.append(f"&quot;{escaped}&quot;")

        return "".join(parts)

    def _process_list(self, text: str) -> str:
        """Add pauses between list items."""
        lines = text.split("\n")
        ssml_items: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            ssml_items.append(f"<s>{_xml_escape(stripped)}</s>")
            ssml_items.append('<break time="300ms"/>')

        # Remove trailing break
        if ssml_items and ssml_items[-1].startswith("<break"):
            ssml_items.pop()

        return "\n".join(ssml_items)

    def _convert_numbers_and_dates(self, text: str) -> str:
        """Convert numbers and dates to SSML ``<say-as>`` tags.

        Only processes text content outside of existing XML tags.
        """
        # Process dates first (more specific patterns)
        text = _DATE_PATTERN.sub(
            lambda m: f'<say-as interpret-as="date">{m.group(0)}</say-as>',
            text,
        )

        # Process standalone years (4-digit numbers that look like years)
        def _year_replace(match: re.Match) -> str:  # type: ignore[type-arg]
            num = int(match.group(1))
            if 1000 <= num <= 2100:
                return f'<say-as interpret-as="date" format="y">{match.group(1)}</say-as>'
            return cast("str", match.group(0))

        # Only replace years that are not already inside a tag
        text = re.sub(
            r'(?<!["\w>])(\d{4})(?!["\w<])',
            _year_replace,
            text,
        )

        # Process other numbers (currency, cardinals)
        def _number_replace(match: re.Match) -> str:  # type: ignore[type-arg]
            num_str = match.group(1)
            # Skip if already inside a tag
            before = text[max(0, match.start() - 1) : match.start()]
            if before in ('"', ">"):
                return cast("str", num_str)
            return f'<say-as interpret-as="cardinal">{num_str}</say-as>'

        return re.sub(
            r'(?<!["\w>])(\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?!["\w<])',
            _number_replace,
            text,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_range_lookup(segments: list[dict]) -> list[dict]:
        """Return segments sorted by start_index for range queries."""
        return sorted(segments, key=lambda s: s.get("start_index", 0))

    @staticmethod
    def _find_dominant(
        segments: list[dict],
        start: int,
        end: int,
    ) -> str | None:
        """Find the dominant emotion/attribute for a text range."""
        for seg in segments:
            seg_start = seg.get("start_index", 0)
            seg_end = seg.get("end_index", 0)
            # Check for overlap
            if seg_start < end and seg_end > start:
                return seg.get("emotion")
        return None

    @staticmethod
    def _find_pace(
        segments: list[dict],
        start: int,
        end: int,
    ) -> dict | None:
        """Find the pace suggestion that overlaps with the given range."""
        for seg in segments:
            seg_start = seg.get("start_index", 0)
            seg_end = seg.get("end_index", 0)
            if seg_start < end and seg_end > start:
                return seg
        return None
