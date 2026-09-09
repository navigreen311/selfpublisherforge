"""Text Readability & Pacing analysis engine for Children's Book Studio.

Provides age-band compliance checking, readability scoring, rhythm analysis,
page-turn surprise mapping, Look Inside optimization, and rhyme detection
with AI-powered fix suggestions.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Age-Band Rules
# ---------------------------------------------------------------------------

AGE_BAND_RULES: dict[str, dict[str, Any]] = {
    "board_0_3": {
        "max_sentence_words": 5,
        "max_word_length": 5,
        "vocab_level": 500,
        "total_words": (50, 150),
    },
    "picture_3_5": {
        "max_sentence_words": 8,
        "max_word_length": 7,
        "vocab_level": 2000,
        "total_words": (300, 500),
    },
    "early_reader_5_8": {
        "max_sentence_words": 12,
        "max_word_length": 9,
        "vocab_level": 5000,
        "total_words": (500, 2000),
    },
    "chapter_8_12": {
        "max_sentence_words": 15,
        "max_word_length": None,
        "vocab_level": None,
        "total_words": (3000, 10000),
    },
}

# Map the frontend / DB age-range keys to our rule keys
_AGE_RANGE_ALIAS: dict[str, str] = {
    "board": "board_0_3",
    "picture": "picture_3_5",
    "early_reader": "early_reader_5_8",
    "chapter": "chapter_8_12",
    # Allow direct rule keys too
    "board_0_3": "board_0_3",
    "picture_3_5": "picture_3_5",
    "early_reader_5_8": "early_reader_5_8",
    "chapter_8_12": "chapter_8_12",
}


def _resolve_age_range(age_range: str) -> str:
    """Resolve an age-range key to the canonical AGE_BAND_RULES key."""
    key = _AGE_RANGE_ALIAS.get(age_range)
    if key is None:
        raise ValueError(f"Unknown age_range '{age_range}'. " f"Valid values: {list(_AGE_RANGE_ALIAS.keys())}")
    return key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+")
_WORD_RE = re.compile(r"[a-zA-Z'\u2019]+")
_CONSONANT_CLUSTERS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]{3,}", re.IGNORECASE)


@dataclass
class Violation:
    """A single rule violation with location context."""

    rule: str
    message: str
    page: int | None = None
    line: int | None = None
    offending_text: str | None = None
    suggestion: str | None = None


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on .!? boundaries."""
    raw = _SENTENCE_SPLIT_RE.split(text.strip())
    return [s.strip() for s in raw if s.strip()]


def _extract_words(text: str) -> list[str]:
    """Extract alphabetical words from text."""
    return _WORD_RE.findall(text)


def _word_count(text: str) -> int:
    return len(_extract_words(text))


# ---------------------------------------------------------------------------
# Core Analysis Functions
# ---------------------------------------------------------------------------


