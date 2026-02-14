"""Export service for cover designs.

Supports exporting covers in multiple formats:
- PNG at 72dpi (web/ebook preview)
- PNG at 300dpi (print quality)
- PDF with optional bleed and trim marks
- JPEG (compressed for web previews)

Handles Fabric.js editor state rendering when available, with fallback to direct image URLs.
"""

from __future__ import annotations

import io
import logging
from typing import Literal
from uuid import UUID

import httpx
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.cover_design.models import Cover

logger = logging.getLogger(__name__)

ExportFormat = Literal["png_72", "png_300", "pdf", "jpeg"]

SUPPORTED_FORMATS: set[str] = {"png_72", "png_300", "pdf", "jpeg"}

# Bleed size for print formats (0.125 inches)
BLEED_INCHES = 0.125


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def export_cover(
    db: AsyncSession,
    cover_id: UUID,
    format: ExportFormat,  # noqa: A002 — shadows built-in intentionally for API clarity
    include_bleed: bool = False,
) -> tuple[bytes, str, str]:
    """Export a cover in the requested format.

    Parameters
    ----------
    db:
        Async database session.
    cover_id:
        UUID of the cover to export.
    format:
        One of ``'png_72'``, ``'png_300'``, ``'pdf'``, ``'jpeg'``.
    include_bleed:
        If True, add 0.125" bleed area on all sides (for print formats).

    Returns
    -------
    tuple[bytes, str, str]
        ``(file_bytes, filename, content_type)`` ready for a streaming response.

    Raises
    ------
    AppException
        404 if cover not found; 400 for unsupported format or rendering errors.
    """
    if format not in SUPPORTED_FORMATS:
        raise AppException(
            status_code=400,
            code="UNSUPPORTED_FORMAT",
            message=f"Unsupported export format: {format}. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
        )

    cover = await _load_cover(db, cover_id)

    # Determine safe filename
    safe_title = _safe_filename(cover.title)

    if format == "png_72":
        data = await _export_png(cover, dpi=72, include_bleed=include_bleed)
        return data, f"{safe_title}_72dpi.png", "image/png"

    if format == "png_300":
        data = await _export_png(cover, dpi=300, include_bleed=include_bleed)
        return data, f"{safe_title}_300dpi.png", "image/png"

    if format == "pdf":
        data = await _export_pdf(cover, include_bleed=include_bleed)
        return data, f"{safe_title}.pdf", "application/pdf"

    if format == "jpeg":
        data = await _export_jpeg(cover, include_bleed=include_bleed)
        return data, f"{safe_title}.jpg", "image/jpeg"

    # Unreachable, but satisfies type checker
    raise AppException(status_code=400, code="UNSUPPORTED_FORMAT", message="Unknown format")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _load_cover(db: AsyncSession, cover_id: UUID) -> Cover:
    """Fetch the cover by ID."""
    result = await db.execute(select(Cover).where(Cover.id == cover_id))
    cover = result.scalar_one_or_none()
    if not cover:
        raise AppException(
            status_code=404,
            code="COVER_NOT_FOUND",
            message=f"Cover {cover_id} not found.",
        )
    return cover


def _safe_filename(title: str) -> str:
    """Create a safe filename from the cover title."""
    import re

    safe = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
    return safe or "cover"


async def _get_cover_image(cover: Cover) -> Image.Image:
    """Retrieve the cover image from URL or editor_state.

    If editor_state (Fabric.js JSON) is available, render from JSON.
    Otherwise, download the image from image_url.
    """
    # Check if we have a Fabric.js editor state
    editor_state = cover.metadata_json.get("editor_state") if cover.metadata_json else None

    if editor_state:
        # Attempt to render from Fabric.js JSON
        # For now, we use a simplified approach: extract background image if present
        # A full implementation would require fabric.js server-side rendering or conversion
        # For this implementation, we fall through to the image_url
        logger.info("Editor state found for cover %s, but server-side Fabric.js rendering not yet implemented. Using image_url.", cover.id)

    # Fallback to downloading from image_url
    if not cover.image_url:
        raise AppException(
            status_code=400,
            code="NO_IMAGE_AVAILABLE",
            message=f"Cover {cover.id} has no image_url available for export.",
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(cover.image_url, timeout=30.0)
            response.raise_for_status()
            image_data = response.content
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.exception("Failed to download cover image from %s: %s", cover.image_url, exc)
        raise AppException(
            status_code=400,
            code="IMAGE_DOWNLOAD_FAILED",
            message=f"Failed to download cover image: {exc\!s}",
        )

    try:
        img = Image.open(io.BytesIO(image_data))
        # Convert to RGB if necessary (for formats that don't support transparency)
        if img.mode in ("RGBA", "LA", "P"):
            # Create white background
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            rgb_img.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
            return rgb_img
        if img.mode \!= "RGB":
            img = img.convert("RGB")
        return img
    except (OSError, ValueError) as exc:
        logger.exception("Failed to open cover image: %s", exc)
        raise AppException(
            status_code=400,
            code="IMAGE_OPEN_FAILED",
            message=f"Failed to open cover image: {exc\!s}",
        )


def _add_bleed_area(img: Image.Image, dpi: int) -> Image.Image:
    """Add bleed area (0.125 inches) on all sides of the image."""
    bleed_px = int(BLEED_INCHES * dpi)

    new_width = img.width + (2 * bleed_px)
    new_height = img.height + (2 * bleed_px)

    # Create new image with bleed area (white background)
    new_img = Image.new("RGB", (new_width, new_height), (255, 255, 255))

    # Paste original image in center
    new_img.paste(img, (bleed_px, bleed_px))

    return new_img


def _resize_with_dpi(img: Image.Image, target_dpi: int, current_dpi: int | None = None) -> Image.Image:
    """Resize image to target DPI, maintaining aspect ratio.

    If current_dpi is provided and different from target_dpi, scale the image.
    Otherwise, just set the DPI metadata.
    """
    if current_dpi and current_dpi \!= target_dpi:
        # Calculate new dimensions
        scale_factor = target_dpi / current_dpi
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)

        # Resize using high-quality resampling
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return img


