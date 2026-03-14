"""Review Feedback Loop.

Maps common reader complaints from Amazon reviews to actionable fixes
that can be applied within SelfPublisherForge.

Blueprint refs: 12.6
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FeedbackAction:
    """A single actionable fix derived from a reader complaint."""

    complaint: str
    category: str
    suggested_fix: str
    action: str


# ---------------------------------------------------------------------------
# Complaint classification & mapping
# ---------------------------------------------------------------------------

COMPLAINT_MAP: dict[str, dict[str, str]] = {
    # Paper / print quality complaints
    "pages thin": {
        "category": "print_quality",
        "suggested_fix": "Switch to premium (heavier) paper stock. KDP offers 'white' and 'cream' "
                         "paper; IngramSpark offers 50#, 60#, and 70# options.",
        "action": "change_paper_type",
    },
    "pages see through": {
        "category": "print_quality",
        "suggested_fix": "Use heavier paper stock (70# or above) to reduce bleed-through. "
                         "Also reduce ink coverage on reverse sides.",
        "action": "change_paper_type",
    },

    # Color quality complaints
    "colors washed": {
        "category": "color_quality",
        "suggested_fix": "Run CMYK soft-proof to identify out-of-gamut colors. Boost saturation "
                         "by 10-15% and verify with soft-proof before re-exporting.",
        "action": "run_cmyk_softproof",
    },
    "colors too dark": {
        "category": "color_quality",
        "suggested_fix": "Check total ink coverage (should be under 240% for most printers). "
                         "Reduce shadow density and verify with soft-proof.",
        "action": "adjust_ink_coverage",
    },
    "colors different from screen": {
        "category": "color_quality",
        "suggested_fix": "Enable CMYK preview mode and export with embedded ICC profile. "
                         "Printed colors always differ from screen - use soft-proof to preview.",
        "action": "run_cmyk_softproof",
    },

    # Difficulty calibration complaints (puzzle books)
    "too easy": {
        "category": "difficulty",
        "suggested_fix": "Increase difficulty parameters: larger grids, more directions (word search), "
                         "fewer givens (sudoku), longer solution paths (maze).",
        "action": "adjust_difficulty_up",
    },
    "too hard": {
        "category": "difficulty",
        "suggested_fix": "Decrease difficulty parameters: smaller grids, fewer words, more hints. "
                         "Consider adding a progressive difficulty ramp (easy -> hard).",
        "action": "adjust_difficulty_down",
    },
    "not challenging enough": {
        "category": "difficulty",
        "suggested_fix": "Switch to 'progressive' difficulty mode with harder final section. "
                         "Add expert-level bonus puzzles at the end.",
        "action": "adjust_difficulty_up",
    },

    # Answer key complaints (puzzle books)
    "answers wrong": {
        "category": "answer_keys",
        "suggested_fix": "Re-run answer key verification pipeline. Every puzzle must be "
                         "algorithmically re-solved and compared against stored answer keys.",
        "action": "verify_answer_keys",
    },
    "answers missing": {
        "category": "answer_keys",
        "suggested_fix": "Regenerate answer key section. Verify numbering matches between "
                         "puzzle and answer key pages.",
        "action": "regenerate_answer_keys",
    },
    "answer key hard to read": {
        "category": "answer_keys",
        "suggested_fix": "Increase answer key font size. Use a maximum of 4 answers per page. "
                         "Ensure grid lines in answer keys are at least 1pt.",
        "action": "reformat_answer_keys",
    },

    # Typography / readability complaints
    "print too small": {
        "category": "typography",
        "suggested_fix": "Generate a Large Print variant (125-175% scale). For standard edition, "
                         "increase base font to at least 14pt for body text, 18pt for puzzle grids.",
        "action": "generate_large_print",
    },
    "text hard to read": {
        "category": "typography",
        "suggested_fix": "Check font choice (use high-legibility fonts), increase letter spacing, "
                         "verify contrast ratio meets WCAG AA (4.5:1 minimum).",
        "action": "improve_typography",
    },
    "font too light": {
        "category": "typography",
        "suggested_fix": "Switch to a bolder font weight. Ensure text is rendered in pure black "
                         "(K=100%) rather than rich black or grey.",
        "action": "improve_typography",
    },

    # Binding / physical complaints
    "binding breaks": {
        "category": "binding",
        "suggested_fix": "Check gutter margins - increase inner margin to at least 0.75in for "
                         "books over 200 pages. Run gutter collision detector.",
        "action": "check_gutter_margins",
    },
    "pages fall out": {
        "category": "binding",
        "suggested_fix": "For high page-count books, consider splitting into multiple volumes. "
                         "Ensure gutter margins accommodate perfect binding requirements.",
        "action": "check_gutter_margins",
    },
    "spine text cut off": {
        "category": "binding",
        "suggested_fix": "Recalculate spine width based on page count and paper type. "
                         "Add safety margins on spine text.",
        "action": "recalculate_spine",
    },

    # Content quality complaints
    "repetitive content": {
        "category": "content_quality",
        "suggested_fix": "Run originality fingerprint check. Ensure duplicate-page detector "
                         "confirms < 85% similarity between any two pages.",
        "action": "run_originality_check",
    },
    "not enough variety": {
        "category": "content_quality",
        "suggested_fix": "Enable variation mode during generation. Add mix of puzzle types "
                         "or illustration themes.",
        "action": "increase_variety",
    },
    "images blurry": {
        "category": "image_quality",
        "suggested_fix": "Verify all images are at least 300 DPI at print size. "
                         "Regenerate any images below the DPI threshold.",
        "action": "check_image_dpi",
    },
}

# Additional keywords that map to existing complaint entries.
_KEYWORD_ALIASES: dict[str, str] = {
    "thin pages": "pages thin",
    "flimsy": "pages thin",
    "washed out": "colors washed",
    "faded colors": "colors washed",
    "dull colors": "colors washed",
    "wrong answers": "answers wrong",
    "incorrect answers": "answers wrong",
    "no answers": "answers missing",
    "small print": "print too small",
    "tiny text": "print too small",
    "tiny font": "print too small",
    "falls apart": "binding breaks",
    "broke spine": "binding breaks",
    "same puzzles": "repetitive content",
    "duplicate": "repetitive content",
    "blurry": "images blurry",
    "pixelated": "images blurry",
    "low quality images": "images blurry",
    "too simple": "too easy",
    "boring puzzles": "too easy",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_feedback(complaints: list[str]) -> list[FeedbackAction]:
    """Analyse a list of reader complaints and return actionable fixes.

    Each complaint string is matched against ``COMPLAINT_MAP`` (exact)
    and ``_KEYWORD_ALIASES`` (fuzzy keyword lookup).  Unrecognised
    complaints are returned with a generic investigation action.

    Parameters
    ----------
    complaints:
        Free-text complaint strings, e.g. ``["pages thin", "answers wrong"]``.

    Returns
    -------
    list[FeedbackAction]
        One action per input complaint, in the same order.
    """
    results: list[FeedbackAction] = []

    for raw in complaints:
        normalised = raw.strip().lower()

        # Direct match.
        if normalised in COMPLAINT_MAP:
            entry = COMPLAINT_MAP[normalised]
            results.append(FeedbackAction(
                complaint=raw,
                category=entry["category"],
                suggested_fix=entry["suggested_fix"],
                action=entry["action"],
            ))
            continue

        # Alias / keyword match.
        if normalised in _KEYWORD_ALIASES:
            canonical = _KEYWORD_ALIASES[normalised]
            entry = COMPLAINT_MAP[canonical]
            results.append(FeedbackAction(
                complaint=raw,
                category=entry["category"],
                suggested_fix=entry["suggested_fix"],
                action=entry["action"],
            ))
            continue

        # Partial keyword search across all keys.
        matched = False
        for key, entry in COMPLAINT_MAP.items():
            if key in normalised or normalised in key:
                results.append(FeedbackAction(
                    complaint=raw,
                    category=entry["category"],
                    suggested_fix=entry["suggested_fix"],
                    action=entry["action"],
                ))
                matched = True
                break

        if not matched:
            # Also check aliases for partial matches.
            for alias, canonical in _KEYWORD_ALIASES.items():
                if alias in normalised or normalised in alias:
                    entry = COMPLAINT_MAP[canonical]
                    results.append(FeedbackAction(
                        complaint=raw,
                        category=entry["category"],
                        suggested_fix=entry["suggested_fix"],
                        action=entry["action"],
                    ))
                    matched = True
                    break

        if not matched:
            results.append(FeedbackAction(
                complaint=raw,
                category="unknown",
                suggested_fix="This complaint could not be automatically categorised. "
                              "Review the feedback manually and investigate the specific issue.",
                action="manual_review",
            ))

    return results