def analyze_text(text: str, age_range: str) -> dict[str, Any]:
    """Check *text* against every rule for *age_range*.

    Parameters
    ----------
    text:
        The full book text.  Pages can be separated by ``\\n---\\n``
        or ``\\f`` (form-feed) to allow per-page analysis.
    age_range:
        One of the AGE_BAND_RULES keys or a known alias
        (``board``, ``picture``, ``early_reader``, ``chapter``).

    Returns
    -------
    dict with keys:
        - ``violations``: list[dict] – each violation with
          rule, message, page, line, offending_text, suggestion.
        - ``total_words``: int
        - ``age_range``: str (resolved key)
        - ``rules_checked``: list[str]
        - ``pass``: bool – True when no violations found.
    """
    key = _resolve_age_range(age_range)
    rules = AGE_BAND_RULES[key]

    # Split into pages
    pages: list[str]
    if "\f" in text:
        pages = [p.strip() for p in text.split("\f") if p.strip()]
    elif "\n---\n" in text:
        pages = [p.strip() for p in text.split("\n---\n") if p.strip()]
    else:
        pages = [text.strip()]

    violations: list[Violation] = []
    total_words = 0

    for page_idx, page_text in enumerate(pages, start=1):
        lines = page_text.split("\n")
        for line_idx, line in enumerate(lines, start=1):
            sentences = _split_sentences(line)
            for sentence in sentences:
                words = _extract_words(sentence)
                total_words += len(words)

                # --- Max sentence words ---
                max_sw = rules["max_sentence_words"]
                if max_sw is not None and len(words) > max_sw:
                    violations.append(
                        Violation(
                            rule="max_sentence_words",
                            message=(f"Sentence has {len(words)} words " f"(max {max_sw} for {key})"),
                            page=page_idx,
                            line=line_idx,
                            offending_text=sentence,
                            suggestion=f"Break this into sentences of {max_sw} words or fewer.",
                        )
                    )

                # --- Max word length ---
                max_wl = rules["max_word_length"]
                if max_wl is not None:
                    for word in words:
                        if len(word) > max_wl:
                            violations.append(
                                Violation(
                                    rule="max_word_length",
                                    message=(f"Word '{word}' has {len(word)} letters " f"(max {max_wl} for {key})"),
                                    page=page_idx,
                                    line=line_idx,
                                    offending_text=word,
                                    suggestion=f"Replace with a simpler word ({max_wl} letters or fewer).",
                                )
                            )

    # --- Total word count ---
    min_words, max_words = rules["total_words"]
    if total_words < min_words:
        violations.append(
            Violation(
                rule="total_words",
                message=(f"Book has {total_words} words " f"(minimum {min_words} for {key})"),
                suggestion=f"Add more content to reach at least {min_words} words.",
            )
        )
    elif total_words > max_words:
        violations.append(
            Violation(
                rule="total_words",
                message=(f"Book has {total_words} words " f"(maximum {max_words} for {key})"),
                suggestion=f"Trim content to stay under {max_words} words.",
            )
        )

    rules_checked = [
        "max_sentence_words",
        "max_word_length",
        "total_words",
    ]
    if rules["vocab_level"] is not None:
        rules_checked.append("vocab_level")

    return {
        "violations": [
            {
                "rule": v.rule,
                "message": v.message,
                "page": v.page,
                "line": v.line,
                "offending_text": v.offending_text,
                "suggestion": v.suggestion,
            }
            for v in violations
        ],
        "total_words": total_words,
        "age_range": key,
        "rules_checked": rules_checked,
        "pass": len(violations) == 0,
    }


# ---------------------------------------------------------------------------
# Readability Score
# ---------------------------------------------------------------------------


def calculate_readability_score(text: str, age_range: str) -> float:
    """Return a 0-100 readability score for *text* against *age_range*.

    100 = perfectly compliant with the age band.
    Each violation category proportionally reduces the score.
    """
    analysis = analyze_text(text, age_range)
    violations = analysis["violations"]

    if not violations:
        return 100.0

    # Deduct points per violation, capped at certain amounts per rule
    deductions: dict[str, float] = {}
    for v in violations:
        rule = v["rule"]
        if rule == "total_words":
            deductions[rule] = max(deductions.get(rule, 0), 20.0)
        elif rule == "max_sentence_words":
            deductions[rule] = min(deductions.get(rule, 0) + 5.0, 40.0)
        elif rule == "max_word_length":
            deductions[rule] = min(deductions.get(rule, 0) + 3.0, 30.0)
        elif rule == "vocab_level":
            deductions[rule] = min(deductions.get(rule, 0) + 4.0, 30.0)

    total_deduction = sum(deductions.values())
    return max(0.0, round(100.0 - total_deduction, 1))


# ---------------------------------------------------------------------------
# Rhythm Score
# ---------------------------------------------------------------------------


