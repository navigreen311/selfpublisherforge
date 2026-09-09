"""SVG renderers for Word Search and Crossword puzzles.

Produces clean, print-quality SVG with:
- Crisp grid lines
- Proper fonts (monospace for grids, sans-serif for clues)
- Solution highlighting
- Sizing appropriate for standard trim sizes
"""

from __future__ import annotations

from xml.sax.saxutils import escape

# ---- Constants ----
CELL_SIZE = 32  # px per cell
FONT_SIZE = 16
NUMBER_FONT_SIZE = 9
PADDING = 20
STROKE_COLOR = "#333333"
FILL_EMPTY = "#FFFFFF"
FILL_BLACK = "#000000"
HIGHLIGHT_COLOR = "#FFEB3B"
SOLUTION_FILL = "#C8E6C9"
FONT_FAMILY = "'Courier New', Courier, monospace"
SANS_FONT = "'Helvetica Neue', Arial, sans-serif"


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'<rect width="{width}" height="{height}" fill="{FILL_EMPTY}"/>\n'
    )


def _svg_footer() -> str:
    return "</svg>"


# ---- Word Search ----


def render_word_search_svg(puzzle_data: dict, show_solution: bool = False) -> str:
    """Render a word search puzzle as SVG.

    Parameters
    ----------
    puzzle_data:
        Output of ``generate_word_search``.
    show_solution:
        If True, highlight solution cells.

    Returns
    -------
    SVG markup string.
    """
    grid = puzzle_data["grid"]
    grid_size = len(grid)
    solution = puzzle_data.get("solution", {})
    words = puzzle_data.get("words", [])

    svg_grid_w = grid_size * CELL_SIZE
    svg_grid_h = grid_size * CELL_SIZE

    # Word list area below grid
    word_list_height = ((len(words) // 4) + 2) * 20
    total_w = svg_grid_w + 2 * PADDING
    total_h = svg_grid_h + 2 * PADDING + word_list_height

    parts: list[str] = [_svg_header(total_w, total_h)]

    # Solution highlight cells
    solution_cells: set[tuple[int, int]] = set()
    if show_solution:
        for positions in solution.values():
            for pos in positions:
                solution_cells.add((pos[0], pos[1]))

    # Draw cells
    for r in range(grid_size):
        for c in range(grid_size):
            x = PADDING + c * CELL_SIZE
            y = PADDING + r * CELL_SIZE
            fill = SOLUTION_FILL if (r, c) in solution_cells else FILL_EMPTY
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'fill="{fill}" stroke="{STROKE_COLOR}" stroke-width="0.5"/>'
            )
            letter = escape(grid[r][c])
            tx = x + CELL_SIZE // 2
            ty = y + CELL_SIZE // 2 + FONT_SIZE // 3
            parts.append(
                f'<text x="{tx}" y="{ty}" font-family={FONT_FAMILY} '
                f'font-size="{FONT_SIZE}" text-anchor="middle" fill="#222">{letter}</text>'
            )

    # Word list
    wl_y = PADDING + svg_grid_h + 20
    cols = 4
    col_width = svg_grid_w // cols
    for i, word in enumerate(words):
        wx = PADDING + (i % cols) * col_width
        wy = wl_y + (i // cols) * 18
        decoration = "line-through" if show_solution else "none"
        parts.append(
            f'<text x="{wx}" y="{wy}" font-family={SANS_FONT} '
            f'font-size="12" text-decoration="{decoration}" fill="#444">{escape(word)}</text>'
        )

    parts.append(_svg_footer())
    return "\n".join(parts)


# ---- Crossword ----


def render_crossword_svg(puzzle_data: dict, show_solution: bool = False) -> str:
    """Render a crossword puzzle as SVG.

    Parameters
    ----------
    puzzle_data:
        Output of ``generate_crossword``.
    show_solution:
        If True, fill in solution letters.

    Returns
    -------
    SVG markup string.
    """
    grid = puzzle_data["grid"]
    solution = puzzle_data["solution"]
    size = puzzle_data["size"]
    rows = size["rows"]
    cols = size["cols"]
    word_records = puzzle_data.get("words", [])
    across_clues = puzzle_data.get("across_clues", {})
    down_clues = puzzle_data.get("down_clues", {})

    # Build number map from word records
    number_map: dict[tuple[int, int], int] = {}
    for wr in word_records:
        pos = (wr["row"], wr["col"])
        if pos not in number_map or wr["number"] < number_map[pos]:
            number_map[pos] = wr["number"]

    svg_grid_w = cols * CELL_SIZE
    svg_grid_h = rows * CELL_SIZE

    # Clue area
    clue_lines = 2 + len(across_clues) + len(down_clues) + 2
    clue_height = clue_lines * 16
    total_w = max(svg_grid_w + 2 * PADDING, 500)
    total_h = svg_grid_h + 2 * PADDING + clue_height + 20

    parts: list[str] = [_svg_header(total_w, total_h)]

    # Draw cells
    for r in range(rows):
        for c in range(cols):
            x = PADDING + c * CELL_SIZE
            y = PADDING + r * CELL_SIZE
            cell_val = grid[r][c]

            if cell_val is None:
                # Black square
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                    f'fill="{FILL_BLACK}" stroke="{STROKE_COLOR}" stroke-width="0.5"/>'
                )
            else:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                    f'fill="{FILL_EMPTY}" stroke="{STROKE_COLOR}" stroke-width="1"/>'
                )
                # Cell number
                num = number_map.get((r, c))
                if num is not None:
                    parts.append(
                        f'<text x="{x + 2}" y="{y + NUMBER_FONT_SIZE + 1}" '
                        f'font-family={SANS_FONT} font-size="{NUMBER_FONT_SIZE}" '
                        f'fill="#666">{num}</text>'
                    )
                # Solution letter
                if show_solution and solution[r][c] is not None:
                    letter = escape(solution[r][c])
                    tx = x + CELL_SIZE // 2
                    ty = y + CELL_SIZE // 2 + FONT_SIZE // 3
                    parts.append(
                        f'<text x="{tx}" y="{ty}" font-family={FONT_FAMILY} '
                        f'font-size="{FONT_SIZE}" text-anchor="middle" fill="#222">{letter}</text>'
                    )

    # Clues below grid
    clue_y = PADDING + svg_grid_h + 30
    parts.append(
        f'<text x="{PADDING}" y="{clue_y}" font-family={SANS_FONT} '
        f'font-size="14" font-weight="bold" fill="#000">ACROSS</text>'
    )
    clue_y += 18
    for num in sorted(across_clues.keys()):
        clue_text = escape(str(across_clues[num]))
        parts.append(
            f'<text x="{PADDING}" y="{clue_y}" font-family={SANS_FONT} '
            f'font-size="11" fill="#333">{num}. {clue_text}</text>'
        )
        clue_y += 15

    clue_y += 10
    parts.append(
        f'<text x="{PADDING}" y="{clue_y}" font-family={SANS_FONT} '
        f'font-size="14" font-weight="bold" fill="#000">DOWN</text>'
    )
    clue_y += 18
    for num in sorted(down_clues.keys()):
        clue_text = escape(str(down_clues[num]))
        parts.append(
            f'<text x="{PADDING}" y="{clue_y}" font-family={SANS_FONT} '
            f'font-size="11" fill="#333">{num}. {clue_text}</text>'
        )
        clue_y += 15

    parts.append(_svg_footer())
    return "\n".join(parts)
