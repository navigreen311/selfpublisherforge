"""
Device Preview System

Renders page previews scaled to exact device dimensions and DPI for
6 target devices (Kindle Fire HD 10/8, Kindle Paperwhite, iPad 10.2",
iPad Mini 8.3", iPhone 15).
"""

from typing import Any

# ---------------------------------------------------------------------------
# Device specifications
# ---------------------------------------------------------------------------

DEVICE_SPECS: dict[str, dict[str, Any]] = {
    "kindle_fire_hd_10": {
        "name": "Kindle Fire HD 10",
        "width": 1920,
        "height": 1200,
        "dpi": 224,
        "diagonal_inches": 10.1,
        "aspect_ratio": "16:10",
        "platform": "kindle",
        "supports_fixed_layout": True,
        "supports_read_aloud": True,
        "supports_text_popup": True,
        "frame_color": "#232F3E",
        "bezel_width": 24,
    },
    "kindle_fire_hd_8": {
        "name": "Kindle Fire HD 8",
        "width": 1280,
        "height": 800,
        "dpi": 189,
        "diagonal_inches": 8.0,
        "aspect_ratio": "16:10",
        "platform": "kindle",
        "supports_fixed_layout": True,
        "supports_read_aloud": True,
        "supports_text_popup": True,
        "frame_color": "#232F3E",
        "bezel_width": 20,
    },
    "kindle_paperwhite": {
        "name": "Kindle Paperwhite",
        "width": 1236,
        "height": 1648,
        "dpi": 300,
        "diagonal_inches": 6.8,
        "aspect_ratio": "3:4",
        "platform": "kindle",
        "supports_fixed_layout": True,
        "supports_read_aloud": False,
        "supports_text_popup": True,
        "frame_color": "#1A1A2E",
        "bezel_width": 16,
        "grayscale": True,
    },
    "ipad_10_2": {
        "name": 'iPad 10.2"',
        "width": 2160,
        "height": 1620,
        "dpi": 264,
        "diagonal_inches": 10.2,
        "aspect_ratio": "4:3",
        "platform": "apple",
        "supports_fixed_layout": True,
        "supports_read_aloud": True,
        "supports_text_popup": True,
        "frame_color": "#C0C0C0",
        "bezel_width": 28,
    },
    "ipad_mini_8_3": {
        "name": 'iPad Mini 8.3"',
        "width": 2266,
        "height": 1488,
        "dpi": 326,
        "diagonal_inches": 8.3,
        "aspect_ratio": "3:2",
        "platform": "apple",
        "supports_fixed_layout": True,
        "supports_read_aloud": True,
        "supports_text_popup": True,
        "frame_color": "#E0E0E0",
        "bezel_width": 20,
    },
    "iphone_15": {
        "name": "iPhone 15",
        "width": 2556,
        "height": 1179,
        "dpi": 460,
        "diagonal_inches": 6.1,
        "aspect_ratio": "19.5:9",
        "platform": "apple",
        "supports_fixed_layout": True,
        "supports_read_aloud": True,
        "supports_text_popup": True,
        "frame_color": "#1C1C1E",
        "bezel_width": 12,
        "has_notch": True,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_scale(source_w: int, source_h: int, target_w: int, target_h: int) -> dict:
    """Compute scaling info to fit source dimensions within target."""
    scale_x = target_w / source_w if source_w else 1.0
    scale_y = target_h / source_h if source_h else 1.0
    scale = min(scale_x, scale_y)

    rendered_w = int(source_w * scale)
    rendered_h = int(source_h * scale)
    offset_x = (target_w - rendered_w) // 2
    offset_y = (target_h - rendered_h) // 2

    return {
        "scale_factor": round(scale, 4),
        "rendered_width": rendered_w,
        "rendered_height": rendered_h,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "letterboxed": scale_x != scale_y,
    }


def _compute_text_readability(font_size: int, scale_factor: float, dpi: int) -> dict:
    """Evaluate whether text will be readable on the target device."""
    scaled_size = font_size * scale_factor
    # Convert px to physical points at device DPI
    physical_pt = (scaled_size / dpi) * 72
    readable = physical_pt >= 6.0  # 6pt is minimum readable
    needs_popup = physical_pt < 10.0

    return {
        "original_font_size_px": font_size,
        "scaled_font_size_px": round(scaled_size, 1),
        "physical_size_pt": round(physical_pt, 1),
        "is_readable": readable,
        "needs_text_popup": needs_popup,
        "recommendation": (
            "OK"
            if readable and not needs_popup
            else "Text pop-up recommended"
            if readable
            else "Text too small -- increase font size or enable pop-up"
        ),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_preview(page_data: dict, device: str) -> dict:
    """
    Scale and render a single page for a specific device.

    Parameters
    ----------
    page_data : dict
        Page content.  Expected keys: ``width``, ``height`` (source
        dimensions in px), ``text_content``, ``text_font_size``,
        ``image_url``, ``layout``.
    device : str
        Device key from ``DEVICE_SPECS`` (e.g. ``"kindle_fire_hd_10"``).

    Returns
    -------
    dict
        Preview result with scaling info, device frame data, readability
        assessment, and rendering parameters.

    Raises
    ------
    ValueError
        If *device* is not a recognised device key.
    """
    if device not in DEVICE_SPECS:
        raise ValueError(f"Unknown device '{device}'. " f"Valid devices: {', '.join(DEVICE_SPECS.keys())}")

    spec = DEVICE_SPECS[device]
    source_w = page_data.get("width", 1024)
    source_h = page_data.get("height", 1366)
    target_w = spec["width"]
    target_h = spec["height"]

    scaling = _compute_scale(source_w, source_h, target_w, target_h)

    # Text readability check
    font_size = page_data.get("text_font_size", 18)
    readability = _compute_text_readability(font_size, scaling["scale_factor"], spec["dpi"])

    # Grayscale conversion needed?
    is_grayscale = spec.get("grayscale", False)

    return {
        "device": device,
        "device_name": spec["name"],
        "device_dimensions": {
            "width": target_w,
            "height": target_h,
            "dpi": spec["dpi"],
        },
        "source_dimensions": {"width": source_w, "height": source_h},
        "scaling": scaling,
        "text_readability": readability,
        "render_params": {
            "grayscale": is_grayscale,
            "image_url": page_data.get("image_url"),
            "text_content": page_data.get("text_content", ""),
            "layout": page_data.get("layout", "full_bleed"),
        },
        "device_frame": {
            "frame_color": spec["frame_color"],
            "bezel_width": spec["bezel_width"],
            "has_notch": spec.get("has_notch", False),
            "platform": spec["platform"],
        },
        "capabilities": {
            "fixed_layout": spec["supports_fixed_layout"],
            "read_aloud": spec["supports_read_aloud"],
            "text_popup": spec["supports_text_popup"],
        },
    }


def generate_all_previews(page_data: dict) -> dict:
    """
    Generate previews for all 6 supported devices.

    Parameters
    ----------
    page_data : dict
        Page content (same format as :func:`generate_preview`).

    Returns
    -------
    dict
        ``{"previews": {device_key: preview_dict, ...},
        "summary": {"total_devices", "readable_on", "popup_needed_on",
        "warnings"}}``
    """
    previews: dict[str, dict] = {}
    readable_on: list[str] = []
    popup_needed: list[str] = []
    warnings: list[str] = []

    for device_key in DEVICE_SPECS:
        preview = generate_preview(page_data, device_key)
        previews[device_key] = preview

        readability = preview["text_readability"]
        if readability["is_readable"]:
            readable_on.append(device_key)
        else:
            warnings.append(f"Text not readable on {preview['device_name']} " f"({readability['physical_size_pt']}pt)")
        if readability["needs_text_popup"]:
            popup_needed.append(device_key)

    return {
        "previews": previews,
        "summary": {
            "total_devices": len(DEVICE_SPECS),
            "readable_on": readable_on,
            "popup_needed_on": popup_needed,
            "warnings": warnings,
        },
    }
