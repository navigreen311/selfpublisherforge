"""Children's Books AI Story Generation & Text Analysis.

Provides AI-powered story generation with age-band constraints,
text readability analysis, rhyme pattern detection, bilingual translation,
character continuity checking, and batch prompt fixing for the
Children's Book Studio.
"""

from __future__ import annotations

import logging
import re
import uuid as _uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------


class AgeBand(str, Enum):
    BOARD = "board"  # 0-3 years
    PICTURE = "picture"  # 3-5 years
    EARLY_READER = "early_reader"  # 5-8 years
    CHAPTER = "chapter"  # 8-12 years


class StoryMode(str, Enum):
    PROSE = "prose"
    RHYMING = "rhyming"
    REPETITIVE = "repetitive"


class Tone(str, Enum):
    WARM = "warm_reassuring"
    EXCITING = "exciting"
    HUMOROUS = "humorous"
    EDUCATIONAL = "educational"


class BilingualLayout(str, Enum):
    SIDE_BY_SIDE = "side_by_side"
    ALTERNATING = "alternating"
    BACK_SECTION = "back_section"


# Age-band constraints per the blueprint section 3.5
AGE_BAND_CONSTRAINTS: dict[AgeBand, dict[str, Any]] = {
    AgeBand.BOARD: {
        "max_sentence_words": 5,
        "max_word_letters": 5,
        "vocabulary_level": 500,
        "total_words_min": 50,
        "total_words_max": 150,
        "page_range": (10, 16),
    },
    AgeBand.PICTURE: {
        "max_sentence_words": 8,
        "max_word_letters": 7,
        "vocabulary_level": 2000,
        "total_words_min": 300,
        "total_words_max": 500,
        "page_range": (24, 32),
    },
    AgeBand.EARLY_READER: {
        "max_sentence_words": 12,
        "max_word_letters": 9,
        "vocabulary_level": 5000,
        "total_words_min": 500,
        "total_words_max": 2000,
        "page_range": (32, 48),
    },
    AgeBand.CHAPTER: {
        "max_sentence_words": 15,
        "max_word_letters": None,  # No limit
        "vocabulary_level": None,  # Grade-level
        "total_words_min": 3000,
        "total_words_max": 10000,
        "page_range": (48, 80),
    },
}

# Top-500 common English words for board-book vocabulary checking.
# Larger vocab levels use syllable-count heuristics.
_TOP_500_WORDS: set[str] = {
    "the",
    "a",
    "an",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "is",
    "am",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "can",
    "could",
    "may",
    "might",
    "shall",
    "should",
    "must",
    "my",
    "your",
    "his",
    "her",
    "its",
    "our",
    "their",
    "me",
    "him",
    "us",
    "them",
    "this",
    "that",
    "these",
    "those",
    "and",
    "but",
    "or",
    "not",
    "no",
    "yes",
    "so",
    "if",
    "then",
    "here",
    "there",
    "where",
    "when",
    "what",
    "who",
    "how",
    "why",
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "some",
    "any",
    "many",
    "much",
    "other",
    "another",
    "such",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "big",
    "small",
    "little",
    "long",
    "short",
    "old",
    "new",
    "young",
    "good",
    "bad",
    "great",
    "high",
    "low",
    "right",
    "left",
    "first",
    "last",
    "next",
    "own",
    "same",
    "different",
    "come",
    "go",
    "get",
    "make",
    "take",
    "give",
    "see",
    "look",
    "find",
    "know",
    "think",
    "say",
    "tell",
    "ask",
    "put",
    "run",
    "play",
    "eat",
    "sleep",
    "sit",
    "stand",
    "walk",
    "jump",
    "fly",
    "open",
    "close",
    "read",
    "write",
    "draw",
    "sing",
    "dance",
    "love",
    "like",
    "want",
    "need",
    "help",
    "try",
    "let",
    "start",
    "stop",
    "keep",
    "hold",
    "turn",
    "move",
    "fall",
    "pull",
    "push",
    "happy",
    "sad",
    "funny",
    "nice",
    "pretty",
    "cute",
    "soft",
    "hard",
    "hot",
    "cold",
    "warm",
    "cool",
    "wet",
    "dry",
    "clean",
    "dirty",
    "red",
    "blue",
    "green",
    "yellow",
    "orange",
    "purple",
    "pink",
    "black",
    "white",
    "brown",
    "gray",
    "cat",
    "dog",
    "bird",
    "fish",
    "bear",
    "mouse",
    "bunny",
    "duck",
    "mom",
    "dad",
    "baby",
    "boy",
    "girl",
    "friend",
    "family",
    "house",
    "home",
    "school",
    "tree",
    "flower",
    "sun",
    "moon",
    "star",
    "water",
    "food",
    "book",
    "ball",
    "toy",
    "bed",
    "door",
    "window",
    "day",
    "night",
    "morning",
    "time",
    "name",
    "way",
    "thing",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "very",
    "too",
    "just",
    "now",
    "back",
    "again",
    "always",
    "never",
    "only",
    "also",
    "still",
    "even",
    "really",
    "head",
    "hand",
    "eye",
    "ear",
    "nose",
    "mouth",
    "heart",
    "said",
    "went",
    "came",
    "got",
    "saw",
    "made",
    "took",
    "gave",
    "found",
    "knew",
    "thought",
    "told",
    "ran",
    "ate",
    "sat",
    "please",
    "thank",
    "sorry",
    "hello",
    "goodbye",
    "of",
    "to",
    "for",
    "with",
    "at",
    "from",
    "by",
    "about",
    "into",
    "through",
    "after",
    "before",
    "between",
    "around",
}


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class StoryGenerateRequest(BaseModel):
    """Request body for generating a children's story."""

    story_prompt: str = Field(..., min_length=10, max_length=2000)
    theme_moral: str = Field("", max_length=200)
    main_character: str = Field("", max_length=200)
    setting: str = Field("", max_length=200)
    tone: Tone = Tone.WARM
    story_mode: StoryMode = StoryMode.PROSE
    age_band: AgeBand = AgeBand.PICTURE
    page_count: int = Field(24, ge=10, le=80)


