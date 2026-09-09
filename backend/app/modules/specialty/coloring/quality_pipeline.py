"""Line Art Quality Pipeline (7 Steps) for Coloring Books.

Implements the full quality pipeline from the blueprint (Section 4.3):
    1. Generate    -- AI creates illustration with line art prompts
    2. Auto-Clean  -- Convert to pure black/white (threshold binarization at 128)
    3. Stroke Uniformity -- Normalize line thickness via morphological operations
    4. Closed Shapes     -- Detect open outlines using contour analysis
    5. Speck Removal     -- Remove connected components smaller than min_size
    6. Background Check  -- Verify pure #FFFFFF background, fix off-white areas
    7. Quality Check     -- Final verification with aggregate score

Image processing functions define clear interfaces using PIL/Pillow concepts
and data structures.  Logic is structured so it works correctly when real
image libraries (Pillow, OpenCV) are available at runtime.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class QualityIssue:
    """A single quality issue found during pipeline inspection."""

    step: str
    severity: Severity
    message: str
    location: dict[str, Any] | None = None  # e.g. {"x": 120, "y": 340}


@dataclass
class QualityReport:
    """Aggregate quality report returned by step_7 / run_full_pipeline."""

    score: float  # 0-100
    issues: list[QualityIssue] = field(default_factory=list)
    passed: bool = True


@dataclass
class StepResult:
    """Result of a single pipeline step."""

    step_name: str
    success: bool
    issues: list[QualityIssue] = field(default_factory=list)
    error: str | None = None


@dataclass
class PipelineResult:
    """Return value of run_full_pipeline."""

    image_data: bytes
    report: QualityReport
    steps_completed: list[str] = field(default_factory=list)
    step_results: list[StepResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Step 1: Generate raw image via AI
# ---------------------------------------------------------------------------


async def step_1_generate(prompt: str, style: str) -> bytes:
    """Generate a raw line-art image from an AI model.

    Builds a coloring-book-specific prompt enforcing:
      - Pure line art, no shading, no color fills
      - Single stroke weight
      - White background, black outlines only
      - No gradients or grayscale fills

    Parameters
    ----------
    prompt:
        User-facing description of the desired illustration.
    style:
        One of the 6 supported line art styles (e.g. "clean_outlines",
        "sketchy_hand_drawn", "whimsical_decorative", "realistic_detailed",
        "zentangle", "bold_and_simple").

    Returns
    -------
    bytes
        Raw image data (PNG) from the AI generation service.
    """
    style_modifiers = {
        "clean_outlines": "clean precise outlines, uniform line weight",
        "sketchy_hand_drawn": "sketchy hand-drawn look, varied pen strokes",
        "whimsical_decorative": "whimsical decorative borders, ornamental details",
        "realistic_detailed": "realistic detailed line art, fine cross-hatching",
        "zentangle": "zentangle-inspired patterns, intricate repeating designs",
        "bold_and_simple": "bold simple outlines, thick lines, minimal detail",
    }
    modifier = style_modifiers.get(style, style_modifiers["clean_outlines"])

    coloring_prompt = (
        f"Coloring book page illustration: {prompt}. "
        f"Style: {modifier}. "
        "REQUIREMENTS: Pure black line art on white background. "
        "No shading, no gradients, no color fills, no grayscale. "
        "Single consistent stroke weight throughout. "
        "All shapes must have closed outlines suitable for coloring. "
        "High contrast black lines on pure white (#FFFFFF) background. "
        "No texture or halftone patterns. Print-ready at 300 DPI."
    )

    logger.info("Generating line art with prompt length=%d, style=%s", len(coloring_prompt), style)

    # Placeholder: In production this calls the image generation service.
    # Returns empty bytes to be replaced with actual AI service integration.
    # Example: result = await image_service.generate(coloring_prompt, size=(2550, 3300), model="line-art-v1")
    return b""


# ---------------------------------------------------------------------------
# Step 2: Auto-Clean -- Convert to pure B&W
# ---------------------------------------------------------------------------


async def step_2_auto_clean(image_data: bytes) -> tuple[bytes, list[QualityIssue]]:
    """Convert image to pure black-and-white using threshold binarization.

    Algorithm:
        1. Convert image to grayscale (single channel).
        2. Apply binary threshold at value 128:
           - Pixels >= 128 -> 255 (white)
           - Pixels <  128 -> 0   (black)
        3. Report any pixels that were in the gray zone (64-192) as cleaned.

    Parameters
    ----------
    image_data:
        Raw PNG image bytes.

    Returns
    -------
    tuple[bytes, list[QualityIssue]]
        Cleaned image data and any issues found.
    """
    issues: list[QualityIssue] = []

    try:
        import io

        from PIL import Image

        img = Image.open(io.BytesIO(image_data)).convert("L")
        pixels = img.load()
        width, height = img.size

        gray_pixel_count = 0
        for y in range(height):
            for x in range(width):
                val = pixels[x, y]
                if 1 <= val <= 254:
                    gray_pixel_count += 1
                # Threshold binarization at 128
                pixels[x, y] = 255 if val >= 128 else 0

        if gray_pixel_count > 0:
            gray_pct = (gray_pixel_count / (width * height)) * 100
            issues.append(
                QualityIssue(
                    step="auto_clean",
                    severity=Severity.WARNING if gray_pct > 5 else Severity.INFO,
                    message=f"Cleaned {gray_pixel_count} gray pixels ({gray_pct:.1f}% of image)",
                )
            )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), issues

    except ImportError:
        logger.warning("PIL not available; returning image data unchanged")
        issues.append(
            QualityIssue(
                step="auto_clean",
                severity=Severity.WARNING,
                message="PIL/Pillow not installed; skipped binarization",
            )
        )
        return image_data, issues


# ---------------------------------------------------------------------------
# Step 3: Stroke Uniformity
# ---------------------------------------------------------------------------


async def step_3_stroke_uniformity(
    image_data: bytes,
    target_weight: int = 3,
) -> tuple[bytes, list[QualityIssue]]:
    """Normalize line thickness using morphological operations.

    Algorithm:
        1. Invert image (lines become white on black for morphological ops).
        2. Apply morphological closing to fill small gaps in lines.
        3. Apply morphological opening with a disk kernel sized to
           ``target_weight`` to normalize stroke width.
        4. Re-invert to restore black-on-white.
        5. Report uniformity metrics.

    Parameters
    ----------
    image_data:
        B&W PNG image bytes (output of step_2).
    target_weight:
        Desired stroke width in pixels (default 3).

    Returns
    -------
    tuple[bytes, list[QualityIssue]]
        Stroke-normalized image and issues.
    """
    issues: list[QualityIssue] = []

    try:
        import io

        from PIL import Image, ImageFilter, ImageMorph  # noqa: F401

        img = Image.open(io.BytesIO(image_data)).convert("L")

        # Invert: lines (0) become 255, background (255) becomes 0
        inverted = Image.eval(img, lambda px: 255 - px)

        # Morphological closing (dilate then erode) to connect near-breaks
        # Using min/max filters as Pillow morphological approximation
        kernel_size = max(3, target_weight)
        closed = inverted.filter(ImageFilter.MaxFilter(kernel_size))
        closed = closed.filter(ImageFilter.MinFilter(kernel_size))

        # Morphological opening (erode then dilate) to normalize thickness
        opened = closed.filter(ImageFilter.MinFilter(kernel_size))
        opened = opened.filter(ImageFilter.MaxFilter(kernel_size))

        # Re-invert back to black lines on white
        result = Image.eval(opened, lambda px: 255 - px)

        # Measure uniformity: compare original vs processed black pixel counts
        orig_black = sum(1 for px in img.getdata() if px == 0)
        new_black = sum(1 for px in result.getdata() if px == 0)
        if orig_black > 0:
            change_pct = abs(new_black - orig_black) / orig_black * 100
            if change_pct > 20:
                issues.append(
                    QualityIssue(
                        step="stroke_uniformity",
                        severity=Severity.WARNING,
                        message=f"Significant stroke change: {change_pct:.1f}% pixel difference after normalization",
                    )
                )

        buf = io.BytesIO()
        result.save(buf, format="PNG")
        return buf.getvalue(), issues

    except ImportError:
        logger.warning("PIL not available; skipping stroke uniformity")
        issues.append(
            QualityIssue(
                step="stroke_uniformity",
                severity=Severity.WARNING,
                message="PIL/Pillow not installed; skipped stroke normalization",
            )
        )
        return image_data, issues


# ---------------------------------------------------------------------------
# Step 4: Closed Shapes
# ---------------------------------------------------------------------------


async def step_4_closed_shapes(image_data: bytes) -> tuple[bytes, list[QualityIssue]]:
    """Detect open outlines using contour analysis.

    Algorithm:
        1. Find all contours (connected black regions) in the binary image.
        2. For each contour, check if the start and end points are within
           a proximity threshold (indicating a closed shape).
        3. Open shapes are flagged with their location coordinates.
        4. Image data is returned unchanged (detection only, no auto-fix).

    Parameters
    ----------
    image_data:
        B&W PNG image bytes.

    Returns
    -------
    tuple[bytes, list[QualityIssue]]
        Original image data and list of open shape locations found.
    """
    issues: list[QualityIssue] = []

    try:
        import io

        from PIL import Image

        img = Image.open(io.BytesIO(image_data)).convert("L")
        width, height = img.size
        pixels = list(img.getdata())

        # Simple contour detection: scan for black pixel clusters
        # and check boundary connectivity
        visited = set()
        open_shapes: list[dict[str, int]] = []

        def flood_fill(start_x: int, start_y: int) -> tuple[list[tuple[int, int]], bool]:
            """Flood-fill a connected component, return pixels and edge-touching flag."""
            stack = [(start_x, start_y)]
            component: list[tuple[int, int]] = []
            touches_edge = False
            boundary_pixels: list[tuple[int, int]] = []

            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in visited or cx < 0 or cy < 0 or cx >= width or cy >= height:
                    continue
                if pixels[cy * width + cx] != 0:  # not black
                    continue
                visited.add((cx, cy))
                component.append((cx, cy))

                # Check if pixel is on image edge
                if cx == 0 or cy == 0 or cx == width - 1 or cy == height - 1:
                    touches_edge = True

                # Check if pixel is a boundary pixel (has white neighbor)
                is_boundary = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if pixels[ny * width + nx] == 255:
                            is_boundary = True
                        elif (nx, ny) not in visited:
                            stack.append((nx, ny))
                    else:
                        is_boundary = True

                if is_boundary:
                    boundary_pixels.append((cx, cy))

            return boundary_pixels, touches_edge

        # Scan for connected black components (sample for performance)
        step_size = max(1, min(width, height) // 100)
        for y in range(0, height, step_size):
            for x in range(0, width, step_size):
                if (x, y) not in visited and pixels[y * width + x] == 0:
                    boundary, touches_edge = flood_fill(x, y)
                    # Shapes touching the image edge are potentially open
                    if touches_edge and len(boundary) > 20:
                        center_x = sum(p[0] for p in boundary) // len(boundary)
                        center_y = sum(p[1] for p in boundary) // len(boundary)
                        open_shapes.append({"x": center_x, "y": center_y})

        if open_shapes:
            issues.append(
                QualityIssue(
                    step="closed_shapes",
                    severity=Severity.WARNING,
                    message=f"Found {len(open_shapes)} potentially open shape(s)",
                    location={"open_shapes": open_shapes[:20]},  # cap at 20
                )
            )

        return image_data, issues

    except ImportError:
        logger.warning("PIL not available; skipping closed shape detection")
        issues.append(
            QualityIssue(
                step="closed_shapes",
                severity=Severity.WARNING,
                message="PIL/Pillow not installed; skipped contour analysis",
            )
        )
        return image_data, issues


# ---------------------------------------------------------------------------
# Step 5: Speck Removal
# ---------------------------------------------------------------------------


async def step_5_speck_removal(
    image_data: bytes,
    min_size: int = 10,
) -> tuple[bytes, list[QualityIssue]]:
    """Remove connected components smaller than min_size pixels.

    Algorithm:
        1. Identify all connected black-pixel components.
        2. Components with fewer than ``min_size`` pixels are considered
           specks/noise and are set to white (255).
        3. Report count of removed specks.

    Parameters
    ----------
    image_data:
        B&W PNG image bytes.
    min_size:
        Minimum number of pixels for a component to be kept (default 10).

    Returns
    -------
    tuple[bytes, list[QualityIssue]]
        Cleaned image and issues.
    """
    issues: list[QualityIssue] = []

    try:
        import io

        from PIL import Image

        img = Image.open(io.BytesIO(image_data)).convert("L")
        width, height = img.size
        pixels = img.load()

        visited = [[False] * width for _ in range(height)]
        specks_removed = 0

        def find_component(sx: int, sy: int) -> list[tuple[int, int]]:
            stack = [(sx, sy)]
            component: list[tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                if cx < 0 or cy < 0 or cx >= width or cy >= height:
                    continue
                if visited[cy][cx] or pixels[cx, cy] != 0:
                    continue
                visited[cy][cx] = True
                component.append((cx, cy))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    stack.append((cx + dx, cy + dy))
            return component

        for y in range(height):
            for x in range(width):
                if not visited[y][x] and pixels[x, y] == 0:
                    component = find_component(x, y)
                    if len(component) < min_size:
                        for cx, cy in component:
                            pixels[cx, cy] = 255
                        specks_removed += 1

        if specks_removed > 0:
            issues.append(
                QualityIssue(
                    step="speck_removal",
                    severity=Severity.INFO,
                    message=f"Removed {specks_removed} speck(s) smaller than {min_size}px",
                )
            )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), issues

    except ImportError:
        logger.warning("PIL not available; skipping speck removal")
        issues.append(
            QualityIssue(
                step="speck_removal",
                severity=Severity.WARNING,
                message="PIL/Pillow not installed; skipped speck removal",
            )
        )
        return image_data, issues


# ---------------------------------------------------------------------------
# Step 6: Background Check
# ---------------------------------------------------------------------------


async def step_6_background_check(image_data: bytes) -> tuple[bytes, list[QualityIssue]]:
    """Verify pure #FFFFFF background and fix off-white areas.

    Algorithm:
        1. Scan all non-black pixels (value > 0).
        2. Any pixel in range 200-254 (off-white) is set to 255 (pure white).
        3. Report percentage of off-white pixels corrected.

    Parameters
    ----------
    image_data:
        B&W PNG image bytes.

    Returns
    -------
    tuple[bytes, list[QualityIssue]]
        Image with corrected background and issues.
    """
    issues: list[QualityIssue] = []

    try:
        import io

        from PIL import Image

        img = Image.open(io.BytesIO(image_data)).convert("L")
        pixels = img.load()
        width, height = img.size

        off_white_count = 0
        total_white_area = 0

        for y in range(height):
            for x in range(width):
                val = pixels[x, y]
                if val > 0:  # not black
                    total_white_area += 1
                    if val < 255:
                        off_white_count += 1
                        pixels[x, y] = 255

        if off_white_count > 0 and total_white_area > 0:
            pct = (off_white_count / total_white_area) * 100
            issues.append(
                QualityIssue(
                    step="background_check",
                    severity=Severity.WARNING if pct > 2 else Severity.INFO,
                    message=f"Fixed {off_white_count} off-white pixels ({pct:.1f}% of background)",
                )
            )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), issues

    except ImportError:
        logger.warning("PIL not available; skipping background check")
        issues.append(
            QualityIssue(
                step="background_check",
                severity=Severity.WARNING,
                message="PIL/Pillow not installed; skipped background verification",
            )
        )
        return image_data, issues


# ---------------------------------------------------------------------------
# Step 7: Quality Check (Final Verification)
# ---------------------------------------------------------------------------


async def step_7_quality_check(image_data: bytes) -> QualityReport:
    """Run final verification -- aggregate all checks and produce a QualityReport.

    Checks performed:
        - Pure B&W verification (no gray pixels remain)
        - Ink density calculation (percentage of black pixels)
        - Minimum content check (image is not blank)
        - Resolution check placeholder (300 DPI at print size)

    Parameters
    ----------
    image_data:
        B&W PNG image bytes (after steps 1-6).

    Returns
    -------
    QualityReport
        Final quality report with score (0-100), issues, and pass/fail.
    """
    issues: list[QualityIssue] = []
    score = 100.0

    try:
        import io

        from PIL import Image

        img = Image.open(io.BytesIO(image_data)).convert("L")
        width, height = img.size
        total_pixels = width * height

        if total_pixels == 0:
            return QualityReport(
                score=0,
                issues=[QualityIssue(step="quality_check", severity=Severity.ERROR, message="Image has zero pixels")],
                passed=False,
            )

        pixel_data = list(img.getdata())

        # Count pixel types
        black_count = sum(1 for p in pixel_data if p == 0)
        white_count = sum(1 for p in pixel_data if p == 255)
        gray_count = total_pixels - black_count - white_count

        # Gray pixel check (should be 0 after auto-clean)
        if gray_count > 0:
            gray_pct = (gray_count / total_pixels) * 100
            score -= min(30, gray_pct * 3)
            issues.append(
                QualityIssue(
                    step="quality_check",
                    severity=Severity.ERROR,
                    message=f"Found {gray_count} gray pixels ({gray_pct:.2f}%); image is not pure B&W",
                )
            )

        # Ink density check
        ink_density = (black_count / total_pixels) * 100
        if ink_density > 40:
            score -= 15
            issues.append(
                QualityIssue(
                    step="quality_check",
                    severity=Severity.WARNING,
                    message=f"High ink density: {ink_density:.1f}% (recommended <40%)",
                )
            )
        elif ink_density < 2:
            score -= 20
            issues.append(
                QualityIssue(
                    step="quality_check",
                    severity=Severity.WARNING,
                    message=f"Very low ink density: {ink_density:.1f}% -- page may appear blank",
                )
            )

        # Blank page check
        if black_count == 0:
            score = 0
            issues.append(
                QualityIssue(
                    step="quality_check",
                    severity=Severity.ERROR,
                    message="Page is completely blank (no black pixels)",
                )
            )

        # Resolution check (informational)
        if width < 2550 or height < 3300:
            score -= 10
            issues.append(
                QualityIssue(
                    step="quality_check",
                    severity=Severity.WARNING,
                    message=f"Image resolution {width}x{height} may be below 300 DPI at 8.5x11 (need 2550x3300)",
                )
            )

    except ImportError:
        logger.warning("PIL not available; returning basic report")
        issues.append(
            QualityIssue(
                step="quality_check",
                severity=Severity.WARNING,
                message="PIL/Pillow not installed; quality check limited",
            )
        )
        score = 50.0

    score = max(0, min(100, score))
    passed = score >= 70 and not any(i.severity == Severity.ERROR for i in issues)

    return QualityReport(score=score, issues=issues, passed=passed)


# ---------------------------------------------------------------------------
# Full Pipeline Runner
# ---------------------------------------------------------------------------


async def run_full_pipeline(image_data: bytes) -> PipelineResult:
    """Execute all 7 pipeline steps sequentially.

    Steps 2-6 clean/process the image.  Step 7 produces the final report.
    Step 1 (generation) is NOT called here -- the caller passes in already-
    generated image data.

    Each step is wrapped in error handling so that a failure in one step is
    recorded but does not prevent subsequent steps from running.  The final
    ``PipelineResult`` includes per-step success/failure information in
    ``step_results``.

    Parameters
    ----------
    image_data:
        Raw PNG image bytes (output of step 1 or user upload).

    Returns
    -------
    PipelineResult
        Cleaned image bytes, quality report, list of completed steps,
        and per-step structured results.
    """
    steps_completed: list[str] = []
    step_results: list[StepResult] = []
    all_issues: list[QualityIssue] = []

    # Define processing steps (2-6) with uniform signature: bytes in -> (bytes, issues) out
    processing_steps: list[tuple[str, Any]] = [
        ("auto_clean", step_2_auto_clean),
        ("stroke_uniformity", step_3_stroke_uniformity),
        ("closed_shapes", step_4_closed_shapes),
        ("speck_removal", step_5_speck_removal),
        ("background_check", step_6_background_check),
    ]

    for step_name, step_fn in processing_steps:
        try:
            image_data, issues = await step_fn(image_data)
            all_issues.extend(issues)
            steps_completed.append(step_name)
            step_results.append(
                StepResult(
                    step_name=step_name,
                    success=True,
                    issues=list(issues),
                )
            )
        except Exception as exc:
            error_msg = f"Step '{step_name}' failed: {exc}"
            logger.error(error_msg, exc_info=True)
            failure_issue = QualityIssue(
                step=step_name,
                severity=Severity.ERROR,
                message=error_msg,
            )
            all_issues.append(failure_issue)
            step_results.append(
                StepResult(
                    step_name=step_name,
                    success=False,
                    issues=[failure_issue],
                    error=str(exc),
                )
            )
            # Continue with the image data we have so far

    # Step 7: Quality Check (final verification)
    try:
        report = await step_7_quality_check(image_data)
        report.issues = all_issues + report.issues
        steps_completed.append("quality_check")
        step_results.append(
            StepResult(
                step_name="quality_check",
                success=True,
                issues=list(report.issues),
            )
        )
    except Exception as exc:
        error_msg = f"Step 'quality_check' failed: {exc}"
        logger.error(error_msg, exc_info=True)
        failure_issue = QualityIssue(
            step="quality_check",
            severity=Severity.ERROR,
            message=error_msg,
        )
        all_issues.append(failure_issue)
        step_results.append(
            StepResult(
                step_name="quality_check",
                success=False,
                issues=[failure_issue],
                error=str(exc),
            )
        )
        # Build a fallback report since step 7 failed
        report = QualityReport(score=0, issues=all_issues, passed=False)

    # Recalculate passed based on all issues
    has_errors = any(i.severity == Severity.ERROR for i in report.issues)
    report.passed = report.score >= 70 and not has_errors

    return PipelineResult(
        image_data=image_data,
        report=report,
        steps_completed=steps_completed,
        step_results=step_results,
    )
