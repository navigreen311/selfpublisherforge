"""
Crossword puzzle generator.

Algorithm: Intersection-based placement with scoring for compactness and symmetry.
Produces valid crossword grids with numbered squares and across/down clues.
"""

import hashlib
import json
import random

# Placement direction constants
ACROSS = "across"
DOWN = "down"


def _sanitize_word(word: str) -> str:
    """Uppercase, remove non-alpha characters."""
    return "".join(ch for ch in word.upper() if ch.isalpha())


def _find_intersections(
    word: str,
    placed: list[dict],
    grid: dict[tuple[int, int], str],
    max_width: int,
    max_height: int,
) -> list[dict]:
    """
    Find all valid intersection positions for a word with already-placed words.

    Returns list of candidate placements with scores.
    """
    candidates = []

    for p in placed:
        p_word = p["word"]
        p_row = p["row"]
        p_col = p["col"]
        p_dir = p["direction"]

        for i, letter_w in enumerate(word):
            for j, letter_p in enumerate(p_word):
                if letter_w != letter_p:
                    continue

                # The intersection point in the placed word
                if p_dir == ACROSS:
                    int_row = p_row
                    int_col = p_col + j
                else:
                    int_row = p_row + j
                    int_col = p_col

                # New word direction is perpendicular
                new_dir = DOWN if p_dir == ACROSS else ACROSS

                # Calculate start position of new word
                if new_dir == ACROSS:
                    new_row = int_row
                    new_col = int_col - i
                else:
                    new_row = int_row - i
                    new_col = int_col

                # Check bounds
                if new_dir == ACROSS:
                    end_col = new_col + len(word) - 1
                    if new_col < 0 or end_col >= max_width or new_row < 0 or new_row >= max_height:
                        continue
                else:
                    end_row = new_row + len(word) - 1
                    if new_row < 0 or end_row >= max_height or new_col < 0 or new_col >= max_width:
                        continue

                # Check if placement is valid (no conflicts)
                valid = True
                intersections = 0

                for k, letter in enumerate(word):
                    if new_dir == ACROSS:
                        r, c = new_row, new_col + k
                    else:
                        r, c = new_row + k, new_col

                    cell = grid.get((r, c))
                    if cell is not None:
                        if cell == letter:
                            intersections += 1
                        else:
                            valid = False
                            break

                    # Check adjacent cells (no parallel touching)
                    if new_dir == ACROSS:
                        # Check above and below unless it's an intersection
                        if cell is None:
                            above = grid.get((r - 1, c))
                            below = grid.get((r + 1, c))
                            if above is not None or below is not None:
                                # Check if this adjacency is from an intersecting word
                                is_intersection = False
                                for pp in placed:
                                    if pp["direction"] == DOWN:
                                        pr, pc = pp["row"], pp["col"]
                                        for m in range(len(pp["word"])):
                                            if (pr + m, pc) == (r, c):
                                                is_intersection = True
                                                break
                                    if is_intersection:
                                        break
                                if not is_intersection and (above is not None or below is not None):
                                    valid = False
                                    break
                    else:
                        if cell is None:
                            left = grid.get((r, c - 1))
                            right = grid.get((r, c + 1))
                            if left is not None or right is not None:
                                is_intersection = False
                                for pp in placed:
                                    if pp["direction"] == ACROSS:
                                        pr, pc = pp["row"], pp["col"]
                                        for m in range(len(pp["word"])):
                                            if (pr, pc + m) == (r, c):
                                                is_intersection = True
                                                break
                                    if is_intersection:
                                        break
                                if not is_intersection and (left is not None or right is not None):
                                    valid = False
                                    break

                if not valid:
                    continue

                # Check cells immediately before and after the word are empty
                if new_dir == ACROSS:
                    before = grid.get((new_row, new_col - 1))
                    after = grid.get((new_row, new_col + len(word)))
                else:
                    before = grid.get((new_row - 1, new_col))
                    after = grid.get((new_row + len(word), new_col))

                if before is not None or after is not None:
                    continue

                if intersections == 0:
                    continue

                candidates.append({
                    "word": word,
                    "row": new_row,
                    "col": new_col,
                    "direction": new_dir,
                    "intersections": intersections,
                })

    return candidates


