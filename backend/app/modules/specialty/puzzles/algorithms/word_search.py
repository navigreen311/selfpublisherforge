"""
Word Search puzzle generator.

Algorithm: Backtracking placement with configurable directions.
Produces valid, solvable word search grids with solution data.
"""

import hashlib
import json
import random
import string

# Direction vectors: (row_delta, col_delta)
DIRECTION_VECTORS = {
    "right": (0, 1),
    "down": (1, 0),
    "left": (0, -1),
    "up": (-1, 0),
    "down_right": (1, 1),
    "down_left": (1, -1),
    "up_right": (-1, 1),
    "up_left": (-1, -1),
}

# Direction sets by count
DIRECTION_SETS = {
    2: ["right", "down"],
    4: ["right", "down", "down_right", "down_left"],
    8: ["right", "down", "left", "up", "down_right", "down_left", "up_right", "up_left"],
}


def _sanitize_word(word: str) -> str:
    """Uppercase, remove non-alpha characters."""
    return "".join(ch for ch in word.upper() if ch.isalpha())


def _sanitize_word_list(words: list[str]) -> list[str]:
    """Sanitize and deduplicate word list, sort longest first."""
    seen: set[str] = set()
    sanitized: list[str] = []
    for w in words:
        clean = _sanitize_word(w)
        if clean and len(clean) >= 2 and clean not in seen:
            seen.add(clean)
            sanitized.append(clean)
    sanitized.sort(key=len, reverse=True)
    return sanitized


def _can_place_word(
    grid: list[list[str]],
    word: str,
    row: int,
    col: int,
    dr: int,
    dc: int,
    grid_size: int,
) -> bool:
    """Check if a word can be placed at position in given direction."""
    for i, letter in enumerate(word):
        r = row + i * dr
        c = col + i * dc
        if r < 0 or r >= grid_size or c < 0 or c >= grid_size:
            return False
        cell = grid[r][c]
        if cell != "" and cell != letter:
            return False
    return True


def _place_word(
    grid: list[list[str]],
    word: str,
    row: int,
    col: int,
    dr: int,
    dc: int,
) -> list[tuple[int, int]]:
    """Place word on grid, return list of (row, col) positions."""
    positions = []
    for i, letter in enumerate(word):
        r = row + i * dr
        c = col + i * dc
        grid[r][c] = letter
        positions.append((r, c))
    return positions


def _remove_word(
    grid: list[list[str]],
    positions: list[tuple[int, int]],
    original_cells: list[str],
) -> None:
    """Remove a placed word, restoring original cell values."""
    for (r, c), orig in zip(positions, original_cells, strict=False):
        grid[r][c] = orig


def _count_overlaps(
    grid: list[list[str]],
    word: str,
    row: int,
    col: int,
    dr: int,
    dc: int,
) -> int:
    """Count how many letters overlap with already-placed letters."""
    count = 0
    for i, letter in enumerate(word):
        r = row + i * dr
        c = col + i * dc
        if grid[r][c] == letter:
            count += 1
    return count


def generate_word_search(
    words: list[str],
    grid_size: int = 15,
    directions: int = 4,
    max_retries_per_word: int = 200,
    seed: int | None = None,
) -> dict:
    """
    Generate a word search puzzle using backtracking placement.

    Args:
        words: List of words to place in the grid.
        grid_size: Size of the square grid (e.g. 15 = 15x15).
        directions: Number of directions (2, 4, or 8).
        max_retries_per_word: Maximum random placement attempts per word.
        seed: Optional random seed for reproducibility.

    Returns:
        Dictionary with grid, placed_words, solution, difficulty, content_hash.
    """
    if seed is not None:
        random.seed(seed)

    if directions not in DIRECTION_SETS:
        raise ValueError(f"directions must be 2, 4, or 8, got {directions}")

    direction_names = DIRECTION_SETS[directions]
    direction_vecs = [DIRECTION_VECTORS[d] for d in direction_names]

    sanitized = _sanitize_word_list(words)
    # Filter words that are too long for the grid
    sanitized = [w for w in sanitized if len(w) <= grid_size]

    # Initialize empty grid
    grid: list[list[str]] = [["" for _ in range(grid_size)] for _ in range(grid_size)]

    placed_words: list[dict] = []
    solution_positions: dict[str, list[tuple[int, int]]] = {}

    for word in sanitized:
        placed = False
        # Collect all possible placements
        candidates: list[tuple[int, int, int, int, int]] = []

        for _ in range(max_retries_per_word):
            row = random.randint(0, grid_size - 1)
            col = random.randint(0, grid_size - 1)
            dr, dc = random.choice(direction_vecs)

            if _can_place_word(grid, word, row, col, dr, dc, grid_size):
                overlaps = _count_overlaps(grid, word, row, col, dr, dc)
                candidates.append((row, col, dr, dc, overlaps))

        if candidates:
            # Prefer placements with more overlaps (more compact puzzle)
            candidates.sort(key=lambda x: x[4], reverse=True)
            row, col, dr, dc, overlaps = candidates[0]

            positions = _place_word(grid, word, row, col, dr, dc)
            # Find direction name
            dir_name = direction_names[direction_vecs.index((dr, dc))]

            placed_words.append(
                {
                    "word": word,
                    "row": row,
                    "col": col,
                    "direction": dir_name,
                    "positions": positions,
                }
            )
            solution_positions[word] = positions
            placed = True

        if not placed:
            # Word couldn't be placed; skip it
            pass

    # Fill remaining empty cells with random letters
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == "":
                grid[r][c] = random.choice(string.ascii_uppercase)

    # Calculate overlap rate
    total_placed_cells = sum(len(pw["positions"]) for pw in placed_words)
    unique_cells = len(set(pos for pw in placed_words for pos in pw["positions"]))
    overlap_rate = 1.0 - (unique_cells / total_placed_cells) if total_placed_cells > 0 else 0.0

    difficulty = calculate_difficulty(
        grid_size=grid_size,
        word_count=len(placed_words),
        direction_count=directions,
        overlap_rate=overlap_rate,
    )

    # Build solution highlight as a 2D boolean grid
    solution_highlight = [[False] * grid_size for _ in range(grid_size)]
    for positions in solution_positions.values():
        for r, c in positions:
            solution_highlight[r][c] = True

    # Content hash for duplicate detection
    content_data = {
        "grid": grid,
        "placed_words": [pw["word"] for pw in placed_words],
    }
    content_hash = hashlib.sha256(json.dumps(content_data, sort_keys=True).encode()).hexdigest()

    return {
        "grid": grid,
        "grid_size": grid_size,
        "directions": directions,
        "placed_words": [
            {
                "word": pw["word"],
                "row": pw["row"],
                "col": pw["col"],
                "direction": pw["direction"],
            }
            for pw in placed_words
        ],
        "unplaced_words": [w for w in sanitized if w not in solution_positions],
        "solution": {
            "highlighted_positions": [
                [r, c] for word_positions in solution_positions.values() for r, c in word_positions
            ],
            "word_positions": {word: [[r, c] for r, c in positions] for word, positions in solution_positions.items()},
        },
        "difficulty_score": difficulty,
        "overlap_rate": round(overlap_rate, 4),
        "content_hash": content_hash,
    }


