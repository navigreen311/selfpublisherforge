"""
Advanced Layout Protection

Safe-zone heatmap overlay, gutter collision detection, and auto-reflow
for alternate trim sizes.
"""


# ---------------------------------------------------------------------------
# Standard print zone definitions (in inches)
# ---------------------------------------------------------------------------

_BLEED_SIZE = 0.125  # Standard KDP bleed
_SAFE_MARGIN = 0.375  # Minimum safe zone from trim edge
_GUTTER_MARGIN = 0.625  # Inside margin near spine

# Zone colours (CSS / hex)
ZONE_COLORS = {
    "bleed": {"color": "#FF0000", "opacity": 0.25, "label": "Bleed Zone"},
    "trim": {"color": "#0000FF", "opacity": 0.20, "label": "Trim Line"},
    "safe": {"color": "#00FF00", "opacity": 0.15, "label": "Safe Zone"},
    "gutter": {"color": "#FFFF00", "opacity": 0.25, "label": "Gutter Zone"},
}

# Common KDP trim sizes (width x height in inches)
TRIM_SIZES: dict[str, dict[str, float]] = {
    "5x8": {"width": 5.0, "height": 8.0},
    "5.5x8.5": {"width": 5.5, "height": 8.5},
    "6x9": {"width": 6.0, "height": 9.0},
    "7x10": {"width": 7.0, "height": 10.0},
    "8x10": {"width": 8.0, "height": 10.0},
    "8.5x8.5": {"width": 8.5, "height": 8.5},
    "8.5x11": {"width": 8.5, "height": 11.0},
    "10x8": {"width": 10.0, "height": 8.0},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _inches_to_px(inches: float, dpi: int = 300) -> float:
    return inches * dpi


def _compute_zones(trim_width: float, trim_height: float, dpi: int = 300) -> dict:
    """Compute zone rectangles in pixels for a given trim size."""
    tw = _inches_to_px(trim_width, dpi)
    th = _inches_to_px(trim_height, dpi)
    bleed = _inches_to_px(_BLEED_SIZE, dpi)
    safe = _inches_to_px(_SAFE_MARGIN, dpi)
    gutter = _inches_to_px(_GUTTER_MARGIN, dpi)

    # Full page includes bleed on all sides
    full_w = tw + 2 * bleed
    full_h = th + 2 * bleed

    return {
        "full_page": {"width": full_w, "height": full_h},
        "bleed_zone": {
            "outer": {"x": 0, "y": 0, "width": full_w, "height": full_h},
            "inner": {"x": bleed, "y": bleed, "width": tw, "height": th},
        },
        "trim_line": {"x": bleed, "y": bleed, "width": tw, "height": th},
        "safe_zone": {
            "x": bleed + safe,
            "y": bleed + safe,
            "width": tw - 2 * safe,
            "height": th - 2 * safe,
        },
        "gutter_zone": {
            "x": bleed,
            "y": bleed,
            "width": gutter,
            "height": th,
        },
    }


def _rect_overlap(r1: dict, r2: dict) -> bool:
    """Check if two rectangles overlap (keys: x, y, width, height)."""
    return not (
        r1["x"] + r1["width"] <= r2["x"]
        or r2["x"] + r2["width"] <= r1["x"]
        or r1["y"] + r1["height"] <= r2["y"]
        or r2["y"] + r2["height"] <= r1["y"]
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_safe_zone_heatmap(page_data: dict, trim_size: str) -> dict:
    """
    Generate a colour-coded safe-zone heatmap overlay for the given page.

    Zones:
    - **Bleed** (red): content that will be cut off
    - **Trim** (blue): the cut line
    - **Safe** (green): content guaranteed visible
    - **Gutter** (yellow): near-spine area, risk of hiding in fold

    Also detects faces and text elements that fall outside the safe zone.

    Parameters
    ----------
    page_data : dict
        Must include ``elements`` list (each element has ``type``,
        ``x``, ``y``, ``width``, ``height``).  Optional ``dpi``
        (default 300).
    trim_size : str
        Key from ``TRIM_SIZES`` or a ``"WxH"`` string in inches.

    Returns
    -------
    dict
        Zone definitions, element overlay positions, and warnings.
    """
    dpi = page_data.get("dpi", 300)

    # Parse trim size
    if trim_size in TRIM_SIZES:
        ts = TRIM_SIZES[trim_size]
    else:
        parts = trim_size.lower().replace("x", " ").split()
        ts = {"width": float(parts[0]), "height": float(parts[1])}

    zones = _compute_zones(ts["width"], ts["height"], dpi)
    safe_rect = zones["safe_zone"]
    gutter_rect = zones["gutter_zone"]

    # Analyse elements for zone violations
    elements = page_data.get("elements", [])
    overlays: list[dict] = []
    warnings: list[dict] = []

    for elem in elements:
        elem_rect = {
            "x": elem.get("x", 0),
            "y": elem.get("y", 0),
            "width": elem.get("width", 0),
            "height": elem.get("height", 0),
        }

        in_safe = (
            elem_rect["x"] >= safe_rect["x"]
            and elem_rect["y"] >= safe_rect["y"]
            and elem_rect["x"] + elem_rect["width"]
            <= safe_rect["x"] + safe_rect["width"]
            and elem_rect["y"] + elem_rect["height"]
            <= safe_rect["y"] + safe_rect["height"]
        )

        in_gutter = _rect_overlap(elem_rect, gutter_rect)
        in_bleed = not (
            elem_rect["x"] >= zones["trim_line"]["x"]
            and elem_rect["y"] >= zones["trim_line"]["y"]
            and elem_rect["x"] + elem_rect["width"]
            <= zones["trim_line"]["x"] + zones["trim_line"]["width"]
            and elem_rect["y"] + elem_rect["height"]
            <= zones["trim_line"]["y"] + zones["trim_line"]["height"]
        )

        zone = "safe" if in_safe else "gutter" if in_gutter else "bleed" if in_bleed else "trim"

        overlay = {
            "element_type": elem.get("type", "unknown"),
            "position": elem_rect,
            "zone": zone,
            "zone_color": ZONE_COLORS[zone]["color"],
        }
        overlays.append(overlay)

        if zone != "safe":
            severity = "critical" if zone == "bleed" else "warning"
            warnings.append(
                {
                    "element_type": elem.get("type", "unknown"),
                    "zone": zone,
                    "severity": severity,
                    "message": (
                        f"{elem.get('type', 'Element')} is in the {zone} zone "
                        f"and may be cut off or hidden in the fold."
                    ),
                    "suggestion": (
                        f"Move {elem.get('type', 'element')} at least "
                        f"{_SAFE_MARGIN}in from the trim edge."
                    ),
                }
            )

    return {
        "trim_size": {"width": ts["width"], "height": ts["height"]},
        "dpi": dpi,
        "zones": {
            name: {
                **ZONE_COLORS[name],
                "rect": zones.get(f"{name}_zone", zones.get(f"{name}_line")),
            }
            for name in ("bleed", "trim", "safe", "gutter")
        },
        "element_overlays": overlays,
        "warnings": warnings,
        "total_elements": len(elements),
        "elements_in_safe_zone": sum(1 for o in overlays if o["zone"] == "safe"),
        "elements_at_risk": sum(1 for o in overlays if o["zone"] != "safe"),
    }


def check_gutter_collision(page_data: dict, spine_width: float) -> list[dict]:
    """
    Detect faces and text elements that are too close to the fold/gutter.

    Parameters
    ----------
    page_data : dict
        Must include ``elements`` list with ``type``, ``x``, ``y``,
        ``width``, ``height``.  Optional ``dpi`` (default 300).
    spine_width : float
        Spine width in inches.

    Returns
    -------
    list[dict]
        List of collision results, each with ``element``, ``distance_from_gutter``,
        ``collision``, ``auto_shift_suggestion``.
    """
    dpi = page_data.get("dpi", 300)
    gutter_px = _inches_to_px(_GUTTER_MARGIN + spine_width * 0.5, dpi)
    min_safe_px = _inches_to_px(0.5, dpi)  # 0.5 inches from spine

    elements = page_data.get("elements", [])
    collisions: list[dict] = []

    for elem in elements:
        elem_type = elem.get("type", "unknown")
        # Only check faces and text -- the critical content types
        if elem_type not in ("face", "text", "heading", "caption"):
            continue

        elem_x = elem.get("x", 0)
        elem_right = elem_x + elem.get("width", 0)

        # Check left-side gutter (for right-hand pages / recto)
        distance_left = elem_x
        # Check right-side gutter (for left-hand pages / verso)
        page_width = page_data.get("page_width", _inches_to_px(8.5, dpi))
        distance_right = page_width - elem_right

        min_distance = min(distance_left, distance_right)
        is_collision = min_distance < min_safe_px

        shift_amount = 0.0
        shift_direction = ""
        if is_collision:
            shift_amount = round((min_safe_px - min_distance) / dpi, 3)
            shift_direction = "right" if distance_left < distance_right else "left"

        collisions.append(
            {
                "element": {
                    "type": elem_type,
                    "x": elem_x,
                    "y": elem.get("y", 0),
                    "width": elem.get("width", 0),
                    "height": elem.get("height", 0),
                },
                "distance_from_gutter_px": round(min_distance, 1),
                "distance_from_gutter_inches": round(min_distance / dpi, 3),
                "min_safe_distance_inches": round(min_safe_px / dpi, 3),
                "collision": is_collision,
                "severity": (
                    "critical"
                    if is_collision and elem_type == "face"
                    else "warning"
                    if is_collision
                    else "ok"
                ),
                "auto_shift_suggestion": (
                    {
                        "direction": shift_direction,
                        "amount_inches": shift_amount,
                        "amount_px": round(shift_amount * dpi),
                    }
                    if is_collision
                    else None
                ),
            }
        )

    return collisions


def auto_reflow(book_data: dict, target_trim_size: str) -> dict:
    """
    Convert a book between trim sizes, repositioning text and scaling
    illustrations proportionally.

    Parameters
    ----------
    book_data : dict
        Full book data with ``trim_size`` (current), ``pages`` list.
        Each page has ``elements`` with absolute positions and sizes.
    target_trim_size : str
        Target trim size key from ``TRIM_SIZES`` or ``"WxH"`` string.

    Returns
    -------
    dict
        Reflowed book data with ``pages`` containing repositioned
        elements, plus a ``reflow_report`` summarising changes.
    """
    # Parse source trim size
    source_ts_key = book_data.get("trim_size", "8.5x11")
    if source_ts_key in TRIM_SIZES:
        source = TRIM_SIZES[source_ts_key]
    else:
        sp = source_ts_key.lower().replace("x", " ").split()
        source = {"width": float(sp[0]), "height": float(sp[1])}

    # Parse target trim size
    if target_trim_size in TRIM_SIZES:
        target = TRIM_SIZES[target_trim_size]
    else:
        tp = target_trim_size.lower().replace("x", " ").split()
        target = {"width": float(tp[0]), "height": float(tp[1])}

    scale_x = target["width"] / source["width"]
    scale_y = target["height"] / source["height"]

    dpi = book_data.get("dpi", 300)
    source_w_px = _inches_to_px(source["width"], dpi)
    source_h_px = _inches_to_px(source["height"], dpi)
    target_w_px = _inches_to_px(target["width"], dpi)
    target_h_px = _inches_to_px(target["height"], dpi)

    reflowed_pages: list[dict] = []
    warnings: list[str] = []
    changes_count = 0

    for page_idx, page in enumerate(book_data.get("pages", [])):
        new_elements: list[dict] = []

        for elem in page.get("elements", []):
            new_elem = dict(elem)
            elem_type = elem.get("type", "unknown")

            if elem_type in ("illustration", "image", "photo"):
                # Scale illustrations proportionally using uniform scale
                uniform_scale = min(scale_x, scale_y)
                new_elem["x"] = round(elem.get("x", 0) * scale_x)
                new_elem["y"] = round(elem.get("y", 0) * scale_y)
                new_elem["width"] = round(elem.get("width", 0) * uniform_scale)
                new_elem["height"] = round(elem.get("height", 0) * uniform_scale)

                # Re-centre if aspect ratio changed
                avail_w = target_w_px
                if new_elem["width"] < avail_w:
                    new_elem["x"] = round((avail_w - new_elem["width"]) / 2)
            else:
                # Text elements: reposition, adjust font if needed
                new_elem["x"] = round(elem.get("x", 0) * scale_x)
                new_elem["y"] = round(elem.get("y", 0) * scale_y)
                new_elem["width"] = round(elem.get("width", 0) * scale_x)
                new_elem["height"] = round(elem.get("height", 0) * scale_y)

                # Scale font size but clamp to minimum
                original_font = elem.get("font_size", 18)
                scaled_font = round(original_font * min(scale_x, scale_y))
                new_elem["font_size"] = max(scaled_font, 12)

                if scaled_font < 12:
                    warnings.append(
                        f"Page {page_idx + 1}: text font scaled to "
                        f"{scaled_font}px, clamped to 12px minimum."
                    )

            # Safe-zone check on reflowed element
            safe_margin_px = _inches_to_px(_SAFE_MARGIN, dpi)
            if new_elem["x"] < safe_margin_px or new_elem["y"] < safe_margin_px:
                new_elem["x"] = max(new_elem["x"], round(safe_margin_px))
                new_elem["y"] = max(new_elem["y"], round(safe_margin_px))
                warnings.append(
                    f"Page {page_idx + 1}: {elem_type} repositioned into safe zone."
                )

            new_elements.append(new_elem)
            changes_count += 1

        reflowed_pages.append({**page, "elements": new_elements})

    return {
        "trim_size": target_trim_size,
        "dimensions": {
            "width_inches": target["width"],
            "height_inches": target["height"],
            "width_px": target_w_px,
            "height_px": target_h_px,
        },
        "scale_factors": {"x": round(scale_x, 4), "y": round(scale_y, 4)},
        "pages": reflowed_pages,
        "reflow_report": {
            "source_trim": source_ts_key,
            "target_trim": target_trim_size,
            "total_pages": len(reflowed_pages),
            "total_elements_repositioned": changes_count,
            "warnings": warnings,
            "warnings_count": len(warnings),
        },
    }