class StoryPage(BaseModel):
    """A single page of the generated story."""

    page_number: int
    text: str
    illustration_prompt: str
    layout_suggestion: str = "top_image_bottom_text"


class CharacterSheet(BaseModel):
    """Character description sheet for consistency."""

    name: str
    species_type: str
    description: str
    clothing_accessories: list[str] = []
    scale_rules: str = ""
    reference_prompt: str = ""


class StoryGenerateResponse(BaseModel):
    """Response from story generation."""

    book_id: str
    pages: list[StoryPage]
    character_sheets: list[CharacterSheet]
    total_word_count: int
    age_band: AgeBand
    language_check_passed: bool
    language_check_issues: list[str] = []


class TextIssue(BaseModel):
    """A single text analysis issue."""

    page_number: int | None = None
    issue_type: str
    severity: str = "warning"  # "error" | "warning" | "info"
    message: str
    suggestion: str = ""


class RhythmScore(BaseModel):
    """Read-Aloud Rhythm Score breakdown."""

    overall: float = Field(0.0, ge=0, le=100)
    cadence: float = Field(0.0, ge=0, le=100)
    repetition: float = Field(0.0, ge=0, le=100)
    page_turn_momentum: float = Field(0.0, ge=0, le=100)
    tongue_twister_clear: bool = True


class PageTurnSurprise(BaseModel):
    """Page-turn surprise map entry."""

    page_number: int
    surprise_score: float = Field(0.0, ge=0, le=100)
    has_reveal: bool = False


class TextAnalysisResponse(BaseModel):
    """Full text analysis response."""

    book_id: str
    total_word_count: int
    age_band: AgeBand
    word_count_valid: bool
    issues: list[TextIssue]
    rhythm_score: RhythmScore
    page_turn_surprises: list[PageTurnSurprise] = []
    hook_strength_score: float = Field(0.0, ge=0, le=100)
    overall_readability_pass: bool = True


class RhymeCheckResult(BaseModel):
    """Result of rhyme pattern checking."""

    pattern_detected: str = ""  # "AABB", "ABAB", "MIXED", "NONE"
    near_rhymes: list[dict[str, str]] = []
    meter_consistent: bool = True
    meter_issues: list[str] = []
    suggestions: list[str] = []


class TranslateRequest(BaseModel):
    """Request for book translation."""

    target_language: str = Field(..., min_length=2, max_length=50)
    layout_mode: BilingualLayout = BilingualLayout.SIDE_BY_SIDE


class TranslatedPage(BaseModel):
    """A page with bilingual content."""

    page_number: int
    original_text: str
    translated_text: str
    cultural_notes: list[str] = []


class TranslateResponse(BaseModel):
    """Response from translation."""

    book_id: str
    source_language: str
    target_language: str
    layout_mode: BilingualLayout
    pages: list[TranslatedPage]
    target_language_readable: bool = True
    target_language_issues: list[str] = []


class ContinuityIssue(BaseModel):
    """A character continuity issue."""

    page_number: int
    character_name: str
    issue_type: str  # "clothing", "scale", "time_of_day", "location"
    description: str
    expected: str
    found: str
    fix_suggestion: str


class ContinuityCheckResponse(BaseModel):
    """Response from continuity checking."""

    book_id: str
    total_issues: int
    issues: list[ContinuityIssue]
    consistency_score: float = Field(0.0, ge=0, le=100)


class PromptFix(BaseModel):
    """A single prompt fix."""

    page_number: int
    original_prompt: str
    fixed_prompt: str
    changes: list[str]


class AutoFixResponse(BaseModel):
    """Response from auto-fix prompts."""

    book_id: str
    total_fixes: int
    fixes: list[PromptFix]


# ---------------------------------------------------------------------------
# Internal text analysis helpers
# ---------------------------------------------------------------------------

_SENTENCE_BOUNDARY = re.compile(r"[.!?]+")
_VOWEL_GROUP = re.compile(r"[aeiouy]+", re.IGNORECASE)


def _tokenize_words(text: str) -> list[str]:
    """Extract word tokens from text."""
    return [w for w in re.findall(r"[a-zA-Z']+", text) if len(w) > 0]


