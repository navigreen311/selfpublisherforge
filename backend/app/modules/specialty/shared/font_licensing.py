"""Font License Registry.

Maintains a registry of commercially-safe fonts for print publication,
with license type and details.  All fonts listed here are verified safe
for commercial print use (KDP, IngramSpark, B&N Press).

Blueprint ref: 3.7 (Font Licensing), 6.2
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FontLicenseInfo:
    """License information for a single font."""

    font_name: str
    safe: bool
    license_type: str  # "sil_ofl", "apache_2", "ubuntu", "open_source", "commercial"
    details: str
    foundry: str = ""
    url: str = ""


# ---------------------------------------------------------------------------
# Safe font registry
# ---------------------------------------------------------------------------

SAFE_FONTS: dict[str, FontLicenseInfo] = {
    # --------------- Sans-Serif ---------------
    "Open Sans": FontLicenseInfo(
        font_name="Open Sans",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Free for commercial print.",
        foundry="Google / Steve Matteson",
        url="https://fonts.google.com/specimen/Open+Sans",
    ),
    "Roboto": FontLicenseInfo(
        font_name="Roboto",
        safe=True,
        license_type="apache_2",
        details="Apache License 2.0. Free for all commercial use.",
        foundry="Google / Christian Robertson",
        url="https://fonts.google.com/specimen/Roboto",
    ),
    "Lato": FontLicenseInfo(
        font_name="Lato",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Free for commercial print.",
        foundry="tyPoland / Lukasz Dziedzic",
        url="https://fonts.google.com/specimen/Lato",
    ),
    "Nunito": FontLicenseInfo(
        font_name="Nunito",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Rounded terminals, child-friendly.",
        foundry="Google / Vernon Adams",
        url="https://fonts.google.com/specimen/Nunito",
    ),
    "Nunito Sans": FontLicenseInfo(
        font_name="Nunito Sans",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Clean sans-serif variant of Nunito.",
        foundry="Google / Vernon Adams",
        url="https://fonts.google.com/specimen/Nunito+Sans",
    ),
    "Montserrat": FontLicenseInfo(
        font_name="Montserrat",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Geometric, modern headings.",
        foundry="Google / Julieta Ulanovsky",
        url="https://fonts.google.com/specimen/Montserrat",
    ),
    "Poppins": FontLicenseInfo(
        font_name="Poppins",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Geometric sans-serif.",
        foundry="Google / Indian Type Foundry",
        url="https://fonts.google.com/specimen/Poppins",
    ),
    "Raleway": FontLicenseInfo(
        font_name="Raleway",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Elegant thin weights available.",
        foundry="Google / Matt McInerney",
        url="https://fonts.google.com/specimen/Raleway",
    ),
    "Inter": FontLicenseInfo(
        font_name="Inter",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Excellent readability.",
        foundry="Google / Rasmus Andersson",
        url="https://fonts.google.com/specimen/Inter",
    ),
    "Source Sans 3": FontLicenseInfo(
        font_name="Source Sans 3",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Adobe's open-source sans-serif.",
        foundry="Adobe / Paul Hunt",
        url="https://fonts.google.com/specimen/Source+Sans+3",
    ),
    "PT Sans": FontLicenseInfo(
        font_name="PT Sans",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1 (ParaType Public License).",
        foundry="ParaType / Alexandra Korolkova",
        url="https://fonts.google.com/specimen/PT+Sans",
    ),
    # --------------- Serif ---------------
    "Merriweather": FontLicenseInfo(
        font_name="Merriweather",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Designed for screen readability, prints well.",
        foundry="Google / Eben Sorkin",
        url="https://fonts.google.com/specimen/Merriweather",
    ),
    "Playfair Display": FontLicenseInfo(
        font_name="Playfair Display",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Elegant display serif.",
        foundry="Google / Claus Eggers Sorensen",
        url="https://fonts.google.com/specimen/Playfair+Display",
    ),
    "Lora": FontLicenseInfo(
        font_name="Lora",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Well-balanced serif for body text.",
        foundry="Google / Cyreal",
        url="https://fonts.google.com/specimen/Lora",
    ),
    "Libre Baskerville": FontLicenseInfo(
        font_name="Libre Baskerville",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Classic Baskerville revival.",
        foundry="Google / Impallari Type",
        url="https://fonts.google.com/specimen/Libre+Baskerville",
    ),
    "EB Garamond": FontLicenseInfo(
        font_name="EB Garamond",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Revival of Claude Garamond's type.",
        foundry="Google / Georg Duffner",
        url="https://fonts.google.com/specimen/EB+Garamond",
    ),
    "Crimson Text": FontLicenseInfo(
        font_name="Crimson Text",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Inspired by old-style serif types.",
        foundry="Google / Sebastian Kosch",
        url="https://fonts.google.com/specimen/Crimson+Text",
    ),
    "PT Serif": FontLicenseInfo(
        font_name="PT Serif",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1 (ParaType Public License).",
        foundry="ParaType / Alexandra Korolkova",
        url="https://fonts.google.com/specimen/PT+Serif",
    ),
    "Source Serif 4": FontLicenseInfo(
        font_name="Source Serif 4",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Adobe's open-source serif.",
        foundry="Adobe / Frank Grie\u00dfhammer",
        url="https://fonts.google.com/specimen/Source+Serif+4",
    ),
    "Bitter": FontLicenseInfo(
        font_name="Bitter",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Slab serif, highly readable.",
        foundry="Google / Huerta Tipografica",
        url="https://fonts.google.com/specimen/Bitter",
    ),
    # --------------- Handwriting / Display ---------------
    "Comic Neue": FontLicenseInfo(
        font_name="Comic Neue",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Refined comic-style font, child-friendly.",
        foundry="Craig Rozynski",
        url="https://fonts.google.com/specimen/Comic+Neue",
    ),
    "Patrick Hand": FontLicenseInfo(
        font_name="Patrick Hand",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Casual handwriting style.",
        foundry="Google / Patrick Wagesreiter",
        url="https://fonts.google.com/specimen/Patrick+Hand",
    ),
    "Schoolbell": FontLicenseInfo(
        font_name="Schoolbell",
        safe=True,
        license_type="apache_2",
        details="Apache License 2.0. Playful handwriting, great for kids' books.",
        foundry="Google / Font Diner",
        url="https://fonts.google.com/specimen/Schoolbell",
    ),
    "Caveat": FontLicenseInfo(
        font_name="Caveat",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Natural handwriting style.",
        foundry="Google / Impallari Type",
        url="https://fonts.google.com/specimen/Caveat",
    ),
    "Indie Flower": FontLicenseInfo(
        font_name="Indie Flower",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Whimsical handwriting.",
        foundry="Google / Kimberly Geswein",
        url="https://fonts.google.com/specimen/Indie+Flower",
    ),
    "Fredoka": FontLicenseInfo(
        font_name="Fredoka",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Rounded, playful, perfect for children.",
        foundry="Google / Milena Brandao",
        url="https://fonts.google.com/specimen/Fredoka",
    ),
    "Bubblegum Sans": FontLicenseInfo(
        font_name="Bubblegum Sans",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Fun, bubbly display font.",
        foundry="Google / Sudtipos",
        url="https://fonts.google.com/specimen/Bubblegum+Sans",
    ),
    "Baloo 2": FontLicenseInfo(
        font_name="Baloo 2",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Rounded, friendly display font.",
        foundry="Google / Ek Type",
        url="https://fonts.google.com/specimen/Baloo+2",
    ),
    "Gaegu": FontLicenseInfo(
        font_name="Gaegu",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Korean-inspired handwriting font.",
        foundry="Google / JIKJI",
        url="https://fonts.google.com/specimen/Gaegu",
    ),
    # --------------- Monospace / Puzzle ---------------
    "Roboto Mono": FontLicenseInfo(
        font_name="Roboto Mono",
        safe=True,
        license_type="apache_2",
        details="Apache License 2.0. Monospace, ideal for puzzle grids.",
        foundry="Google / Christian Robertson",
        url="https://fonts.google.com/specimen/Roboto+Mono",
    ),
    "Source Code Pro": FontLicenseInfo(
        font_name="Source Code Pro",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Monospace, clear letter forms for grids.",
        foundry="Adobe / Paul Hunt",
        url="https://fonts.google.com/specimen/Source+Code+Pro",
    ),
    "Courier Prime": FontLicenseInfo(
        font_name="Courier Prime",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Improved Courier for print.",
        foundry="Google / Alan Dague-Greene",
        url="https://fonts.google.com/specimen/Courier+Prime",
    ),
    "IBM Plex Mono": FontLicenseInfo(
        font_name="IBM Plex Mono",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License 1.1. Clean monospace for grids.",
        foundry="IBM / Mike Abbink",
        url="https://fonts.google.com/specimen/IBM+Plex+Mono",
    ),
    # --------------- Accessibility ---------------
    "OpenDyslexic": FontLicenseInfo(
        font_name="OpenDyslexic",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License. Designed for readers with dyslexia.",
        foundry="Abbie Gonzalez",
        url="https://opendyslexic.org/",
    ),
    "Lexie Readable": FontLicenseInfo(
        font_name="Lexie Readable",
        safe=True,
        license_type="open_source",
        details="Free for commercial use. High readability for all ages.",
        foundry="K-Type",
        url="https://www.k-type.com/fonts/lexie-readable/",
    ),
    "Atkinson Hyperlegible": FontLicenseInfo(
        font_name="Atkinson Hyperlegible",
        safe=True,
        license_type="sil_ofl",
        details="SIL Open Font License. Designed for low-vision readers by Braille Institute.",
        foundry="Braille Institute / Applied Design Works",
        url="https://fonts.google.com/specimen/Atkinson+Hyperlegible",
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_font_license(font_name: str) -> dict[str, Any]:
    """Check whether a font is safe for commercial print publication.

    Parameters
    ----------
    font_name:
        The font name to look up (case-insensitive match attempted).

    Returns
    -------
    dict with keys: ``safe`` (bool), ``license_type``, ``details``.
    If the font is not found in the registry, ``safe`` is ``False``
    and details explain that manual verification is needed.
    """
    # Try exact match first
    info = SAFE_FONTS.get(font_name)

    # Try case-insensitive match
    if info is None:
        font_lower = font_name.lower()
        for name, entry in SAFE_FONTS.items():
            if name.lower() == font_lower:
                info = entry
                break

    if info is None:
        return {
            "safe": False,
            "license_type": "unknown",
            "details": (
                f"Font '{font_name}' is not in the safe font registry. "
                f"Verify its license permits commercial print use before publishing."
            ),
        }

    return {
        "safe": info.safe,
        "license_type": info.license_type,
        "details": info.details,
    }


def get_safe_font_list() -> list[dict[str, Any]]:
    """Return all fonts in the safe registry.

    Returns a list of dicts with ``font_name``, ``license_type``,
    ``details``, ``foundry``, and ``url``.
    """
    return [
        {
            "font_name": info.font_name,
            "license_type": info.license_type,
            "details": info.details,
            "foundry": info.foundry,
            "url": info.url,
        }
        for info in sorted(SAFE_FONTS.values(), key=lambda f: f.font_name)
    ]
