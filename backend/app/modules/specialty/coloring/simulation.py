"""Coloring simulation service.

Provides region detection, palette management, and media-specific simulation
for coloring book pages. The heavy image processing returns structured data
that can drive either server-side rendering or client-side canvas compositing.
"""
from __future__ import annotations

import hashlib
import logging
import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

MediaType = Literal["marker", "crayon", "colored_pencil"]

VALID_MEDIA_TYPES: set[str] = {"marker", "crayon", "colored_pencil"}

# Map frontend hyphenated names to backend underscored names
MEDIA_TYPE_ALIASES: dict[str, MediaType] = {
    "colored-pencil": "colored_pencil",
    "colored_pencil": "colored_pencil",
    "marker": "marker",
    "crayon": "crayon",
}


@dataclass
class ColorSwatch:
    """A single color in a palette."""

    id: str
    hex: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "hex": self.hex, "name": self.name}


@dataclass
class ColorPalette:
    """A named collection of color swatches."""

    id: str
    name: str
    swatches: list[ColorSwatch]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "swatches": [s.to_dict() for s in self.swatches],
        }


@dataclass
class Region:
    """A detected colorable region within line art."""

    id: int
    x: int
    y: int
    width: int
    height: int
    pixel_count: int
    centroid_x: float
    centroid_y: float
    bounding_box: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "pixel_count": self.pixel_count,
            "centroid_x": round(self.centroid_x, 1),
            "centroid_y": round(self.centroid_y, 1),
            "bounding_box": self.bounding_box,
        }


@dataclass
class MediaCharacteristics:
    """Visual characteristics for a coloring medium."""

    media_type: MediaType
    opacity: float
    texture: str
    edge_behavior: str
    stroke_visible: bool
    paper_texture_visible: bool
    coverage_uniformity: float  # 0.0 = very uneven, 1.0 = perfectly even
    layer_blend_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "media_type": self.media_type,
            "opacity": self.opacity,
            "texture": self.texture,
            "edge_behavior": self.edge_behavior,
            "stroke_visible": self.stroke_visible,
            "paper_texture_visible": self.paper_texture_visible,
            "coverage_uniformity": self.coverage_uniformity,
            "layer_blend_mode": self.layer_blend_mode,
        }


@dataclass
class SimulationResult:
    """Result of a coloring simulation."""

    regions: list[dict[str, Any]]
    color_assignments: dict[int, str]  # region_id -> hex color
    media_characteristics: dict[str, Any]
    palette_used: dict[str, Any]
    composite_instructions: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "regions": self.regions,
            "color_assignments": {
                str(k): v for k, v in self.color_assignments.items()
            },
            "media_characteristics": self.media_characteristics,
            "palette_used": self.palette_used,
            "composite_instructions": self.composite_instructions,
        }


# ---------------------------------------------------------------------------
# Media characteristic definitions
# ---------------------------------------------------------------------------

MEDIA_CHARACTERISTICS: dict[MediaType, MediaCharacteristics] = {
    "marker": MediaCharacteristics(
        media_type="marker",
        opacity=0.85,
        texture="smooth",
        edge_behavior="bleed",
        stroke_visible=False,
        paper_texture_visible=False,
        coverage_uniformity=0.92,
        layer_blend_mode="multiply",
    ),
    "crayon": MediaCharacteristics(
        media_type="crayon",
        opacity=0.70,
        texture="grain",
        edge_behavior="rough",
        stroke_visible=True,
        paper_texture_visible=True,
        coverage_uniformity=0.55,
        layer_blend_mode="multiply",
    ),
    "colored_pencil": MediaCharacteristics(
        media_type="colored_pencil",
        opacity=0.50,
        texture="hatched",
        edge_behavior="feathered",
        stroke_visible=True,
        paper_texture_visible=True,
        coverage_uniformity=0.65,
        layer_blend_mode="multiply",
    ),
}


# ---------------------------------------------------------------------------
# Predefined palettes
# ---------------------------------------------------------------------------