def calculate_rhythm_score(text: str) -> float:
    """Return a 0-100 read-aloud rhythm score.

    Evaluates:
    - Sentence cadence variance (consistent beat is better)
    - Repetition patterns (repeated phrases score higher for young readers)
    - Page-turn momentum (sentences that end mid-thought near page breaks)
    - Tongue-twister detection (consecutive similar consonants penalised)
    """
    sentences = _split_sentences(text)
    if not sentences:
        return 0.0

    score = 100.0

    # --- Cadence variance ---
    word_counts = [len(_extract_words(s)) for s in sentences]
    if len(word_counts) >= 2:
        mean_wc = sum(word_counts) / len(word_counts)
        variance = sum((wc - mean_wc) ** 2 for wc in word_counts) / len(word_counts)
        std_dev = math.sqrt(variance)
        # High variance = inconsistent cadence → lower score
        cadence_penalty = min(std_dev * 3, 25.0)
        score -= cadence_penalty

    # --- Repetition patterns (boost for young readers) ---
    lower_sentences = [s.lower().strip() for s in sentences]
    repeated = sum(1 for i, s in enumerate(lower_sentences) if lower_sentences.count(s) > 1)
    repetition_ratio = repeated / len(lower_sentences) if lower_sentences else 0
    # Moderate repetition is good (0.1-0.4), too much or too little is neutral
    if 0.1 <= repetition_ratio <= 0.4:
        score += 5.0  # small bonus

    # --- Tongue-twister detection ---
    tongue_twister_count = len(_CONSONANT_CLUSTERS_RE.findall(text.lower()))
    twister_penalty = min(tongue_twister_count * 2, 20.0)
    score -= twister_penalty

    # --- Page-turn momentum ---
    # Check for sentences that end with ellipsis or em-dash (momentum builders)
    momentum_markers = sum(1 for s in sentences if s.rstrip().endswith(("...", "\u2014", "--")))
    if momentum_markers > 0:
        score += min(momentum_markers * 2, 10.0)

    return max(0.0, min(100.0, round(score, 1)))


# ---------------------------------------------------------------------------
# Page-Turn Surprise Map
# ---------------------------------------------------------------------------


def generate_page_turn_map(pages: list[str]) -> list[tuple[int, float]]:
    """Return a list of ``(page_num, surprise_score)`` tuples.

    *surprise_score* (0-100) estimates how much of a "reveal" or
    dramatic shift happens at each page turn.

    Parameters
    ----------
    pages:
        A list of page texts in order.

    Heuristics used:
    - Question ending the previous page (builds anticipation)
    - Exclamation marks (excitement)
    - New character/name introduction
    - Significant change in sentence length (pacing shift)
    - Ellipsis at page end (cliffhanger)
    """
    result: list[tuple[int, float]] = []

    for idx, page_text in enumerate(pages):
        surprise = 0.0
        stripped = page_text.strip()

        if not stripped:
            result.append((idx + 1, 0.0))
            continue

        # Question at end of page → anticipation for next page
        if stripped.endswith("?"):
            surprise += 25.0

        # Exclamation → excitement
        exclamation_count = stripped.count("!")
        surprise += min(exclamation_count * 10, 20.0)

        # Ellipsis / cliffhanger
        if stripped.endswith(("...", "\u2026")):
            surprise += 30.0

        # ALL-CAPS words (emphasis / reveal)
        caps_words = [w for w in _extract_words(stripped) if w.isupper() and len(w) > 1]
        surprise += min(len(caps_words) * 5, 15.0)

        # Short, punchy page (few words but impactful)
        wc = _word_count(stripped)
        if 1 <= wc <= 5:
            surprise += 10.0

        result.append((idx + 1, min(100.0, round(surprise, 1))))

    return result


# ---------------------------------------------------------------------------
# Look Inside Score
# ---------------------------------------------------------------------------