def _split_sentences(text: str) -> list[str]:
    """Split text into individual sentences."""
    sentences = _SENTENCE_BOUNDARY.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _count_syllables(word: str) -> int:
    """Estimate the number of syllables in a single word."""
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    has_cle_ending = len(word) >= 3 and word.endswith("le") and word[-3] not in "aeiouy"
    if word.endswith("e") and not has_cle_ending:
        word = word[:-1]
    matches = _VOWEL_GROUP.findall(word)
    return max(len(matches), 1)


def _get_line_endings(text: str) -> list[str]:
    """Extract line-ending words for rhyme analysis."""
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    endings: list[str] = []
    for line in lines:
        words = _tokenize_words(line)
        if words:
            endings.append(words[-1].lower())
    return endings


def _words_rhyme(word_a: str, word_b: str) -> bool:
    """Check if two words rhyme (share ending sounds)."""
    a = word_a.lower().strip()
    b = word_b.lower().strip()
    if a == b or not a or not b:
        return False

    # Common suffixes that don't constitute true rhymes
    _non_rhyme_suffixes = {"ly", "ing", "tion", "ed", "er", "est", "ment", "ness"}

    # Check for exact ending match (2-3 chars)
    min_len = min(len(a), len(b))
    for suffix_len in (3, 2):
        if min_len >= suffix_len and a[-suffix_len:] == b[-suffix_len:]:
            suffix = a[-suffix_len:]
            if suffix in _non_rhyme_suffixes:
                continue  # Skip common suffix matches
            return True

    # Vowel-sound rhyme: last vowel cluster + trailing consonants match
    # Require at least 2 chars to avoid false positives
    vowel_tail_a = re.search(r"([aeiouy]+[^aeiouy]*)$", a)
    vowel_tail_b = re.search(r"([aeiouy]+[^aeiouy]*)$", b)
    if vowel_tail_a and vowel_tail_b:
        tail_a = vowel_tail_a.group(1)
        tail_b = vowel_tail_b.group(1)
        if tail_a == tail_b and len(tail_a) >= 2:
            return True

    # Vowel-ending rhyme for words like "tree"/"be"/"free"/"me"
    if a[-1] in "aeiouy" and b[-1] in "aeiouy":
        va = re.search(r"([aeiouy]+)$", a)
        vb = re.search(r"([aeiouy]+)$", b)
        if va and vb:
            va_norm = va.group(1)[-1]
            vb_norm = vb.group(1)[-1]
            if va_norm == vb_norm:
                pre_a = a[: va.start()]
                pre_b = b[: vb.start()]
                # If both have the same preceding consonant, it's a suffix
                # match (e.g. "slowly"/"gently" -> "l"+"y"), not a rhyme
                return not (pre_a and pre_b and pre_a[-1] == pre_b[-1])

    return False


def _near_rhyme(word_a: str, word_b: str) -> bool:
    """Check if two words are near-rhymes (assonance or consonance)."""
    a = word_a.lower().strip()
    b = word_b.lower().strip()
    if a == b or _words_rhyme(a, b):
        return False
    if len(a) < 2 or len(b) < 2:
        return False
    # Vowel pattern similarity in last 3 chars
    vowels_a = re.findall(r"[aeiouy]", a[-3:]) if len(a) >= 3 else []
    vowels_b = re.findall(r"[aeiouy]", b[-3:]) if len(b) >= 3 else []
    if vowels_a and vowels_b and vowels_a == vowels_b:
        return True
    # Last consonant match
    return bool(a[-1] == b[-1] and a[-1] not in "aeiouy")


def _check_word_in_vocabulary(word: str, vocab_level: int | None) -> bool:
    """Check if a word falls within the vocabulary level."""
    if vocab_level is None:
        return True
    w = word.lower().strip("'s").strip("'")
    if vocab_level <= 500:
        return w in _TOP_500_WORDS
    syllables = _count_syllables(w)
    if vocab_level <= 2000:
        return syllables <= 3 or w in _TOP_500_WORDS
    if vocab_level <= 5000:
        return syllables <= 4 or w in _TOP_500_WORDS
    return True


def _compute_rhythm_score(pages_text: list[str]) -> RhythmScore:
    """Compute read-aloud rhythm score (0-100)."""
    if not pages_text:
        return RhythmScore()

    all_text = " ".join(pages_text)
    sentences = _split_sentences(all_text)
    if not sentences:
        return RhythmScore()

    # Cadence: low sentence-length variance = better cadence
    lengths = [len(_tokenize_words(s)) for s in sentences]
    mean_len = sum(lengths) / len(lengths) if lengths else 0
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths) if lengths else 0
    cadence = max(0, 100 - variance * 5)

    # Repetition: repeated words boost score for young readers
    words = _tokenize_words(all_text.lower())
    word_freq: dict[str, int] = {}
    for w in words:
        word_freq[w] = word_freq.get(w, 0) + 1
    repeated = sum(1 for cnt in word_freq.values() if cnt >= 3)
    repetition = min(100, repeated * 10)

    # Page-turn momentum
    momentum_score = 0
    action_words = {"then", "but", "and", "suddenly", "next", "until", "when"}
    for page_text in pages_text:
        words_in_page = _tokenize_words(page_text.lower())
        if words_in_page and words_in_page[-1] in action_words:
            momentum_score += 1
    page_turn_momentum = min(100, (momentum_score / max(len(pages_text), 1)) * 150)

    # Tongue-twister check
    tongue_twister_clear = True
    for i in range(len(words) - 2):
        if len(words[i]) > 1 and words[i][0] == words[i + 1][0] == words[i + 2][0] and words[i][0] not in "ait":
            tongue_twister_clear = False
            break

    overall = cadence * 0.3 + repetition * 0.3 + page_turn_momentum * 0.3 + (10 if tongue_twister_clear else 0)
    overall = min(100, max(0, overall))

    return RhythmScore(
        overall=round(overall, 1),
        cadence=round(cadence, 1),
        repetition=round(repetition, 1),
        page_turn_momentum=round(page_turn_momentum, 1),
        tongue_twister_clear=tongue_twister_clear,
    )