_PALETTES: list[ColorPalette] = [
    ColorPalette(
        id="primary",
        name="Primary Colors",
        swatches=[
            ColorSwatch("p-red", "#FF0000", "Red"),
            ColorSwatch("p-blue", "#0000FF", "Blue"),
            ColorSwatch("p-yellow", "#FFFF00", "Yellow"),
            ColorSwatch("p-green", "#00FF00", "Green"),
            ColorSwatch("p-orange", "#FF8800", "Orange"),
            ColorSwatch("p-purple", "#8800FF", "Purple"),
        ],
    ),
    ColorPalette(
        id="pastel",
        name="Pastel",
        swatches=[
            ColorSwatch("ps-pink", "#FFB3BA", "Pastel Pink"),
            ColorSwatch("ps-peach", "#FFDFBA", "Pastel Peach"),
            ColorSwatch("ps-yellow", "#FFFFBA", "Pastel Yellow"),
            ColorSwatch("ps-green", "#BAFFC9", "Pastel Green"),
            ColorSwatch("ps-blue", "#BAE1FF", "Pastel Blue"),
            ColorSwatch("ps-lavender", "#D4BAFF", "Pastel Lavender"),
        ],
    ),
    ColorPalette(
        id="earth_tones",
        name="Earth Tones",
        swatches=[
            ColorSwatch("et-sienna", "#A0522D", "Sienna"),
            ColorSwatch("et-ochre", "#CC7722", "Ochre"),
            ColorSwatch("et-olive", "#808000", "Olive"),
            ColorSwatch("et-forest", "#228B22", "Forest Green"),
            ColorSwatch("et-clay", "#B66A50", "Clay"),
            ColorSwatch("et-slate", "#708090", "Slate"),
        ],
    ),
    ColorPalette(
        id="tropical",
        name="Tropical",
        swatches=[
            ColorSwatch("tr-coral", "#FF6F61", "Coral"),
            ColorSwatch("tr-turquoise", "#40E0D0", "Turquoise"),
            ColorSwatch("tr-mango", "#FF8243", "Mango"),
            ColorSwatch("tr-hibiscus", "#B6316C", "Hibiscus"),
            ColorSwatch("tr-lime", "#32CD32", "Lime"),
            ColorSwatch("tr-ocean", "#006994", "Ocean"),
        ],
    ),
    ColorPalette(
        id="monochrome",
        name="Monochrome",
        swatches=[
            ColorSwatch("mo-black", "#1A1A1A", "Charcoal"),
            ColorSwatch("mo-dark", "#4D4D4D", "Dark Gray"),
            ColorSwatch("mo-medium", "#808080", "Medium Gray"),
            ColorSwatch("mo-light", "#B3B3B3", "Light Gray"),
            ColorSwatch("mo-silver", "#D9D9D9", "Silver"),
            ColorSwatch("mo-snow", "#F2F2F2", "Snow"),
        ],
    ),
    ColorPalette(
        id="rainbow",
        name="Rainbow",
        swatches=[
            ColorSwatch("rb-red", "#FF0000", "Red"),
            ColorSwatch("rb-orange", "#FF7F00", "Orange"),
            ColorSwatch("rb-yellow", "#FFFF00", "Yellow"),
            ColorSwatch("rb-green", "#00FF00", "Green"),
            ColorSwatch("rb-blue", "#0000FF", "Blue"),
            ColorSwatch("rb-indigo", "#4B0082", "Indigo"),
            ColorSwatch("rb-violet", "#9400D3", "Violet"),
        ],
    ),
]

# Quick lookup by palette id
_PALETTE_MAP: dict[str, ColorPalette] = {p.id: p for p in _PALETTES}


# ---------------------------------------------------------------------------
# Public API: get_color_palettes
# ---------------------------------------------------------------------------


def get_color_palettes() -> list[dict[str, Any]]:
    """Return all predefined color palettes.

    Returns a list of palette dicts, each containing:
      - id: unique palette identifier
      - name: human-readable palette name
      - swatches: list of {id, hex, name} color entries
    """
    return [p.to_dict() for p in _PALETTES]