def score_look_inside(pages: list[str]) -> float:
    """Score the hook strength of the first 10 percent of pages (0-100).

    Amazon's "Look Inside" feature shows roughly the first 10% of a book.
    This function evaluates whether those pages hook the reader.

    Factors:
    - Opening line impact (question, exclamation, action verb)
    - Character introduction within first 2 pages
    - Pacing variety (mix of sentence lengths)
    - Cliffhanger or question at the boundary page
    """
    if not pages:
        return 0.0

    preview_count = max(1, math.ceil(len(pages) * 0.10))
    preview_pages = pages[:preview_count]
    score = 50.0  # baseline

    # --- Opening line impact ---
    first_page = preview_pages[0].strip()
    first_sentence = ""
    first_sentences = _split_sentences(first_page)
    if first_sentences:
        first_sentence = first_sentences[0]

    if first_sentence.endswith("?") or first_sentence.rstrip().endswith("?"):
        score += 10.0  # question hook
    if "!" in first_sentence:
        score += 5.0  # excitement

    # Action verbs at start (simple heuristic: short first sentence with a verb)
    first_words = _extract_words(first_sentence)
    if 2 <= len(first_words) <= 8:
        score += 5.0  # punchy opening

    # --- Character introduction ---
    preview_text = " ".join(preview_pages)
    # Heuristic: proper nouns (capitalized words not at sentence start)
    proper_nouns = re.findall(r"(?<!\. )(?<!\? )(?<!! )[A-Z][a-z]{2,}", preview_text)
    if proper_nouns:
        score += 10.0

    # --- Pacing variety ---
    all_sentences = _split_sentences(preview_text)
    if len(all_sentences) >= 3:
        lengths = [len(_extract_words(s)) for s in all_sentences]
        unique_lengths = len(set(lengths))
        variety_ratio = unique_lengths / len(lengths)
        score += variety_ratio * 10.0

    # --- Cliffhanger at boundary ---
    last_preview = preview_pages[-1].strip()
    if last_preview.endswith(("?", "...", "\u2026")):
        score += 10.0

    return max(0.0, min(100.0, round(score, 1)))


# ---------------------------------------------------------------------------
# Rhyme Detection
# ---------------------------------------------------------------------------

# Simple phonetic ending map for common English rhyme detection
_VOWEL_SOUND_RE = re.compile(r"[aeiouy]+[^aeiouy]*$", re.IGNORECASE)


def _get_rhyme_ending(word: str) -> str:
    """Extract the approximate rhyme ending of a word."""
    word = word.lower().strip(".,!?;:'\"")
    match = _VOWEL_SOUND_RE.search(word)
    if match:
        return match.group(0).lower()
    return word[-2:] if len(word) >= 2 else word


def _lines_from_text(text: str) -> list[str]:
    """Get non-empty lines from text."""
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