def calculate_difficulty(
    grid_size: int,
    word_count: int,
    direction_count: int,
    overlap_rate: float,
) -> float:
    """
    Calculate word search difficulty score (0-100).

    Factors:
    - Grid size: larger = harder (10x10=easy, 20x20=hard)
    - Word count: more words = harder
    - Direction count: more directions = harder
    - Overlap rate: more overlap = harder to distinguish
    """
    # Grid size contribution (0-30): 10x10=0, 20x20=30
    grid_score = min(30.0, max(0.0, (grid_size - 10) / 10 * 30))

    # Word count contribution (0-25): 5 words=0, 25 words=25
    word_score = min(25.0, max(0.0, (word_count - 5) / 20 * 25))

    # Direction contribution (0-25): 2=0, 4=12, 8=25
    dir_map = {2: 0.0, 4: 12.0, 8: 25.0}
    dir_score = dir_map.get(direction_count, 12.0)

    # Overlap contribution (0-20): 0%=5, 30%+=20
    overlap_score = min(20.0, 5.0 + overlap_rate * 50)

    total = grid_score + word_score + dir_score + overlap_score
    return round(min(100.0, max(0.0, total)), 1)


def render_to_svg(
    puzzle: dict,
    cell_size: int = 30,
    show_solution: bool = False,
    font_size: int = 16,
    font_family: str = "Arial, Helvetica, sans-serif",
) -> str:
    """
    Render a word search puzzle to SVG string for print output.

    Args:
        puzzle: Result from generate_word_search().
        cell_size: Size of each grid cell in pixels.
        show_solution: If True, highlight solution positions.
        font_size: Font size for letters.
        font_family: CSS font family.

    Returns:
        SVG string.
    """
    grid = puzzle["grid"]
    grid_size = puzzle["grid_size"]
    placed_words = puzzle["placed_words"]

    padding = 20
    word_list_height = 80
    grid_px = grid_size * cell_size
    svg_width = grid_px + 2 * padding
    svg_height = grid_px + 2 * padding + word_list_height

    # Build set of solution cells for highlighting
    solution_cells: set[tuple[int, int]] = set()
    if show_solution:
        for pos in puzzle["solution"]["highlighted_positions"]:
            solution_cells.add((pos[0], pos[1]))

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_width}" height="{svg_height}" '
        f'viewBox="0 0 {svg_width} {svg_height}">'
    )

    # White background
    parts.append(f'<rect width="{svg_width}" height="{svg_height}" fill="white"/>')

    # Grid
    for r in range(grid_size):
        for c in range(grid_size):
            x = padding + c * cell_size
            y = padding + r * cell_size

            # Cell background
            fill = "#FFFFCC" if (r, c) in solution_cells else "white"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                f'fill="{fill}" stroke="#CCCCCC" stroke-width="0.5"/>'
            )

            # Letter
            letter = grid[r][c]
            tx = x + cell_size // 2
            ty = y + cell_size // 2 + font_size // 3
            weight = "bold" if (r, c) in solution_cells else "normal"
            parts.append(
                f'<text x="{tx}" y="{ty}" text-anchor="middle" '
                f'font-family="{font_family}" font-size="{font_size}" '
                f'font-weight="{weight}" fill="#333333">{letter}</text>'
            )

    # Grid border
    parts.append(
        f'<rect x="{padding}" y="{padding}" '
        f'width="{grid_px}" height="{grid_px}" '
        f'fill="none" stroke="#333333" stroke-width="1.5"/>'
    )

    # Word list at bottom
    word_y = padding + grid_px + 25
    words_per_row = max(1, grid_size // 3)
    word_list = [pw["word"] for pw in placed_words]

    for i, word in enumerate(word_list):
        row_idx = i // words_per_row
        col_idx = i % words_per_row
        wx = padding + col_idx * (grid_px // words_per_row)
        wy = word_y + row_idx * 18
        decoration = "line-through" if show_solution else "none"
        parts.append(
            f'<text x="{wx}" y="{wy}" font-family="{font_family}" '
            f'font-size="12" fill="#333333" '
            f'text-decoration="{decoration}">{word}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)
