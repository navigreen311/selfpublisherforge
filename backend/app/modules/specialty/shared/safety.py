"""Content Safety -- Trademark, Sensitivity, and Word-List Filters.

Shared safety layer used across all specialty book types (Children's,
Coloring, Puzzle) to prevent trademark infringement, inappropriate
content, and offensive language in published materials.

Blueprint refs: 3.7, 5.4, 7.1
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Trademark blocklist (~100 terms)
# ---------------------------------------------------------------------------

TRADEMARK_BLOCKLIST: frozenset[str] = frozenset({
    # Disney / Pixar / Marvel / Star Wars
    "disney", "pixar", "marvel", "avengers", "spider-man", "spiderman",
    "iron man", "ironman", "hulk", "thor", "captain america", "black panther",
    "black widow", "guardians of the galaxy", "frozen", "elsa", "moana",
    "encanto", "coco", "toy story", "woody", "buzz lightyear", "finding nemo",
    "finding dory", "cars", "lightning mcqueen", "monsters inc", "inside out",
    "the incredibles", "ratatouille", "star wars", "darth vader", "yoda",
    "mandalorian", "baby yoda", "grogu", "lightsaber",
    # DC Comics
    "dc comics", "batman", "superman", "wonder woman", "justice league",
    "aquaman", "the flash", "joker", "harley quinn",
    # Nintendo / Gaming
    "nintendo", "mario", "luigi", "princess peach", "zelda", "link",
    "pokemon", "pikachu", "kirby", "donkey kong", "metroid",
    "sonic", "sonic the hedgehog",
    # Children's brands
    "peppa pig", "bluey", "paw patrol", "cocomelon", "sesame street",
    "elmo", "big bird", "dora the explorer", "spongebob", "spongebob squarepants",
    "patrick star", "thomas the tank engine", "thomas & friends",
    "teletubbies", "barney", "curious george", "clifford",
    "bob the builder", "fireman sam", "postman pat", "hey duggee",
    "octonauts", "daniel tiger", "baby shark", "blippi",
    # Toy & consumer brands
    "barbie", "hot wheels", "lego", "playmobil", "transformers",
    "my little pony", "care bears", "cabbage patch", "bratz",
    "build-a-bear", "nerf", "monopoly",
    # Cartoon / anime
    "hello kitty", "sanrio", "doraemon", "naruto", "dragon ball",
    "one piece", "sailor moon",
    # Other media
    "harry potter", "hogwarts", "lord of the rings", "hobbit",
    "hunger games", "game of thrones", "winnie the pooh", "paddington",
    "peter rabbit", "gruffalo", "dr. seuss", "dr seuss",
    "cat in the hat", "lorax",
    # Tech / other
    "google", "apple", "microsoft", "amazon", "netflix", "youtube",
    "tiktok", "instagram", "facebook", "roblox", "minecraft", "fortnite",
})


# ---------------------------------------------------------------------------
# Artist style pattern
# ---------------------------------------------------------------------------

ARTIST_STYLE_PATTERN: re.Pattern[str] = re.compile(
    r"""
    (?:
        in\s+the\s+style\s+of\s+     # "in the style of [name]"
      | inspired\s+by\s+              # "inspired by [name]"
      | (\b\w[\w\s]{2,30})-style\b    # "[name]-style"
      | \blike\s+                     # "like [artist]"
      | \bsimilar\s+to\s+            # "similar to [artist]"
      | \bimitating\s+               # "imitating [artist]"
      | \breminist?cent\s+of\s+      # "reminiscent of [artist]"
      | \bin\s+the\s+manner\s+of\s+  # "in the manner of [artist]"
      | à\s+la\s+                    # "à la [artist]"
    )
    ([\w][\w\s.'-]{1,40})            # Capture the name
    """,
    re.IGNORECASE | re.VERBOSE,
)


# ---------------------------------------------------------------------------
# Offensive word filter (~200 terms)
# ---------------------------------------------------------------------------

OFFENSIVE_WORDS: frozenset[str] = frozenset({
    # Profanity
    "fuck", "shit", "ass", "asshole", "bitch", "bastard", "damn", "crap",
    "dick", "cock", "piss", "cunt", "twat", "bollocks", "wanker", "tosser",
    "motherfucker", "bullshit", "horseshit", "dumbass", "jackass", "dipshit",
    "shithead", "fuckface", "fuckwit", "arsehole",
    # Slurs and hate speech
    "nigger", "nigga", "chink", "gook", "spic", "wetback", "beaner",
    "kike", "faggot", "fag", "dyke", "tranny", "retard", "retarded",
    "cripple", "mongoloid", "halfbreed", "redskin", "injun", "squaw",
    "raghead", "towelhead", "camel jockey", "sand nigger", "cracker",
    "honky", "gringo", "jap", "zipperhead", "slope",
    # Sexual / explicit
    "penis", "vagina", "boobs", "tits", "nipple", "erection", "orgasm",
    "masturbate", "masturbation", "ejaculate", "ejaculation", "dildo",
    "vibrator", "pornography", "porn", "hentai", "fetish", "bondage",
    "dominatrix", "stripper", "prostitute", "whore", "hooker", "pimp",
    "brothel", "escort", "intercourse", "fornication", "sodomy",
    "fellatio", "cunnilingus", "genitals", "genitalia", "pubic",
    "scrotum", "testicle", "clitoris", "labia", "anus", "anal",
    "erotic", "erotica", "smut", "obscene", "pervert", "pedophile",
    "paedophile", "molest", "molestation", "rape", "rapist",
    # Violence (extreme)
    "murder", "murderer", "killer", "killing", "slaughter", "massacre",
    "genocide", "decapitate", "decapitation", "dismember", "disembowel",
    "mutilate", "mutilation", "torture", "torment", "bloodbath",
    "carnage", "butcher", "execution", "assassinate", "assassination",
    "homicide", "manslaughter",
    # Substance abuse
    "cocaine", "heroin", "methamphetamine", "meth", "crack", "ecstasy",
    "lsd", "marijuana", "weed", "cannabis", "ketamine", "fentanyl",
    "opioid", "overdose", "junkie", "crackhead", "stoner",
    # Self-harm
    "suicide", "suicidal", "self-harm", "self-mutilation", "cutting",
    # Misc inappropriate for children
    "nazi", "hitler", "swastika", "kkk", "ku klux klan", "white supremacy",
    "jihad", "terrorist", "terrorism", "extremist", "extremism",
    "necrophilia", "bestiality", "incest",
    # Body shaming / bullying
    "fatass", "lardass", "ugly", "fugly", "freak", "loser", "idiot",
    "moron", "imbecile", "stupid",
    # Bathroom humour (inappropriate for formal publications)
    "poop", "turd", "diarrhea", "fart", "vomit", "booger", "snot",
    "puke", "barf",
})


# ---------------------------------------------------------------------------
# Sensitivity categories
# ---------------------------------------------------------------------------

_SENSITIVITY_PATTERNS: dict[str, list[tuple[re.Pattern[str], str, str]]] = {
    "violence": [
        (re.compile(r"\b(gun|guns|rifle|shotgun|pistol|firearm|firearms)\b", re.I),
         "medium", "Replace with non-weapon alternatives"),
        (re.compile(r"\b(sword|dagger|knife|blade|axe)\b", re.I),
         "low", "Consider age-appropriateness of weapon references"),
        (re.compile(r"\b(kill|killing|murder|stab|shoot|shooting|attack|fight|fighting|punch|kick|blood|bleeding|wound|wounded)\b", re.I),
         "medium", "Avoid violent language; use conflict resolution themes"),
        (re.compile(r"\b(bomb|explosion|explode|grenade|missile|warfare)\b", re.I),
         "high", "Remove military/explosive references"),
    ],
    "weapons": [
        (re.compile(r"\b(weapon|weapons|ammo|ammunition|bullet|bullets|cannon|artillery)\b", re.I),
         "high", "Remove all weapon references for children's content"),
        (re.compile(r"\b(crossbow|bow and arrow|spear|lance)\b", re.I),
         "low", "Consider context; may be acceptable in fantasy settings"),
    ],
    "fear_horror": [
        (re.compile(r"\b(monster|demon|devil|evil|ghost|haunted|zombie|vampire|skeleton|skull|death|dead|die|dying|cemetery|graveyard)\b", re.I),
         "medium", "Evaluate fear intensity for target age range"),
        (re.compile(r"\b(nightmare|terror|terrify|terrifying|horror|scream|screaming|blood|gore|gory)\b", re.I),
         "high", "Too intense for young children; tone down or remove"),
        (re.compile(r"\b(dark|darkness|shadow|scary|creepy|spooky)\b", re.I),
         "low", "May be acceptable depending on age range and context"),
    ],
    "stereotypes": [
        (re.compile(r"\b(savage|primitive|exotic|oriental|gyps[yi]e?|tribe|tribal)\b", re.I),
         "medium", "Use culturally respectful alternatives"),
        (re.compile(r"\b(chief|medicine man|spirit animal|pow\s*wow)\b", re.I),
         "medium", "Avoid cultural appropriation; use respectful language"),
        (re.compile(r"\b(crazy|insane|psycho|lunatic|schizo)\b", re.I),
         "low", "Avoid mental health stigma; use precise language"),
    ],
    "mature_themes": [
        (re.compile(r"\b(sex|sexual|sexy|seduc|romantic|romance|kiss|kissing|lover|lovers)\b", re.I),
         "medium", "Not appropriate for children's content"),
        (re.compile(r"\b(naked|nude|nudity|undress|strip|topless)\b", re.I),
         "high", "Remove nudity references"),
        (re.compile(r"\b(pregnant|pregnancy|birth|giving birth|labor|childbirth)\b", re.I),
         "low", "May require sensitive handling for young audiences"),
    ],
    "substance_references": [
        (re.compile(r"\b(beer|wine|alcohol|drunk|drinking|vodka|whiskey|cocktail|bar|pub|liquor)\b", re.I),
         "medium", "Remove alcohol references for children's content"),
        (re.compile(r"\b(smoking|cigarette|cigar|tobacco|vape|vaping)\b", re.I),
         "high", "Remove all smoking/tobacco references"),
        (re.compile(r"\b(drug|drugs|pill|pills|needle|inject|syringe)\b", re.I),
         "high", "Remove drug references (unless medical context)"),
    ],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_text_for_trademarks(text: str) -> list[dict[str, Any]]:
    """Scan text for trademarked terms.

    Returns a list of dicts with keys: ``term``, ``position``, ``context``.
    """
    if not text:
        return []

    results: list[dict[str, Any]] = []
    text_lower = text.lower()

    for term in TRADEMARK_BLOCKLIST:
        start = 0
        while True:
            pos = text_lower.find(term, start)
            if pos == -1:
                break

            # Verify word boundary (not part of a larger word)
            before_ok = pos == 0 or not text_lower[pos - 1].isalnum()
            after_pos = pos + len(term)
            after_ok = after_pos >= len(text_lower) or not text_lower[after_pos].isalnum()

            if before_ok and after_ok:
                # Extract context (up to 30 chars on each side)
                ctx_start = max(0, pos - 30)
                ctx_end = min(len(text), pos + len(term) + 30)
                context = text[ctx_start:ctx_end]

                results.append({
                    "term": term,
                    "position": pos,
                    "context": context.strip(),
                })

            start = pos + 1

    # Also check for artist style references
    for match in ARTIST_STYLE_PATTERN.finditer(text):
        # The last group is the captured artist name
        artist_name = match.group(2) if match.group(2) else match.group(1)
        if artist_name:
            artist_name = artist_name.strip()
            results.append({
                "term": f"artist style reference: {artist_name}",
                "position": match.start(),
                "context": match.group(0).strip(),
            })

    return results


def scan_content_sensitivity(
    text: str,
    audience: str = "kids",
) -> list[dict[str, Any]]:
    """Scan text for content sensitivity issues.

    Parameters
    ----------
    text:
        The text to scan.
    audience:
        Target audience: ``"kids"``, ``"teens"``, ``"adults"``.
        Stricter filtering is applied for younger audiences.

    Returns
    -------
    list of dicts with keys: ``category``, ``severity``, ``text``,
    ``suggestion``.
    """
    if not text:
        return []

    results: list[dict[str, Any]] = []

    # Severity thresholds by audience
    # Adults: only flag "high"; Teens: flag "medium" and "high"; Kids: flag all
    min_severity = {
        "kids": "low",
        "teens": "medium",
        "adults": "high",
    }
    severity_order = {"low": 0, "medium": 1, "high": 2}
    threshold = severity_order.get(min_severity.get(audience, "low"), 0)

    for category, patterns in _SENSITIVITY_PATTERNS.items():
        for pattern, severity, suggestion in patterns:
            if severity_order.get(severity, 0) < threshold:
                continue
            for match in pattern.finditer(text):
                results.append({
                    "category": category,
                    "severity": severity,
                    "text": match.group(0),
                    "suggestion": suggestion,
                })

    return results


def check_word_list_safety(
    words: list[str],
) -> dict[str, Any]:
    """Filter a word list for offensive and inappropriate terms.

    Returns a dict with:
    - ``clean``: list of safe words
    - ``removed``: list of dicts with ``word`` and ``reason``
    """
    clean: list[str] = []
    removed: list[dict[str, str]] = []

    for word in words:
        word_stripped = word.strip()
        if not word_stripped:
            continue

        word_lower = word_stripped.lower()

        # Check against offensive words
        if word_lower in OFFENSIVE_WORDS:
            removed.append({"word": word_stripped, "reason": "offensive_language"})
            continue

        # Check against trademark blocklist
        if word_lower in TRADEMARK_BLOCKLIST:
            removed.append({"word": word_stripped, "reason": "trademark"})
            continue

        # Check for partial trademark matches (multi-word trademarks)
        is_trademark = False
        for tm in TRADEMARK_BLOCKLIST:
            if " " in tm and tm in word_lower:
                removed.append({"word": word_stripped, "reason": f"trademark ({tm})"})
                is_trademark = True
                break
        if is_trademark:
            continue

        clean.append(word_stripped)

    return {"clean": clean, "removed": removed}