def _score_placement(
    candidate: dict,
    placed: list[dict],
    max_width: int,
    max_height: int,
) -> float:
    """
    Score a candidate placement by compactness, symmetry, and intersection count.
    Higher is better.
    """
    score = 0.0

    # Intersection count (strongly preferred)
    score += candidate["intersections"] * 10.0

    # Compactness: prefer positions closer to center of existing words
    if placed:
        center_r = sum(p["row"] for p in placed) / len(placed)
        center_c = sum(p["col"] for p in placed) / len(placed)
        dist = abs(candidate["row"] - center_r) + abs(candidate["col"] - center_c)
        score -= dist * 0.5

    # Symmetry bonus: prefer placements that balance the grid
    mid_r = max_height / 2
    mid_c = max_width / 2
    sym_dist = abs(candidate["row"] - mid_r) + abs(candidate["col"] - mid_c)
    score -= sym_dist * 0.2

    return score


def _number_grid(
    placed: list[dict],
    min_row: int,
    min_col: int,
) -> tuple[list[dict], dict[int, str], dict[int, str]]:
    """
    Assign standard crossword numbering to placed words.
    A square gets a number if it's the start of an across or down word.
    Numbers are assigned left-to-right, top-to-bottom.
    """
    # Collect all starting positions
    starts: dict[tuple[int, int], dict] = {}  # (row, col) -> {"across": word, "down": word}

    for p in placed:
        r = p["row"] - min_row
        c = p["col"] - min_col
        key = (r, c)
        if key not in starts:
            starts[key] = {}
        starts[key][p["direction"]] = p["word"]

    # Sort positions top-to-bottom, left-to-right
    sorted_positions = sorted(starts.keys(), key=lambda pos: (pos[0], pos[1]))

    numbered_placements = []
    across_clues: dict[int, str] = {}
    down_clues: dict[int, str] = {}
    number = 1

    assigned_numbers: dict[tuple[int, int], int] = {}

    for pos in sorted_positions:
        assigned_numbers[pos] = number
        dirs = starts[pos]

        if ACROSS in dirs:
            across_clues[number] = dirs[ACROSS]
        if DOWN in dirs:
            down_clues[number] = dirs[DOWN]
        number += 1

    # Rebuild placements with numbers
    for p in placed:
        r = p["row"] - min_row
        c = p["col"] - min_col
        key = (r, c)
        num = assigned_numbers.get(key)
        numbered_placements.append({
            "word": p["word"],
            "row": r,
            "col": c,
            "direction": p["direction"],
            "number": num,
        })

    return numbered_placements, across_clues, down_clues