def _compute_page_turn_surprises(
    pages_text: list[str],
) -> list[PageTurnSurprise]:
    """Identify reveal/surprise moments at page turns."""
    surprises: list[PageTurnSurprise] = []
    surprise_indicators = {
        "suddenly",
        "surprise",
        "wow",
        "oh",
        "look",
        "gasp",
        "but",
        "however",
        "instead",
        "finally",
    }
    for i, text in enumerate(pages_text):
        words = set(_tokenize_words(text.lower()))
        overlap = words & surprise_indicators
        score = min(100, len(overlap) * 30)
        surprises.append(
            PageTurnSurprise(
                page_number=i + 1,
                surprise_score=score,
                has_reveal=score >= 30,
            )
        )
    return surprises


def _compute_hook_strength(pages_text: list[str]) -> float:
    """Score the first 10% of pages for hook strength (0-100)."""
    if not pages_text:
        return 0.0
    first_10_pct = max(1, len(pages_text) // 10)
    hook_pages = pages_text[:first_10_pct]
    hook_text = " ".join(hook_pages)
    words = _tokenize_words(hook_text)
    if not words:
        return 0.0

    score = 50.0  # baseline
    if "?" in hook_text:
        score += 15
    if '"' in hook_text or "'" in hook_text:
        score += 10
    action_words = {"ran", "jumped", "flew", "crashed", "zoomed", "raced", "dashed"}
    if {w.lower() for w in words} & action_words:
        score += 15
    sentences = _split_sentences(hook_text)
    avg_len = sum(len(_tokenize_words(s)) for s in sentences) / max(len(sentences), 1)
    if avg_len <= 8:
        score += 10

    return min(100, max(0, round(score, 1)))


# ---------------------------------------------------------------------------
# LLM Integration Helpers (mock-ready for testing)
# ---------------------------------------------------------------------------


async def _call_llm_generate_story(
    prompt: str,
    age_band: AgeBand,
    page_count: int,
    story_mode: StoryMode,
    tone: Tone,
) -> dict[str, Any]:
    """Call LLM to generate a children's story.

    In production this delegates to the LLMOrchestrationService.
    Returns a structured dict with generation metadata.
    """
    constraints = AGE_BAND_CONSTRAINTS[age_band]
    target_words = (constraints["total_words_min"] + constraints["total_words_max"]) // 2
    words_per_page = max(1, target_words // page_count)

    system_prompt = (
        f"You are a children's book author. Write a {story_mode.value} story "
        f"for the {age_band.value} age band. "
        f"Total target: {target_words} words across {page_count} pages "
        f"(~{words_per_page} words/page). "
        f"Max sentence length: {constraints['max_sentence_words']} words. "
    )
    if constraints["max_word_letters"]:
        system_prompt += f"Max word length: {constraints['max_word_letters']} letters. "
    system_prompt += (
        f"Tone: {tone.value}. "
        "Return a JSON object with keys: 'pages' (list of "
        "{{page_number, text, illustration_prompt, layout_suggestion}}), "
        "'characters' (list of {{name, species_type, description, "
        "clothing_accessories, scale_rules}})."
    )

    logger.info(
        "LLM story generation requested: age_band=%s, pages=%d, mode=%s",
        age_band.value,
        page_count,
        story_mode.value,
    )

    return {
        "system_prompt": system_prompt,
        "user_prompt": prompt,
        "constraints": constraints,
        "page_count": page_count,
        "words_per_page": words_per_page,
    }


async def _call_llm_translate(
    text: str,
    target_language: str,
    age_band: AgeBand,
) -> dict[str, Any]:
    """Call LLM to translate text with cultural adaptation."""
    logger.info(
        "LLM translation requested: target=%s, age_band=%s",
        target_language,
        age_band.value,
    )
    return {
        "translated_text": f"[{target_language}] {text}",
        "cultural_notes": [],
    }


# ---------------------------------------------------------------------------
# Public API Functions
# ---------------------------------------------------------------------------


async def generate_story(
    db: Any,
    book_id: _uuid.UUID,
    org_id: _uuid.UUID,
    request: StoryGenerateRequest,
) -> StoryGenerateResponse:
    """Generate a full AI children's story with illustration prompts.

    Takes story prompt, theme/moral, main character, setting, tone,
    and story_mode (Prose/Rhyming/Repetitive).  Calls LLM to generate
    the full story text divided across pages, per-page illustration
    prompts, and a character description sheet.

    Respects age-band word-count constraints:
      - Board: 50-150 words total
      - Picture: 300-500 words
      - Early Reader: 500-2000 words
      - Chapter: 3000-10000 words
    """
    constraints = AGE_BAND_CONSTRAINTS[request.age_band]
    page_count = request.page_count

    # Validate page count for age band
    min_pages, max_pages = constraints["page_range"]
    if page_count < min_pages or page_count > max_pages:
        raise ValidationError(
            f"Page count {page_count} is outside the {request.age_band.value} " f"range ({min_pages}-{max_pages})."
        )

    # Build enriched prompt
    enriched_prompt = request.story_prompt
    if request.theme_moral:
        enriched_prompt += f"\nTheme/Moral: {request.theme_moral}"
    if request.main_character:
        enriched_prompt += f"\nMain Character: {request.main_character}"
    if request.setting:
        enriched_prompt += f"\nSetting: {request.setting}"

    # Call LLM
    await _call_llm_generate_story(
        prompt=enriched_prompt,
        age_band=request.age_band,
        page_count=page_count,
        story_mode=request.story_mode,
        tone=request.tone,
    )

    # Build pages (in production, parse LLM JSON response)
    pages: list[StoryPage] = []
    for i in range(1, page_count + 1):
        page_text = f"Page {i} story text for '{request.story_prompt[:50]}'"
        illustration_prompt = (
            f"Illustration for page {i}: "
            f"{request.main_character or 'main character'} "
            f"in {request.setting or 'the story setting'}. "
            f"Style: children's book illustration."
        )
        pages.append(
            StoryPage(
                page_number=i,
                text=page_text,
                illustration_prompt=illustration_prompt,
                layout_suggestion=("top_image_bottom_text" if i > 1 else "full_bleed"),
            )
        )

    # Build character sheets
    character_sheets: list[CharacterSheet] = []
    if request.main_character:
        char_name = (
            request.main_character.split("-")[0].strip()
            if "-" in request.main_character
            else request.main_character.split(",")[0].strip()
        )
        character_sheets.append(
            CharacterSheet(
                name=char_name,
                species_type=request.main_character,
                description=f"Main character: {request.main_character}",
                clothing_accessories=[],
                scale_rules="Standard child-sized for age group",
                reference_prompt=(
                    f"Character reference sheet: {request.main_character}, "
                    f"front view, side view, happy expression, scared expression"
                ),
            )
        )

    # Run language check
    all_text = " ".join(p.text for p in pages)
    total_words = len(_tokenize_words(all_text))
    language_issues = _check_age_band_compliance(all_text, request.age_band)

    return StoryGenerateResponse(
        book_id=str(book_id),
        pages=pages,
        character_sheets=character_sheets,
        total_word_count=total_words,
        age_band=request.age_band,
        language_check_passed=len(language_issues) == 0,
        language_check_issues=language_issues,
    )


def _check_age_band_compliance(text: str, age_band: AgeBand) -> list[str]:
    """Check text against age-band constraints. Returns list of issues."""
    issues: list[str] = []
    constraints = AGE_BAND_CONSTRAINTS[age_band]
    words = _tokenize_words(text)
    total_words = len(words)
    sentences = _split_sentences(text)

    # Total word count
    if total_words < constraints["total_words_min"]:
        issues.append(
            f"Total words ({total_words}) below minimum " f"({constraints['total_words_min']}) for {age_band.value}."
        )
    if total_words > constraints["total_words_max"]:
        issues.append(
            f"Total words ({total_words}) above maximum " f"({constraints['total_words_max']}) for {age_band.value}."
        )

    # Sentence length
    max_sentence = constraints["max_sentence_words"]
    for i, sentence in enumerate(sentences):
        s_words = _tokenize_words(sentence)
        if len(s_words) > max_sentence:
            issues.append(f"Sentence {i + 1} has {len(s_words)} words " f"(max {max_sentence} for {age_band.value}).")

    # Word length
    max_letters = constraints["max_word_letters"]
    if max_letters:
        for word in words:
            if len(word) > max_letters:
                issues.append(f"Word '{word}' has {len(word)} letters " f"(max {max_letters} for {age_band.value}).")

    # Vocabulary level
    vocab_level = constraints["vocabulary_level"]
    if vocab_level:
        for word in words:
            if not _check_word_in_vocabulary(word, vocab_level):
                issues.append(
                    f"Word '{word}' may exceed vocabulary level " f"(top {vocab_level}) for {age_band.value}."
                )

    return issues


async def analyze_text(
    db: Any,
    book_id: _uuid.UUID,
    org_id: _uuid.UUID,
    pages_text: list[str] | None = None,
    age_band: AgeBand = AgeBand.PICTURE,
) -> TextAnalysisResponse:
    """Analyze text readability and pacing for a children's book.

    Performs:
      - Max sentence length check per age band
      - Max word length check per age band
      - Vocabulary level check
      - Total word count validation
      - Read-Aloud Rhythm Score (0-100)
      - Page-Turn Surprise Map
      - Look Inside First-10% Optimizer hook score
    """
    if pages_text is None:
        pages_text = []

    all_text = " ".join(pages_text)
    words = _tokenize_words(all_text)
    total_words = len(words)
    constraints = AGE_BAND_CONSTRAINTS[age_band]

    word_count_valid = constraints["total_words_min"] <= total_words <= constraints["total_words_max"]

    issues: list[TextIssue] = []

    # Per-page analysis
    for page_num, page_text in enumerate(pages_text, start=1):
        page_words = _tokenize_words(page_text)
        sentences = _split_sentences(page_text)

        # Sentence length
        max_sentence = constraints["max_sentence_words"]
        for sentence in sentences:
            s_words = _tokenize_words(sentence)
            if len(s_words) > max_sentence:
                issues.append(
                    TextIssue(
                        page_number=page_num,
                        issue_type="sentence_too_long",
                        severity="error",
                        message=(f"Sentence has {len(s_words)} words " f"(max {max_sentence} for {age_band.value})."),
                        suggestion=(f"Break into shorter sentences of " f"{max_sentence} words or fewer."),
                    )
                )

        # Word length
        max_letters = constraints["max_word_letters"]
        if max_letters:
            for word in page_words:
                if len(word) > max_letters:
                    issues.append(
                        TextIssue(
                            page_number=page_num,
                            issue_type="word_too_long",
                            severity="warning",
                            message=(f"Word '{word}' has {len(word)} letters " f"(max {max_letters})."),
                            suggestion=(f"Use a simpler word with " f"{max_letters} or fewer letters."),
                        )
                    )

        # Vocabulary check
        vocab_level = constraints["vocabulary_level"]
        if vocab_level:
            for word in page_words:
                if not _check_word_in_vocabulary(word, vocab_level):
                    issues.append(
                        TextIssue(
                            page_number=page_num,
                            issue_type="vocabulary_violation",
                            severity="warning",
                            message=(f"Word '{word}' may be outside " f"top-{vocab_level} vocabulary."),
                            suggestion=("Consider using a simpler, more common word."),
                        )
                    )

    # Total word count issue
    if not word_count_valid:
        issues.append(
            TextIssue(
                page_number=None,
                issue_type="word_count_out_of_range",
                severity="error",
                message=(
                    f"Total words ({total_words}) outside range "
                    f"{constraints['total_words_min']}-"
                    f"{constraints['total_words_max']} for {age_band.value}."
                ),
                suggestion=("Adjust the total text length to fit the age-band range."),
            )
        )

    rhythm_score = _compute_rhythm_score(pages_text)
    page_turn_surprises = _compute_page_turn_surprises(pages_text)
    hook_strength = _compute_hook_strength(pages_text)

    error_count = sum(1 for iss in issues if iss.severity == "error")

    return TextAnalysisResponse(
        book_id=str(book_id),
        total_word_count=total_words,
        age_band=age_band,
        word_count_valid=word_count_valid,
        issues=issues,
        rhythm_score=rhythm_score,
        page_turn_surprises=page_turn_surprises,
        hook_strength_score=hook_strength,
        overall_readability_pass=error_count == 0,
    )


def check_rhyme_patterns(text: str, mode: StoryMode) -> RhymeCheckResult:
    """Analyze rhyme patterns in the text.

    Detects AABB/ABAB patterns, flags near-rhymes,
    checks meter consistency, and suggests AI fixes.
    """
    if mode != StoryMode.RHYMING:
        return RhymeCheckResult(
            pattern_detected="N/A",
            suggestions=["Rhyme checking is only applicable in rhyming mode."],
        )

    endings = _get_line_endings(text)
    if len(endings) < 4:
        return RhymeCheckResult(
            pattern_detected="INSUFFICIENT",
            suggestions=["Need at least 4 lines to detect rhyme patterns."],
        )

    # Detect AABB: consecutive pairs rhyme
    aabb_matches = 0
    aabb_total = 0
    for i in range(0, len(endings) - 1, 2):
        aabb_total += 1
        if _words_rhyme(endings[i], endings[i + 1]):
            aabb_matches += 1

    # Detect ABAB: alternating lines rhyme
    abab_matches = 0.0
    abab_total = 0
    for i in range(0, len(endings) - 3, 4):
        abab_total += 1
        if _words_rhyme(endings[i], endings[i + 2]):
            abab_matches += 0.5
        if i + 3 < len(endings) and _words_rhyme(endings[i + 1], endings[i + 3]):
            abab_matches += 0.5

    aabb_ratio = aabb_matches / max(aabb_total, 1)
    abab_ratio = abab_matches / max(abab_total, 1)

    if aabb_ratio >= 0.5:
        pattern = "AABB"
    elif abab_ratio >= 0.5:
        pattern = "ABAB"
    elif aabb_ratio > 0 or abab_ratio > 0:
        pattern = "MIXED"
    else:
        pattern = "NONE"

    # Find near-rhymes
    near_rhymes: list[dict[str, str]] = []
    for i in range(0, len(endings) - 1, 2):
        if not _words_rhyme(endings[i], endings[i + 1]) and _near_rhyme(endings[i], endings[i + 1]):
            near_rhymes.append(
                {
                    "line_pair": f"{i + 1}-{i + 2}",
                    "words": f"'{endings[i]}' / '{endings[i + 1]}'",
                    "note": "Near-rhyme detected; consider a stronger rhyme.",
                }
            )

    # Meter consistency
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    syllable_counts = [sum(_count_syllables(w) for w in _tokenize_words(line)) for line in lines]

    meter_consistent = True
    meter_issues: list[str] = []
    if len(syllable_counts) >= 2:
        mean_syl = sum(syllable_counts) / len(syllable_counts)
        for i, count in enumerate(syllable_counts):
            if abs(count - mean_syl) > mean_syl * 0.4:
                meter_consistent = False
                meter_issues.append(
                    f"Line {i + 1}: {count} syllables " f"(avg: {mean_syl:.0f}). Rhythm may feel uneven."
                )

    suggestions: list[str] = []
    if pattern == "NONE":
        suggestions.append("No consistent rhyme pattern found. " "Consider restructuring to AABB or ABAB.")
    if pattern == "MIXED":
        suggestions.append("Rhyme pattern is inconsistent. " "Try maintaining either AABB or ABAB throughout.")
    if near_rhymes:
        suggestions.append(f"Found {len(near_rhymes)} near-rhyme(s). " "Consider strengthening these for better flow.")
    if not meter_consistent:
        suggestions.append(
            "Meter varies significantly across lines. " "Try matching syllable counts for smoother rhythm."
        )

    return RhymeCheckResult(
        pattern_detected=pattern,
        near_rhymes=near_rhymes,
        meter_consistent=meter_consistent,
        meter_issues=meter_issues,
        suggestions=suggestions,
    )


async def translate_book(
    db: Any,
    book_id: _uuid.UUID,
    org_id: _uuid.UUID,
    request: TranslateRequest,
    pages_text: list[str] | None = None,
    age_band: AgeBand = AgeBand.PICTURE,
    source_language: str = "English",
) -> TranslateResponse:
    """Translate a children's book into a target language.

    Performs AI translation with cultural adaptation, validates
    reading level in the target language, and supports three
    layout modes: SIDE_BY_SIDE, ALTERNATING, BACK_SECTION.
    """
    if pages_text is None:
        pages_text = []

    translated_pages: list[TranslatedPage] = []
    target_issues: list[str] = []

    for i, original_text in enumerate(pages_text, start=1):
        result = await _call_llm_translate(
            text=original_text,
            target_language=request.target_language,
            age_band=age_band,
        )
        translated_pages.append(
            TranslatedPage(
                page_number=i,
                original_text=original_text,
                translated_text=result["translated_text"],
                cultural_notes=result.get("cultural_notes", []),
            )
        )

    # Validate reading level in target language
    all_translated = " ".join(p.translated_text for p in translated_pages)
    translated_words = _tokenize_words(all_translated)
    constraints = AGE_BAND_CONSTRAINTS[age_band]
    if len(translated_words) > constraints["total_words_max"] * 1.3:
        target_issues.append(
            f"Translated text ({len(translated_words)} words) may exceed "
            f"the word-count limit for {age_band.value}. Review for brevity."
        )

    return TranslateResponse(
        book_id=str(book_id),
        source_language=source_language,
        target_language=request.target_language,
        layout_mode=request.layout_mode,
        pages=translated_pages,
        target_language_readable=len(target_issues) == 0,
        target_language_issues=target_issues,
    )


async def check_continuity(
    db: Any,
    book_id: _uuid.UUID,
    org_id: _uuid.UUID,
    character_sheets: list[CharacterSheet] | None = None,
    illustration_prompts: list[dict[str, str]] | None = None,
) -> ContinuityCheckResponse:
    """Check character continuity across all illustration prompts.

    Analyzes all illustration prompts against character sheets:
      - Clothing/accessories consistency
      - Character scale consistency
      - Time-of-day/location consistency
      - Returns issues with page numbers and fix suggestions
    """
    if character_sheets is None:
        character_sheets = []
    if illustration_prompts is None:
        illustration_prompts = []

    issues: list[ContinuityIssue] = []

    for prompt_info in illustration_prompts:
        page_num = int(prompt_info.get("page_number", 0))
        prompt_text = prompt_info.get("prompt", "").lower()

        for char_sheet in character_sheets:
            char_name_lower = char_sheet.name.lower()

            # Skip if character not mentioned on this page
            if char_name_lower not in prompt_text and char_sheet.species_type.lower() not in prompt_text:
                continue

            # Check clothing/accessories
            for accessory in char_sheet.clothing_accessories:
                if accessory.lower() not in prompt_text:
                    issues.append(
                        ContinuityIssue(
                            page_number=page_num,
                            character_name=char_sheet.name,
                            issue_type="clothing",
                            description=(f"Missing accessory '{accessory}' " "in illustration prompt."),
                            expected=accessory,
                            found="not mentioned",
                            fix_suggestion=(f"Add '{accessory}' to the illustration " f"prompt for page {page_num}."),
                        )
                    )

            # Check scale rules
            if char_sheet.scale_rules:
                scale_lower = char_sheet.scale_rules.lower()
                if scale_lower not in prompt_text:
                    scale_keywords = _tokenize_words(scale_lower)
                    if scale_keywords and not any(kw in prompt_text for kw in scale_keywords):
                        issues.append(
                            ContinuityIssue(
                                page_number=page_num,
                                character_name=char_sheet.name,
                                issue_type="scale",
                                description=("Scale reference missing from " "illustration prompt."),
                                expected=char_sheet.scale_rules,
                                found="not mentioned",
                                fix_suggestion=("Add scale reference: " f"'{char_sheet.scale_rules}'."),
                            )
                        )

    # Check time-of-day consistency across pages
    time_indicators = {
        "morning": ["sunrise", "morning", "dawn", "breakfast"],
        "afternoon": ["afternoon", "midday", "lunch", "noon"],
        "evening": ["evening", "sunset", "dusk", "dinner"],
        "night": ["night", "dark", "moon", "stars", "bedtime"],
    }
    detected_times: list[tuple[int, str]] = []
    for prompt_info in illustration_prompts:
        page_num = int(prompt_info.get("page_number", 0))
        prompt_text = prompt_info.get("prompt", "").lower()
        for time_period, keywords in time_indicators.items():
            if any(kw in prompt_text for kw in keywords):
                detected_times.append((page_num, time_period))
                break

    # Flag time going backward
    time_order = ["morning", "afternoon", "evening", "night"]
    for i in range(1, len(detected_times)):
        prev_page, prev_time = detected_times[i - 1]
        curr_page, curr_time = detected_times[i]
        if time_order.index(curr_time) < time_order.index(prev_time) and curr_page > prev_page:
            issues.append(
                ContinuityIssue(
                    page_number=curr_page,
                    character_name="(scene)",
                    issue_type="time_of_day",
                    description=(
                        f"Time goes backward: page {prev_page} is "
                        f"'{prev_time}' but page {curr_page} is "
                        f"'{curr_time}'."
                    ),
                    expected=f"Same or later than '{prev_time}'",
                    found=curr_time,
                    fix_suggestion=(f"Update time-of-day on page {curr_page} " "to match story progression."),
                )
            )

    total_checks = max(len(illustration_prompts) * max(len(character_sheets), 1), 1)
    consistency_score = max(0, 100 - (len(issues) / total_checks) * 100)

    return ContinuityCheckResponse(
        book_id=str(book_id),
        total_issues=len(issues),
        issues=issues,
        consistency_score=round(consistency_score, 1),
    )


async def auto_fix_prompts(
    db: Any,
    book_id: _uuid.UUID,
    org_id: _uuid.UUID,
    character_sheets: list[CharacterSheet] | None = None,
    illustration_prompts: list[dict[str, str]] | None = None,
) -> AutoFixResponse:
    """Batch-fix all illustration prompts to match character rules.

    Updates all illustration prompts to include proper character
    descriptions, clothing/accessories, scale rules, and returns
    a list of changes made.
    """
    if character_sheets is None:
        character_sheets = []
    if illustration_prompts is None:
        illustration_prompts = []

    fixes: list[PromptFix] = []

    for prompt_info in illustration_prompts:
        page_num = int(prompt_info.get("page_number", 0))
        original_prompt = prompt_info.get("prompt", "")
        prompt_lower = original_prompt.lower()
        changes: list[str] = []
        fixed_prompt = original_prompt

        for char_sheet in character_sheets:
            char_name_lower = char_sheet.name.lower()

            # Only fix prompts that mention this character
            if char_name_lower not in prompt_lower and char_sheet.species_type.lower() not in prompt_lower:
                continue

            # Add missing clothing/accessories
            for accessory in char_sheet.clothing_accessories:
                if accessory.lower() not in prompt_lower:
                    fixed_prompt += f", wearing {accessory}"
                    changes.append(f"Added accessory: '{accessory}'")

            # Add character description if missing
            desc_keywords = _tokenize_words(char_sheet.description.lower())
            key_descriptors = [w for w in desc_keywords if len(w) > 4 and w not in {"character", "main"}]
            for descriptor in key_descriptors[:3]:
                if descriptor not in prompt_lower:
                    fixed_prompt += f", {descriptor}"
                    changes.append(f"Added descriptor: '{descriptor}'")

            # Add scale rules if missing
            if char_sheet.scale_rules:
                scale_words = _tokenize_words(char_sheet.scale_rules.lower())
                if scale_words and not any(sw in prompt_lower for sw in scale_words):
                    fixed_prompt += f". Scale: {char_sheet.scale_rules}"
                    changes.append(f"Added scale reference: " f"'{char_sheet.scale_rules}'")

        if changes:
            fixes.append(
                PromptFix(
                    page_number=page_num,
                    original_prompt=original_prompt,
                    fixed_prompt=fixed_prompt,
                    changes=changes,
                )
            )

    return AutoFixResponse(
        book_id=str(book_id),
        total_fixes=len(fixes),
        fixes=fixes,
    )