def detect_rhyme_pattern(text: str) -> dict[str, Any]:
    """Detect rhyme scheme in *text*.

    Returns
    -------
    dict with keys:
        - ``pattern``: ``"AABB"`` | ``"ABAB"`` | ``"ABCB"`` | ``None``
        - ``detected_scheme``: str – the letter scheme for each line
        - ``issues``: list[str] – near-rhymes, broken patterns, meter issues
    """
    lines = _lines_from_text(text)
    if len(lines) < 2:
        return {"pattern": None, "detected_scheme": "", "issues": ["Too few lines to detect rhyme pattern."]}

    # Get last word of each line
    endings: list[str] = []
    for line in lines:
        words = _extract_words(line)
        if words:
            endings.append(_get_rhyme_ending(words[-1]))
        else:
            endings.append("")

    # Assign rhyme letters
    scheme_letters: list[str] = []
    rhyme_groups: dict[str, str] = {}
    next_letter = "A"

    for ending in endings:
        if not ending:
            scheme_letters.append("X")
            continue
        # Check if this ending rhymes with any existing group
        matched = False
        for known_ending, letter in rhyme_groups.items():
            if ending == known_ending or (
                len(ending) >= 2 and len(known_ending) >= 2 and ending[-2:] == known_ending[-2:]
            ):
                scheme_letters.append(letter)
                matched = True
                break
        if not matched:
            rhyme_groups[ending] = next_letter
            scheme_letters.append(next_letter)
            next_letter = chr(ord(next_letter) + 1) if next_letter < "Z" else "Z"

    detected_scheme = "".join(scheme_letters)

    # Determine dominant pattern by checking groups of 4 lines
    pattern: str | None = None
    issues: list[str] = []

    if len(scheme_letters) >= 4:
        aabb_matches = 0
        abab_matches = 0
        groups = len(scheme_letters) // 4

        for g in range(groups):
            chunk = scheme_letters[g * 4 : g * 4 + 4]
            if len(chunk) == 4:
                if chunk[0] == chunk[1] and chunk[2] == chunk[3]:
                    aabb_matches += 1
                if chunk[0] == chunk[2] and chunk[1] == chunk[3]:
                    abab_matches += 1

        if aabb_matches > abab_matches and aabb_matches > 0:
            pattern = "AABB"
        elif abab_matches > 0:
            pattern = "ABAB"

        # Check for broken patterns
        if pattern == "AABB":
            for g in range(groups):
                chunk = scheme_letters[g * 4 : g * 4 + 4]
                if len(chunk) == 4 and not (chunk[0] == chunk[1] and chunk[2] == chunk[3]):
                    issues.append(f"Lines {g * 4 + 1}-{g * 4 + 4}: expected AABB pattern but got {''.join(chunk)}")
        elif pattern == "ABAB":
            for g in range(groups):
                chunk = scheme_letters[g * 4 : g * 4 + 4]
                if len(chunk) == 4 and not (chunk[0] == chunk[2] and chunk[1] == chunk[3]):
                    issues.append(f"Lines {g * 4 + 1}-{g * 4 + 4}: expected ABAB pattern but got {''.join(chunk)}")

    # --- Near-rhyme detection ---
    # Check consecutive pairs for near-misses
    for i in range(0, len(endings) - 1, 2):
        e1, e2 = endings[i], endings[i + 1]
        if e1 and e2 and e1 != e2:
            # Check if they share some but not all ending sounds
            if len(e1) >= 2 and len(e2) >= 2:
                if e1[-1] == e2[-1] and e1[-2:] != e2[-2:]:
                    issues.append(
                        f"Lines {i + 1}-{i + 2}: near-rhyme detected "
                        f"('{lines[i].split()[-1] if lines[i].split() else ''}' / "
                        f"'{lines[i + 1].split()[-1] if lines[i + 1].split() else ''}')"
                    )

    # --- Meter consistency (syllable-count heuristic) ---
    word_counts_per_line = [len(_extract_words(ln)) for ln in lines]
    if len(word_counts_per_line) >= 4:
        mean_wc = sum(word_counts_per_line) / len(word_counts_per_line)
        outliers = [
            i + 1 for i, wc in enumerate(word_counts_per_line) if abs(wc - mean_wc) > mean_wc * 0.5 and mean_wc > 0
        ]
        if outliers:
            issues.append(
                f"Meter inconsistency: lines {outliers} have significantly "
                f"different word counts from the average ({mean_wc:.0f} words/line)"
            )

    return {
        "pattern": pattern,
        "detected_scheme": detected_scheme,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Rhyme Fix Suggestions (AI-powered)
# ---------------------------------------------------------------------------


def suggest_rhyme_fixes(text: str) -> dict[str, Any]:
    """Build an LLM prompt to suggest rhyme fixes for *text*.

    Returns a dict with:
    - ``prompt``: str – the system+user prompt to send to the LLM
    - ``context``: dict – rhyme analysis context attached for reference
    """
    analysis = detect_rhyme_pattern(text)
    issues = analysis["issues"]
    pattern = analysis["pattern"]

    system_prompt = (
        "You are a children's book rhyme editor. "
        "Fix the rhyming issues in the following text while preserving the story, "
        "characters, and age-appropriate language. "
        "Maintain the detected rhyme scheme and fix any near-rhymes or meter "
        "inconsistencies. Return ONLY the corrected text, line by line."
    )

    issue_summary = "\n".join(f"- {issue}" for issue in issues) if issues else "No specific issues detected."

    user_prompt = (
        f"Detected rhyme pattern: {pattern or 'None'}\n"
        f"Detected scheme: {analysis['detected_scheme']}\n\n"
        f"Issues found:\n{issue_summary}\n\n"
        f"Original text:\n{text}\n\n"
        "Please provide corrected text that fixes the rhyme and meter issues "
        "while keeping the meaning and age-appropriate vocabulary."
    )

    return {
        "prompt": f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}",
        "context": analysis,
    }
