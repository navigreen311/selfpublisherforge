"""Generate placeholder icons for the Chrome extension.

Creates solid indigo (#4F46E5) PNG icons at 16x16, 48x48, and 128x128.
Uses only the Python standard library (struct + zlib) — no PIL/Pillow needed.
"""
import struct
import zlib
import os


def create_png(width, height, r, g, b):
    """Create a minimal valid PNG file with a solid color fill."""

    def chunk(chunk_type, data):
        c = chunk_type + data
        return (
            struct.pack(">I", len(data))
            + c
            + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        )

    # Build raw pixel data (filter byte 0x00 + RGB triplets per row)
    raw = b""
    for y in range(height):
        raw += b"\x00" + bytes([r, g, b]) * width

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def main():
    # Indigo / purple brand color: #4F46E5
    R, G, B = 0x4F, 0x46, 0xE5

    script_dir = os.path.dirname(os.path.abspath(__file__))

    for size in (16, 48, 128):
        png_bytes = create_png(size, size, R, G, B)
        out_path = os.path.join(script_dir, f"icon{size}.png")
        with open(out_path, "wb") as f:
            f.write(png_bytes)
        print(f"Created icon{size}.png  ({len(png_bytes)} bytes)")


if __name__ == "__main__":
    main()