def generate_crossword(
    words: list[str],
    clues: dict[str, str],
    max_width: int = 15,
    max_height: int = 15,
    max_attempts: int = 3,
    seed: int | None = None,
) -> dict:
    """
    Generate a crossword puzzle using intersection-based placement.

    Args:
        words: List of words to place.
        clues: Dictionary mapping words to their clues.
        max_width: Maximum grid width.
        max_height: Maximum grid height.
        max_attempts: Number of full generation attempts (picks best result).
        seed: Optional random seed.

    Returns:
        Dictionary with grid, placements, clues, solution, difficulty, content_hash.
    """
    if seed is not None:
        random.seed(seed)

    # Sanitize words
    sanitized = []
    clue_map: dict[str, str] = {}
    for w in words:
        clean = _sanitize_word(w)
        if clean and len(clean) >= 2:
            sanitized.append(clean)
            # Map sanitized word to clue
            original_key = next(
                (k for k in clues if _sanitize_word(k) == clean), None
            )
            if original_key:
                clue_map[clean] = clues[original_key]
            else:
                clue_map[clean] = f"Clue for {clean}"

    # Sort longest first
    sanitized.sort(key=len, reverse=True)

    # Filter words that can't fit
    sanitized = [w for w in sanitized if len(w) <= max(max_width, max_height)]

    best_result = None
    best_placed_count = 0

    for attempt in range(max_attempts):
        grid: dict[tuple[int, int], str] = {}
        placed: list[dict] = []

        if not sanitized:
            break

        # Place first word horizontally in center
        first = sanitized[0]
        start_row = max_height // 2
        start_col = (max_width - len(first)) // 2
        for i, letter in enumerate(first):
            grid[(start_row, start_col + i)] = letter
        placed.append({
            "word": first,
            "row": start_row,
            "col": start_col,
            "direction": ACROSS,
        })

        # Try to place remaining words
        remaining = sanitized[1:]
        random.shuffle(remaining)

        for word in remaining:
            candidates = _find_intersections(word, placed, grid, max_width, max_height)
            if not candidates:
                continue

            # Score and pick best
            scored = [(c, _score_placement(c, placed, max_width, max_height)) for c in candidates]
            scored.sort(key=lambda x: x[1], reverse=True)
            best_candidate = scored[0][0]

            # Place the word
            if best_candidate["direction"] == ACROSS:
                for i, letter in enumerate(word):
                    grid[(best_candidate["row"], best_candidate["col"] + i)] = letter
            else:
                for i, letter in enumerate(word):
                    grid[(best_candidate["row"] + i, best_candidate["col"])] = letter

            placed.append({
                "word": word,
                "row": best_candidate["row"],
                "col": best_candidate["col"],
                "direction": best_candidate["direction"],
            })

        if len(placed) > best_placed_count:
            best_placed_count = len(placed)
            best_result = (grid, placed)

    if best_result is None:
        # Return empty puzzle
        return {
            "grid": [],
            "placements": [],
            "across_clues": {},
            "down_clues": {},
            "solution": [],
            "unplaced_words": sanitized,
            "difficulty_score": 0.0,
            "content_hash": hashlib.sha256(b"empty").hexdigest(),
        }

    grid, placed = best_result

    # Determine grid bounds
    all_positions = list(grid.keys())
    min_row = min(r for r, c in all_positions)
    max_row = max(r for r, c in all_positions)
    min_col = min(c for r, c in all_positions)
    max_col = max(c for r, c in all_positions)

    actual_width = max_col - min_col + 1
    actual_height = max_row - min_row + 1

    # Build 2D grid (None = black square, letter = white square)
    grid_2d: list[list[str | None]] = [
        [None] * actual_width for _ in range(actual_height)
    ]
    solution_2d: list[list[str | None]] = [
        [None] * actual_width for _ in range(actual_height)
    ]

    for (r, c), letter in grid.items():
        nr = r - min_row
        nc = c - min_col
        grid_2d[nr][nc] = ""  # Empty white square (for puzzle)
        solution_2d[nr][nc] = letter  # Solution

    # Number the grid and get clues
    numbered_placements, across_numbers, down_numbers = _number_grid(placed, min_row, min_col)

    # Build across and down clue dicts with actual clue text
    across_clues_final: dict[str, str] = {}
    down_clues_final: dict[str, str] = {}

    for num, word in across_numbers.items():
        across_clues_final[str(num)] = clue_map.get(word, f"Clue for {word}")

    for num, word in down_numbers.items():
        down_clues_final[str(num)] = clue_map.get(word, f"Clue for {word}")

    # Calculate difficulty
    total_cells = actual_width * actual_height
    filled_cells = sum(1 for row in grid_2d for cell in row if cell is not None)
    black_square_pct = 1.0 - (filled_cells / total_cells) if total_cells > 0 else 0.0

    placed_words_list = [p["word"] for p in placed]
    avg_word_length = (
        sum(len(w) for w in placed_words_list) / len(placed_words_list)
        if placed_words_list
        else 0
    )

    difficulty = calculate_difficulty(
        black_square_pct=black_square_pct,
        avg_word_length=avg_word_length,
        clue_grade_level=8.0,  # Default grade level
    )

    # Content hash
    content_data = {
        "solution": solution_2d,
        "placements": [(p["word"], p["direction"]) for p in numbered_placements],
    }
    content_hash = hashlib.sha256(
        json.dumps(content_data, sort_keys=True, default=str).encode()
    ).hexdigest()

    # Puzzle grid with numbers
    numbered_grid: list[list[dict | None]] = [
        [None] * actual_width for _ in range(actual_height)
    ]
    number_positions: dict[tuple[int, int], int] = {}
    for p in numbered_placements:
        if p["number"] is not None:
            number_positions[(p["row"], p["col"])] = p["number"]

    for r in range(actual_height):
        for c in range(actual_width):
            if grid_2d[r][c] is not None:
                num = number_positions.get((r, c))
                numbered_grid[r][c] = {
                    "letter": "",
                    "number": num,
                }

    return {
        "grid": numbered_grid,
        "width": actual_width,
        "height": actual_height,
        "placements": numbered_placements,
        "across_clues": across_clues_final,
        "down_clues": down_clues_final,
        "solution": solution_2d,
        "unplaced_words": [w for w in sanitized if w not in [p["word"] for p in placed]],
        "black_square_pct": round(black_square_pct, 4),
        "avg_word_length": round(avg_word_length, 2),
        "difficulty_score": difficulty,
        "content_hash": content_hash,
    }