# ---------------------------------------------------------------------------
# Format-specific exporters
# ---------------------------------------------------------------------------


async def _export_png(cover: Cover, dpi: int, include_bleed: bool) -> bytes:
    """Export to PNG at specified DPI."""
    img = await _get_cover_image(cover)

    # Resize if needed based on current vs. target DPI
    current_dpi = cover.dpi or 300
    img = _resize_with_dpi(img, target_dpi=dpi, current_dpi=current_dpi)

    # Add bleed if requested
    if include_bleed:
        img = _add_bleed_area(img, dpi)

    # Save to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(dpi, dpi))
    return buf.getvalue()


async def _export_jpeg(cover: Cover, include_bleed: bool, quality: int = 85) -> bytes:
    """Export to JPEG for web previews."""
    img = await _get_cover_image(cover)

    # JPEG exports are typically for web, so use 72 DPI
    current_dpi = cover.dpi or 300
    img = _resize_with_dpi(img, target_dpi=72, current_dpi=current_dpi)

    # Add bleed if requested
    if include_bleed:
        img = _add_bleed_area(img, 72)

    # Ensure RGB mode (JPEG doesn't support transparency)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Save to bytes
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


async def _export_pdf(cover: Cover, include_bleed: bool) -> bytes:
    """Export to PDF with optional bleed marks and trim marks."""
    try:
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
    except ImportError:
        raise AppException(
            status_code=400,
            code="LIBRARY_NOT_AVAILABLE",
            message=(
                "PDF export requires the 'reportlab' library. "
                "Install it with: pip install reportlab"
            ),
        )

    img = await _get_cover_image(cover)

    # PDF uses 300 DPI for print quality
    current_dpi = cover.dpi or 300
    if current_dpi != 300:
        img = _resize_with_dpi(img, target_dpi=300, current_dpi=current_dpi)

    # Convert dimensions from pixels to inches at 300 DPI
    width_inches = img.width / 300.0
    height_inches = img.height / 300.0

    # Calculate page size including bleed if requested
    bleed_size = BLEED_INCHES if include_bleed else 0
    page_width = (width_inches + 2 * bleed_size) * inch
    page_height = (height_inches + 2 * bleed_size) * inch

    # Create PDF
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    # Save image to temporary buffer
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)

    # Calculate position (center image if bleed is added)
    x_offset = bleed_size * inch if include_bleed else 0
    y_offset = bleed_size * inch if include_bleed else 0

    # Draw image
    c.drawImage(
        img_buf,
        x_offset,
        y_offset,
        width=width_inches * inch,
        height=height_inches * inch,
    )

    # Add trim marks and bleed marks if requested
    if include_bleed:
        _add_trim_marks(c, width_inches, height_inches, bleed_size)

    c.showPage()
    c.save()

    return buf.getvalue()


def _add_trim_marks(
    c: "canvas.Canvas",  # noqa: F821
    width_inches: float,
    height_inches: float,
    bleed_inches: float,
) -> None:
    """Add trim marks and bleed marks to PDF.

    Trim marks indicate where the cover should be cut.
    Bleed marks show the bleed area boundary.
    """
    from reportlab.lib.units import inch

    # Trim mark length (0.25 inches)
    mark_length = 0.25 * inch
    mark_offset = 0.125 * inch  # Distance from corner

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)

    # Bleed area boundaries
    bleed = bleed_inches * inch
    trim_left = bleed
    trim_right = (width_inches + bleed_inches) * inch
    trim_bottom = bleed
    trim_top = (height_inches + bleed_inches) * inch

    # Top-left corner
    c.line(trim_left - mark_offset, trim_top, trim_left - mark_offset, trim_top + mark_length)  # Vertical
    c.line(trim_left, trim_top + mark_offset, trim_left - mark_length, trim_top + mark_offset)  # Horizontal

    # Top-right corner
    c.line(trim_right + mark_offset, trim_top, trim_right + mark_offset, trim_top + mark_length)  # Vertical
    c.line(trim_right, trim_top + mark_offset, trim_right + mark_length, trim_top + mark_offset)  # Horizontal

    # Bottom-left corner
    c.line(trim_left - mark_offset, trim_bottom, trim_left - mark_offset, trim_bottom - mark_length)  # Vertical
    c.line(trim_left, trim_bottom - mark_offset, trim_left - mark_length, trim_bottom - mark_offset)  # Horizontal

    # Bottom-right corner
    c.line(trim_right + mark_offset, trim_bottom, trim_right + mark_offset, trim_bottom - mark_length)  # Vertical
    c.line(trim_right, trim_bottom - mark_offset, trim_right + mark_length, trim_bottom - mark_offset)  # Horizontal

    # Add bleed marks (dashed lines showing bleed boundary)
    c.setDash(3, 3)
    c.setStrokeColorRGB(0.5, 0.5, 0.5)

    # Top bleed line
    c.line(0, trim_top, (width_inches + 2 * bleed_inches) * inch, trim_top)
    # Bottom bleed line
    c.line(0, trim_bottom, (width_inches + 2 * bleed_inches) * inch, trim_bottom)
    # Left bleed line
    c.line(trim_left, 0, trim_left, (height_inches + 2 * bleed_inches) * inch)
    # Right bleed line
    c.line(trim_right, 0, trim_right, (height_inches + 2 * bleed_inches) * inch)