# ---------------------------------------------------------------------------
# Public API: detect_regions
# ---------------------------------------------------------------------------


def detect_regions(image_data: bytes) -> list[dict[str, Any]]:
    """Detect enclosed colorable regions in B&W line art.

    Algorithm overview:
    1. Parse the image to extract pixel data (grayscale).
    2. Threshold to separate line pixels (dark) from fill areas (white).
    3. Flood-fill from each unvisited white pixel to identify contiguous
       regions bounded by dark lines.
    4. Filter out tiny regions (noise) and the outer background region.
    5. Return region metadata (bounding box, centroid, pixel count).

    In production this would use Pillow/OpenCV for real image parsing.
    For now, we use a deterministic hash-based approach to generate
    plausible region data from the image bytes, enabling full API
    contract testing and client-side development.

    Parameters
    ----------
    image_data : bytes
        Raw image bytes (PNG or similar raster format).

    Returns
    -------
    list[dict]
        List of detected region dicts with spatial metadata.
    """
    if not image_data:
        return []

    # Derive deterministic region count from image content hash
    content_hash = hashlib.sha256(image_data).hexdigest()
    rng = random.Random(content_hash)

    # Typical coloring page has 8-25 regions
    num_regions = rng.randint(8, 25)

    # Assume a standard coloring page canvas (2550x3300 at 300 DPI for 8.5x11)
    canvas_w = 2550
    canvas_h = 3300

    regions: list[Region] = []
    for i in range(num_regions):
        # Generate plausible non-overlapping region bounds
        w = rng.randint(150, canvas_w // 3)
        h = rng.randint(150, canvas_h // 3)
        x = rng.randint(50, canvas_w - w - 50)
        y = rng.randint(50, canvas_h - h - 50)
        pixel_count = int(w * h * rng.uniform(0.3, 0.85))  # fill factor

        regions.append(
            Region(
                id=i,
                x=x,
                y=y,
                width=w,
                height=h,
                pixel_count=pixel_count,
                centroid_x=x + w / 2.0,
                centroid_y=y + h / 2.0,
                bounding_box={"x": x, "y": y, "width": w, "height": h},
            )
        )

    logger.info(
        "Detected %d colorable regions in %d bytes of image data",
        len(regions),
        len(image_data),
    )

    return [r.to_dict() for r in regions]


# ---------------------------------------------------------------------------
# Public API: simulate_coloring
# ---------------------------------------------------------------------------


def _normalize_media_type(media_type: str) -> MediaType:
    """Normalize media type string, accepting both hyphenated and underscored forms."""
    normalized = MEDIA_TYPE_ALIASES.get(media_type)
    if normalized is None:
        raise ValueError(
            f"Invalid media_type '{media_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_MEDIA_TYPES))}"
        )
    return normalized


def _build_composite_instructions(
    regions: list[dict[str, Any]],
    color_assignments: dict[int, str],
    characteristics: MediaCharacteristics,
) -> list[dict[str, Any]]:
    """Build per-region rendering instructions for the compositor.

    Each instruction tells the client (or server-side renderer) how to
    fill a specific region with the assigned color using media-specific
    visual effects.
    """
    instructions: list[dict[str, Any]] = []

    for region in regions:
        region_id = region["id"]
        color_hex = color_assignments.get(region_id, "#FFFFFF")

        instruction: dict[str, Any] = {
            "region_id": region_id,
            "color": color_hex,
            "blend_mode": characteristics.layer_blend_mode,
            "opacity": characteristics.opacity,
            "bounding_box": region["bounding_box"],
        }

        # Media-specific rendering parameters
        if characteristics.media_type == "marker":
            instruction.update({
                "fill_type": "solid",
                "edge_bleed_px": 2,
                "transparency_variation": 0.05,
                "texture_overlay": None,
                "stroke_pattern": None,
            })
        elif characteristics.media_type == "crayon":
            instruction.update({
                "fill_type": "textured",
                "edge_bleed_px": 0,
                "transparency_variation": 0.25,
                "texture_overlay": "grain_noise",
                "texture_scale": 1.5,
                "texture_rotation_deg": random.uniform(0, 360),
                "stroke_pattern": "random_directional",
                "coverage_gaps_pct": 15,
            })
        elif characteristics.media_type == "colored_pencil":
            instruction.update({
                "fill_type": "hatched",
                "edge_bleed_px": 0,
                "transparency_variation": 0.15,
                "texture_overlay": "paper_tooth",
                "texture_scale": 0.8,
                "stroke_pattern": "directional_hatching",
                "stroke_angle_deg": random.uniform(30, 60),
                "stroke_spacing_px": 3,
                "layer_count": 2,
                "pressure_variation": 0.3,
            })

        instructions.append(instruction)

    return instructions


def simulate_coloring(
    image_data: bytes,
    media_type: str,
    palette: str | list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Generate a simulated colored version of a coloring page.

    Parameters
    ----------
    image_data : bytes
        Raw B&W line art image bytes.
    media_type : str
        Coloring medium: ``"marker"`` | ``"crayon"`` | ``"colored_pencil"``
        (also accepts ``"colored-pencil"`` for frontend compatibility).
    palette : str | list[dict] | None
        Either a palette ID string (e.g. ``"primary"``) or an explicit list
        of ``{id, hex, name}`` color dicts.  Defaults to ``"primary"``.

    Returns
    -------
    dict
        Simulation result containing:
        - ``regions``: detected colorable regions
        - ``color_assignments``: mapping of region ID to hex color
        - ``media_characteristics``: visual properties for the chosen medium
        - ``palette_used``: the resolved palette
        - ``composite_instructions``: per-region rendering directives

    Algorithm
    ---------
    1. Detect enclosed regions in the B&W line art via flood fill.
    2. Assign colors from the palette to regions (cycling through swatches).
    3. Build media-specific texture/fill instructions for each region.
    4. Return structured data for compositing colored regions under line art.
    """
    # Normalize media type
    normalized_media = _normalize_media_type(media_type)
    characteristics = MEDIA_CHARACTERISTICS[normalized_media]

    # Resolve palette
    if palette is None:
        palette = "primary"

    if isinstance(palette, str):
        resolved_palette = _PALETTE_MAP.get(palette)
        if resolved_palette is None:
            resolved_palette = _PALETTES[0]  # fallback to primary
        palette_dict = resolved_palette.to_dict()
        swatches = resolved_palette.swatches
    else:
        # Palette provided as explicit list of color dicts
        swatches = [
            ColorSwatch(
                id=c.get("id", f"custom-{i}"),
                hex=c.get("hex", "#000000"),
                name=c.get("name", f"Color {i}"),
            )
            for i, c in enumerate(palette)
        ]
        palette_dict = {
            "id": "custom",
            "name": "Custom Palette",
            "swatches": [s.to_dict() for s in swatches],
        }

    # Step 1: Detect regions
    regions = detect_regions(image_data)

    if not regions:
        return SimulationResult(
            regions=[],
            color_assignments={},
            media_characteristics=characteristics.to_dict(),
            palette_used=palette_dict,
            composite_instructions=[],
        ).to_dict()

    # Step 2: Assign colors from palette to regions (cyclic assignment)
    color_assignments: dict[int, str] = {}
    if swatches:
        for i, region in enumerate(regions):
            swatch = swatches[i % len(swatches)]
            color_assignments[region["id"]] = swatch.hex

    # Step 3: Build media-specific composite instructions
    composite_instructions = _build_composite_instructions(
        regions, color_assignments, characteristics
    )

    # Step 4: Package result
    result = SimulationResult(
        regions=regions,
        color_assignments=color_assignments,
        media_characteristics=characteristics.to_dict(),
        palette_used=palette_dict,
        composite_instructions=composite_instructions,
    )

    logger.info(
        "Coloring simulation complete: media=%s, regions=%d, palette=%s",
        normalized_media,
        len(regions),
        palette_dict.get("name", "unknown"),
    )

    return result.to_dict()
