"""Safety & Provenance module for Children's Book Studio.

Provides trademark scanning, content sensitivity analysis, font license
checking, and provenance record generation for AI-generated assets.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Trademark blocklist
# ---------------------------------------------------------------------------

TRADEMARK_BLOCKLIST: list[str] = [
    # Major studios / franchises
    "Disney",
    "Pixar",
    "DreamWorks",
    "Nickelodeon",
    "Cartoon Network",
    # Specific children's properties
    "Peppa Pig",
    "Bluey",
    "Paw Patrol",
    "Cocomelon",
    "Sesame Street",
    "Dora the Explorer",
    "SpongeBob",
    "Sponge Bob",
    "Thomas the Tank Engine",
    "Thomas & Friends",
    "Teletubbies",
    "Bob the Builder",
    "Barney",
    "Blue's Clues",
    "Daniel Tiger",
    "Curious George",
    "Caillou",
    "Elmo",
    "Big Bird",
    "Winnie the Pooh",
    "Pooh Bear",
    "Hello Kitty",
    "Pokemon",
    "Pokémon",
    # Superhero / action
    "Marvel",
    "Avengers",
    "Spider-Man",
    "Spiderman",
    "Batman",
    "Superman",
    "DC Comics",
    "Transformers",
    "Power Rangers",
    # Movie / franchise characters
    "Frozen",
    "Elsa",
    "Moana",
    "Encanto",
    "Toy Story",
    "Buzz Lightyear",
    "Lightning McQueen",
    "Nemo",
    "Finding Nemo",
    "Shrek",
    "Minions",
    "Baby Shark",
    # Gaming
    "Mario",
    "Super Mario",
    "Minecraft",
    "Roblox",
    "Fortnite",
    # Toys / brands
    "Barbie",
    "LEGO",
    "Hot Wheels",
    "My Little Pony",
    "Care Bears",
    "Cabbage Patch",
    "Build-A-Bear",
]

# Regex patterns for "in the style of [artist]" and similar constructs
_STYLE_OF_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"in\s+the\s+style\s+of\s+[\w\s]+", re.IGNORECASE),
    re.compile(r"inspired\s+by\s+[\w\s]+(?:art|illustration|style)", re.IGNORECASE),
    re.compile(r"like\s+[\w\s]+(?:draws|drew|paints|painted|illustrates)", re.IGNORECASE),
    re.compile(r"(?:resembling|mimicking|copying)\s+[\w\s]+(?:'s)?\s+(?:art|style|work)", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class IssueSeverity(str, Enum):
    critical = "critical"
    warning = "warning"
    info = "info"


@dataclass
class TrademarkIssue:
    """A single trademark violation found in text."""

    term: str
    start: int
    end: int
    context: str
    severity: IssueSeverity = IssueSeverity.critical


@dataclass
class SensitivityIssue:
    """A content sensitivity concern found in text."""

    category: str  # violence | fear | stereotypes | mature_themes
    description: str
    severity: IssueSeverity
    start: int | None = None
    end: int | None = None


@dataclass
class FontLicenseInfo:
    """License metadata for a font."""

    font_name: str
    license_type: str
    commercial_print_safe: bool
    source: str | None = None
    license_url: str | None = None


@dataclass
class ProvenanceRecord:
    """Provenance metadata for a generated asset."""

    model: str
    prompt_hash: str
    seed: str
    generated_date: str
    settings: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Known font license registry (expandable via database)
# ---------------------------------------------------------------------------

_FONT_LICENSE_REGISTRY: dict[str, FontLicenseInfo] = {
    "open sans": FontLicenseInfo(
        font_name="Open Sans",
        license_type="Apache 2.0",
        commercial_print_safe=True,
        source="Google Fonts",
        license_url="https://www.apache.org/licenses/LICENSE-2.0",
    ),
    "lora": FontLicenseInfo(
        font_name="Lora",
        license_type="OFL 1.1",
        commercial_print_safe=True,
        source="Google Fonts",
        license_url="https://scripts.sil.org/OFL",
    ),
    "comic neue": FontLicenseInfo(
        font_name="Comic Neue",
        license_type="OFL 1.1",
        commercial_print_safe=True,
        source="Google Fonts",
        license_url="https://scripts.sil.org/OFL",
    ),
    "roboto": FontLicenseInfo(
        font_name="Roboto",
        license_type="Apache 2.0",
        commercial_print_safe=True,
        source="Google Fonts",
        license_url="https://www.apache.org/licenses/LICENSE-2.0",
    ),
    "montserrat": FontLicenseInfo(
        font_name="Montserrat",
        license_type="OFL 1.1",
        commercial_print_safe=True,
        source="Google Fonts",
        license_url="https://scripts.sil.org/OFL",
    ),
    "playfair display": FontLicenseInfo(
        font_name="Playfair Display",
        license_type="OFL 1.1",
        commercial_print_safe=True,
        source="Google Fonts",
        license_url="https://scripts.sil.org/OFL",
    ),
    "merriweather": FontLicenseInfo(
        font_name="Merriweather",
        license_type="OFL 1.1",
        commercial_print_safe=True,
        source="Google Fonts",
        license_url="https://scripts.sil.org/OFL",
    ),
    "nunito": FontLicenseInfo(
        font_name="Nunito",
        license_type="OFL 1.1",
        commercial_print_safe=True,
        source="Google Fonts",
        license_url="https://scripts.sil.org/OFL",
    ),
    "poppins": FontLicenseInfo(
        font_name="Poppins",
        license_type="OFL 1.1",
        commercial_print_safe=True,
        source="Google Fonts",
        license_url="https://scripts.sil.org/OFL",
    ),
    "arial": FontLicenseInfo(
        font_name="Arial",
        license_type="Proprietary (Microsoft)",
        commercial_print_safe=False,
        source="Microsoft",
        license_url=None,
    ),
    "times new roman": FontLicenseInfo(
        font_name="Times New Roman",
        license_type="Proprietary (Monotype)",
        commercial_print_safe=False,
        source="Monotype",
        license_url=None,
    ),
    "helvetica": FontLicenseInfo(
        font_name="Helvetica",
        license_type="Proprietary (Linotype)",
        commercial_print_safe=False,
        source="Linotype",
        license_url=None,
    ),
}

# ---------------------------------------------------------------------------
# Sensitivity keyword patterns (by category and age range)
# ---------------------------------------------------------------------------

_VIOLENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:gun|rifle|pistol|sword|dagger|knife|weapon|stab|shoot|kill|murder|blood|bleeding|wound)\b", re.IGNORECASE),
    re.compile(r"\b(?:punch|hit|slap|beat|attack|fight|battle|war|destroy|explode)\b", re.IGNORECASE),
]

_FEAR_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:terrif(?:y|ied|ying)|horrif(?:y|ied|ying)|nightmare|scream(?:ing)?|demon|devil|ghost|haunted|creepy|sinister|menacing)\b", re.IGNORECASE),
    re.compile(r"\b(?:dark\s+shadow|lurking|stalking|threatening|ominous|dread|panic)\b", re.IGNORECASE),
]

_STEREOTYPE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:savage|primitive|exotic|oriental|gypsy|eskimo|redskin|squaw|chief\s+[\w]+\s+feather)\b", re.IGNORECASE),
    re.compile(r"\b(?:boys\s+don't\s+cry|girls\s+can't|only\s+boys|only\s+girls|real\s+men|real\s+women)\b", re.IGNORECASE),
]

_MATURE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:drunk|alcohol|beer|wine|cigarette|smoking|drug|cocaine|marijuana|sexy|seductive|nude|naked)\b", re.IGNORECASE),
    re.compile(r"\b(?:suicide|self-harm|abuse|molest|rape|prostitut)\b", re.IGNORECASE),
]

_SENSITIVITY_CATEGORIES: dict[str, list[re.Pattern[str]]] = {
    "violence": _VIOLENCE_PATTERNS,
    "fear": _FEAR_PATTERNS,
    "stereotypes": _STEREOTYPE_PATTERNS,
    "mature_themes": _MATURE_PATTERNS,
}

# Age ranges where severity is escalated
_YOUNG_AGE_RANGES = {"0-3", "3-5", "board", "picture"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_trademarks(text: str) -> list[TrademarkIssue]:
    """Scan *text* for trademarked terms and artist-style patterns.

    Returns a list of :class:`TrademarkIssue` with the matched term,
    character offsets, and a short context snippet.
    """
    issues: list[TrademarkIssue] = []
    text_lower = text.lower()

    # Check blocklist terms
    for term in TRADEMARK_BLOCKLIST:
        term_lower = term.lower()
        start = 0
        while True:
            idx = text_lower.find(term_lower, start)
            if idx == -1:
                break
            # Extract surrounding context (up to 40 chars each side)
            ctx_start = max(0, idx - 40)
            ctx_end = min(len(text), idx + len(term) + 40)
            context = text[ctx_start:ctx_end]
            if ctx_start > 0:
                context = "..." + context
            if ctx_end < len(text):
                context = context + "..."

            issues.append(
                TrademarkIssue(
                    term=term,
                    start=idx,
                    end=idx + len(term),
                    context=context,
                    severity=IssueSeverity.critical,
                )
            )
            start = idx + len(term)

    # Check "in the style of" patterns
    for pattern in _STYLE_OF_PATTERNS:
        for match in pattern.finditer(text):
            ctx_start = max(0, match.start() - 20)
            ctx_end = min(len(text), match.end() + 20)
            context = text[ctx_start:ctx_end]
            if ctx_start > 0:
                context = "..." + context
            if ctx_end < len(text):
                context = context + "..."

            issues.append(
                TrademarkIssue(
                    term=match.group(),
                    start=match.start(),
                    end=match.end(),
                    context=context,
                    severity=IssueSeverity.critical,
                )
            )

    return issues


def scan_content_sensitivity(
    text: str,
    age_range: str = "3-5",
) -> list[SensitivityIssue]:
    """Scan *text* for content sensitivity issues appropriate for *age_range*.

    Categories: violence, fear, stereotypes, mature_themes.
    Severity is escalated for younger age ranges.
    """
    issues: list[SensitivityIssue] = []
    is_young = age_range.lower() in _YOUNG_AGE_RANGES

    for category, patterns in _SENSITIVITY_CATEGORIES.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                # Determine severity based on category + age range
                if category == "mature_themes":
                    severity = IssueSeverity.critical
                elif category == "violence":
                    severity = IssueSeverity.critical if is_young else IssueSeverity.warning
                elif category == "fear":
                    severity = IssueSeverity.warning if is_young else IssueSeverity.info
                elif category == "stereotypes":
                    severity = IssueSeverity.warning
                else:
                    severity = IssueSeverity.info

                # Build a human-readable description
                matched_text = match.group()
                ctx_start = max(0, match.start() - 30)
                ctx_end = min(len(text), match.end() + 30)
                context = text[ctx_start:ctx_end].strip()

                issues.append(
                    SensitivityIssue(
                        category=category,
                        description=(
                            f"Found '{matched_text}' in context: "
                            f"\"{context}\". "
                            f"Review for age-appropriateness ({age_range})."
                        ),
                        severity=severity,
                        start=match.start(),
                        end=match.end(),
                    )
                )

    return issues


def check_font_license(font_name: str) -> FontLicenseInfo:
    """Look up license information for *font_name*.

    Returns a :class:`FontLicenseInfo`. If the font is not in the known
    registry, returns an ``unknown`` entry with ``commercial_print_safe=False``
    to be safe.
    """
    key = font_name.strip().lower()
    if key in _FONT_LICENSE_REGISTRY:
        return _FONT_LICENSE_REGISTRY[key]

    # Unknown font -- flag as unsafe by default
    return FontLicenseInfo(
        font_name=font_name,
        license_type="Unknown",
        commercial_print_safe=False,
        source=None,
        license_url=None,
    )


def generate_provenance_record(
    model: str,
    prompt: str,
    seed: str,
    *,
    settings: dict[str, Any] | None = None,
) -> ProvenanceRecord:
    """Create a :class:`ProvenanceRecord` for a generated asset.

    The prompt is hashed with SHA-256; the original text is **not** stored
    in the record to keep it lightweight and privacy-friendly.
    """
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    generated_date = datetime.now(timezone.utc).isoformat()

    return ProvenanceRecord(
        model=model,
        prompt_hash=prompt_hash,
        seed=str(seed),
        generated_date=generated_date,
        settings=settings or {},
    )
