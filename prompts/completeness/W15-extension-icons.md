# W15: Chrome Extension Icons + Manifest Polish

## Files to create
- `extension/icons/icon16.png` — 16x16 icon
- `extension/icons/icon48.png` — 48x48 icon
- `extension/icons/icon128.png` — 128x128 icon

## Files to modify
- `extension/manifest.json` — Ensure icons are referenced

## Task

### 1. Create icon directory and placeholder icons

Since we can't generate actual PNG files programmatically in a text-only environment, create SVG icons that can be used as placeholders, or create a script to generate them:

Create `extension/icons/generate_icons.py`:
```python
"""Generate placeholder icons for the Chrome extension."""
from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs("extension/icons", exist_ok=True)

for size in (16, 48, 128):
    img = Image.new("RGBA", (size, size), (79, 70, 229, 255))  # Indigo background
    draw = ImageDraw.Draw(img)
    # Draw "SP" text centered
    text = "SP"
    font_size = size // 3
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (size - (bbox[2] - bbox[0])) // 2
    y = (size - (bbox[3] - bbox[1])) // 2
    draw.text((x, y), text, fill="white", font=font)
    img.save(f"extension/icons/icon{size}.png")
    print(f"Created icon{size}.png")
```

Alternatively, create simple 1-color PNG files using base64-encoded minimal PNGs.

### 2. Update manifest.json

Ensure the manifest references the icons:
```json
{
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

### 3. Verify manifest completeness

Read the manifest.json and ensure all required fields are present:
- name, version, description, manifest_version
- permissions, content_scripts, background
- icons, action (with default_icon, default_popup)
