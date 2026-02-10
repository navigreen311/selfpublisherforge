"""Generate extension icons for the SelfPublisherForge Chrome extension.

Creates modern flat-design PNG icons with a book-and-quill motif.
Uses Pillow (PIL) to draw vector-like shapes at 16x16, 48x48, and 128x128.

    pip install Pillow
    python generate_icons.py
"""

import os
import math

from PIL import Image, ImageDraw


# Brand colours
BG_COLOR = (0x1E, 0x40, 0xAF)  # Deep blue  #1E40AF
ICON_COLOR = (255, 255, 255)     # White icon elements
SHADOW_COLOR = (0x15, 0x30, 0x8B)  # Slightly darker blue for depth


def _draw_rounded_rect(draw, xy, radius, fill):
    """Draw a filled rounded rectangle (compatible with older Pillow versions)."""
    x0, y0, x1, y1 = xy
    r = radius
    # Four corner circles
    draw.ellipse([x0, y0, x0 + 2 * r, y0 + 2 * r], fill=fill)
    draw.ellipse([x1 - 2 * r, y0, x1, y0 + 2 * r], fill=fill)
    draw.ellipse([x0, y1 - 2 * r, x0 + 2 * r, y1], fill=fill)
    draw.ellipse([x1 - 2 * r, y1 - 2 * r, x1, y1], fill=fill)
    # Two overlapping rectangles
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)


def _draw_book(draw, cx, cy, size, color):
    """Draw a simple open-book silhouette centred at (cx, cy).

    The book is drawn as two rectangular "pages" angled slightly apart
    with a centre spine line.
    """
    # Book dimensions relative to the icon area
    half_w = size * 0.32
    half_h = size * 0.28
    spine_w = max(1, size * 0.02)

    # Left page
    left_page = [
        cx - half_w, cy - half_h,
        cx - spine_w, cy + half_h,
    ]
    draw.rectangle(left_page, fill=color)

    # Right page
    right_page = [
        cx + spine_w, cy - half_h,
        cx + half_w, cy + half_h,
    ]
    draw.rectangle(right_page, fill=color)

    # Page lines (give the illusion of text) -- only on larger sizes
    if size >= 40:
        line_color = BG_COLOR
        line_h = max(1, round(size * 0.015))
        num_lines = 4
        for i in range(num_lines):
            frac = 0.25 + 0.14 * i
            ly = cy - half_h + (half_h * 2) * frac
            # Left page lines
            draw.rectangle(
                [cx - half_w + size * 0.04, ly,
                 cx - spine_w - size * 0.04, ly + line_h],
                fill=line_color,
            )
            # Right page lines
            draw.rectangle(
                [cx + spine_w + size * 0.04, ly,
                 cx + half_w - size * 0.04, ly + line_h],
                fill=line_color,
            )


def _draw_quill(draw, cx, cy, size, color):
    """Draw a simplified quill pen (diagonal feather + nib) above the book."""
    # The quill sits at an angle leaning to the upper-right
    # We draw it as a polygon (elongated triangle / feather shape)
    # plus a small nib tip.

    length = size * 0.38
    width = size * 0.08

    # Angle: roughly 40 degrees from vertical, tilted right
    angle = math.radians(-40)

    # Tip position (lower-left, near the book spine)
    tip_x = cx + size * 0.02
    tip_y = cy + size * 0.05

    # Top of the quill
    top_x = tip_x + length * math.sin(angle)
    top_y = tip_y - length * math.cos(angle)

    # Perpendicular offsets for width
    perp_x = width * math.cos(angle)
    perp_y = width * math.sin(angle)

    # Feather polygon (tapers from top to tip)
    feather = [
        (top_x - perp_x, top_y - perp_y),
        (top_x + perp_x, top_y + perp_y),
        (tip_x, tip_y),
    ]
    draw.polygon(feather, fill=color)

    # Nib: small triangle extending below the tip
    nib_len = size * 0.06
    nib_x = tip_x + nib_len * math.sin(angle)
    nib_y = tip_y - nib_len * math.cos(angle) + nib_len * 1.6
    nib_w = max(1, size * 0.015)
    nib = [
        (tip_x - nib_w, tip_y),
        (tip_x + nib_w, tip_y),
        (nib_x, nib_y),
    ]
    draw.polygon(nib, fill=color)


def generate_icon(size):
    """Generate a single icon at the given pixel size and return an Image."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # --- Rounded-rectangle background ---
    radius = max(2, int(size * 0.18))
    _draw_rounded_rect(draw, (0, 0, size - 1, size - 1), radius, BG_COLOR)

    # Centre of icon
    cx = size / 2
    cy = size / 2 + size * 0.06  # nudge book slightly below centre

    # --- Draw book ---
    _draw_book(draw, cx, cy, size, ICON_COLOR)

    # --- Draw quill ---
    # Position quill centre slightly above and to the right of the book
    qx = cx + size * 0.12
    qy = cy - size * 0.22
    _draw_quill(draw, qx, qy, size, ICON_COLOR)

    return img


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    for size in (16, 48, 128):
        img = generate_icon(size)
        out_path = os.path.join(script_dir, f"icon{size}.png")
        img.save(out_path, "PNG")
        file_size = os.path.getsize(out_path)
        print(f"Created icon{size}.png  ({file_size} bytes)")


if __name__ == "__main__":
    main()