def calculate_difficulty(
    black_square_pct: float,
    avg_word_length: float,
    clue_grade_level: float = 8.0,
) -> float:
    """
    Calculate crossword difficulty score (0-100).

    Factors:
    - Black square percentage: higher = more isolated words = harder
    - Average word length: longer words = harder
    - Clue grade level: higher reading level = harder
    """
    # Black square percentage (0-30): 30%=0, 60%=30
    black_score = min(30.0, max(0.0, (black_square_pct - 0.3) / 0.3 * 30))

    # Average word length (0-35): 3 letters=0, 10 letters=35
    length_score = min(35.0, max(0.0, (avg_word_length - 3) / 7 * 35))

    # Clue grade level (0-35): grade 3=0, grade 12=35
    grade_score = min(35.0, max(0.0, (clue_grade_level - 3) / 9 * 35))

    total = black_score + length_score + grade_score
    return round(min(100.0, max(0.0, total)), 1)


def render_to_svg(
    puzzle: dict,
    cell_size: int = 32,
    show_solution: bool = False,
    font_family: str = "Arial, Helvetica, sans-serif",
) -> str:
    """
    Render a crossword puzzle to SVG string for print output.

    Args:
        puzzle: Result from generate_crossword().
        cell_size: Size of each grid cell in pixels.
        show_solution: If True, fill in solution letters.
        font_family: CSS font family.

    Returns:
        SVG string.
    """
    grid = puzzle["grid"]
    width = puzzle["width"]
    height = puzzle["height"]
    solution = puzzle["solution"]
    across_clues = puzzle["across_clues"]
    down_clues = puzzle["down_clues"]

    padding = 20
    clue_width = 280
    grid_px_w = width * cell_size
    grid_px_h = height * cell_size

    # Estimate clue section height
    clue_lines = len(across_clues) + len(down_clues) + 4  # headers + spacing
    clue_section_height = clue_lines * 16

    svg_width = grid_px_w + 2 * padding + clue_width + padding
    svg_height = max(grid_px_h + 2 * padding, clue_section_height + 2 * padding)

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_width}" height="{svg_height}" '
        f'viewBox="0 0 {svg_width} {svg_height}">'
    )
    parts.append(f'<rect width="{svg_width}" height="{svg_height}" fill="white"/>')

    # Draw grid
    for r in range(height):
        for c in range(width):
            x = padding + c * cell_size
            y = padding + r * cell_size

            cell = grid[r][c]
            if cell is None:
                # Black square
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                    f'fill="#333333" stroke="#333333" stroke-width="1"/>'
                )
            else:
                # White square
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                    f'fill="white" stroke="#333333" stroke-width="1"/>'
                )

                # Number in top-left corner
                if cell.get("number") is not None:
                    parts.append(
                        f'<text x="{x + 2}" y="{y + 10}" '
                        f'font-family="{font_family}" font-size="9" '
                        f'fill="#333333">{cell["number"]}</text>'
                    )

                # Solution letter
                if show_solution and solution[r][c] is not None:
                    lx = x + cell_size // 2
                    ly = y + cell_size // 2 + 5
                    parts.append(
                        f'<text x="{lx}" y="{ly}" text-anchor="middle" '
                        f'font-family="{font_family}" font-size="16" '
                        f'font-weight="bold" fill="#333333">{solution[r][c]}</text>'
                    )

    # Grid border
    parts.append(
        f'<rect x="{padding}" y="{padding}" '
        f'width="{grid_px_w}" height="{grid_px_h}" '
        f'fill="none" stroke="#333333" stroke-width="2"/>'
    )

    # Clues section
    clue_x = padding + grid_px_w + padding + 10
    clue_y = padding + 16

    parts.append(
        f'<text x="{clue_x}" y="{clue_y}" font-family="{font_family}" '
        f'font-size="14" font-weight="bold" fill="#333333">ACROSS</text>'
    )
    clue_y += 18

    for num in sorted(across_clues.keys(), key=lambda k: int(k)):
        clue_text = across_clues[num]
        # Escape XML special characters
        clue_text = clue_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append(
            f'<text x="{clue_x}" y="{clue_y}" font-family="{font_family}" '
            f'font-size="11" fill="#333333">{num}. {clue_text}</text>'
        )
        clue_y += 15

    clue_y += 10
    parts.append(
        f'<text x="{clue_x}" y="{clue_y}" font-family="{font_family}" '
        f'font-size="14" font-weight="bold" fill="#333333">DOWN</text>'
    )
    clue_y += 18

    for num in sorted(down_clues.keys(), key=lambda k: int(k)):
        clue_text = down_clues[num]
        clue_text = clue_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append(
            f'<text x="{clue_x}" y="{clue_y}" font-family="{font_family}" '
            f'font-size="11" fill="#333333">{num}. {clue_text}</text>'
        )
        clue_y += 15

    parts.append("</svg>")
    return "\n".join(parts)
