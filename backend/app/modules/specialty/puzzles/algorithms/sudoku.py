"""
Sudoku puzzle generator with verified unique solutions.

Supports 4x4 (kids), 6x6 (kids), and 9x9 (standard) grids.

Algorithm: Generate + Remove
  1. Generate a complete valid solution using backtracking.
     - Fill diagonal boxes first (they are independent).
     - Fill remaining cells with constraint propagation + backtracking.
  2. Remove numbers one at a time in random order.
  3. After each removal, verify the puzzle still has a unique solution.
  4. Stop when the target given-count is reached.
"""

from __future__ import annotations

import copy
import random
from typing import Any

from .utils import (
    generate_content_hash,
    svg_footer,
    svg_grid,
    svg_header,
    svg_rect,
    svg_text,
)

# ---------------------------------------------------------------------------
# Size configurations: (grid_size, box_rows, box_cols)
# ---------------------------------------------------------------------------
_SIZE_CONFIG: dict[int, tuple[int, int]] = {
    4: (2, 2),   # 2x2 boxes
    6: (2, 3),   # 2x3 boxes
    9: (3, 3),   # 3x3 boxes
}

# Given-count ranges per difficulty (for 9x9). Scaled proportionally for others.
_DIFFICULTY_RANGES_9: dict[str, tuple[int, int]] = {
    "easy":   (36, 45),
    "medium": (27, 35),
    "hard":   (22, 26),
}


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _get_box(row: int, col: int, box_rows: int, box_cols: int) -> int:
    """Return the box index for the given cell."""
    return (row // box_rows) * (box_rows) + (col // box_cols)


def _valid_placement(grid: list[list[int]], row: int, col: int,
                     num: int, size: int, box_rows: int, box_cols: int) -> bool:
    """Check whether *num* can be placed at (row, col)."""
    # Row check
    if num in grid[row]:
        return False
    # Column check
    for r in range(size):
        if grid[r][col] == num:
            return False
    # Box check
    br = (row // box_rows) * box_rows
    bc = (col // box_cols) * box_cols
    for r in range(br, br + box_rows):
        for c in range(bc, bc + box_cols):
            if grid[r][c] == num:
                return False
    return True


def _candidates(grid: list[list[int]], row: int, col: int,
                size: int, box_rows: int, box_cols: int) -> list[int]:
    """Return a list of valid candidates for (row, col)."""
    cands = []
    for num in range(1, size + 1):
        if _valid_placement(grid, row, col, num, size, box_rows, box_cols):
            cands.append(num)
    return cands


# ---------------------------------------------------------------------------
# Solution generation
# ---------------------------------------------------------------------------

def _fill_diagonal_boxes(grid: list[list[int]], size: int,
                         box_rows: int, box_cols: int) -> None:
    """
    Fill the diagonal boxes (they share no row/col constraints).

    Only applicable when box_rows == box_cols (square boxes, e.g. 4x4, 9x9).
    For non-square boxes (e.g. 6x6 with 2x3 boxes) this is a no-op because
    the diagonal boxes don't tile the grid evenly.
    """
    if box_rows != box_cols:
        return  # Non-square boxes — diagonal fill not applicable
    nums = list(range(1, size + 1))
    num_boxes_on_diag = size // box_rows
    for b in range(num_boxes_on_diag):
        br = b * box_rows
        bc = b * box_cols
        shuffled = nums[:]
        random.shuffle(shuffled)
        idx = 0
        for r in range(br, br + box_rows):
            for c in range(bc, bc + box_cols):
                grid[r][c] = shuffled[idx]
                idx += 1


def _fill_remaining(grid: list[list[int]], size: int,
                    box_rows: int, box_cols: int) -> bool:
    """Fill non-diagonal cells using backtracking. Returns True on success."""
    for r in range(size):
        for c in range(size):
            if grid[r][c] == 0:
                cands = _candidates(grid, r, c, size, box_rows, box_cols)
                random.shuffle(cands)
                for num in cands:
                    grid[r][c] = num
                    if _fill_remaining(grid, size, box_rows, box_cols):
                        return True
                    grid[r][c] = 0
                return False
    return True


def _generate_full_solution(size: int, box_rows: int,
                            box_cols: int) -> list[list[int]]:
    """
    Generate a complete valid Sudoku grid.

    Fills diagonal boxes first (they are independent of each other), then
    fills the remaining cells with backtracking.  If the diagonal
    configuration leads to an unsolvable state the whole grid is retried.
    """
    for _ in range(200):
        grid = [[0] * size for _ in range(size)]
        _fill_diagonal_boxes(grid, size, box_rows, box_cols)
        if _fill_remaining(grid, size, box_rows, box_cols):
            return grid
    # Fallback: pure backtracking without pre-filling diagonals
    grid = [[0] * size for _ in range(size)]
    _fill_remaining(grid, size, box_rows, box_cols)
    return grid


# ---------------------------------------------------------------------------
# Unique-solution verification
# ---------------------------------------------------------------------------

def verify_unique_solution(grid: list[list[int]],
                           size: int | None = None) -> bool:
    """
    Solve *grid* exhaustively and return True only if exactly 1 solution exists.

    Uses a counter that stops as soon as a second solution is found.
    """
    if size is None:
        size = len(grid)
    box_rows, box_cols = _SIZE_CONFIG[size]
    counter = [0]

    def _solve(g: list[list[int]]) -> None:
        if counter[0] > 1:
            return
        # Find next empty cell
        for r in range(size):
            for c in range(size):
                if g[r][c] == 0:
                    for num in range(1, size + 1):
                        if _valid_placement(g, r, c, num, size, box_rows, box_cols):
                            g[r][c] = num
                            _solve(g)
                            if counter[0] > 1:
                                g[r][c] = 0
                                return
                            g[r][c] = 0
                    return
        # No empty cell found — complete solution
        counter[0] += 1

    work = copy.deepcopy(grid)
    _solve(work)
    return counter[0] == 1


# ---------------------------------------------------------------------------
# Technique detection (simplified)
# ---------------------------------------------------------------------------

_TECHNIQUE_ORDER = [
    "naked_singles",
    "hidden_singles",
    "pointing_pairs",
    "box_line_reduction",
    "naked_pairs",
    "hidden_pairs",
    "naked_triples",
    "x_wing",
    "swordfish",
]


def _detect_techniques(grid: list[list[int]], solution: list[list[int]],
                        size: int, box_rows: int, box_cols: int) -> list[str]:
    """
    Detect which solving techniques are required for a puzzle.

    Uses a constraint-based solver that applies techniques in increasing
    difficulty order and records which ones were needed.
    """
    work = copy.deepcopy(grid)
    # Build candidate sets
    cand: list[list[set[int]]] = [
        [set() for _ in range(size)] for _ in range(size)
    ]
    for r in range(size):
        for c in range(size):
            if work[r][c] == 0:
                cand[r][c] = set(_candidates(work, r, c, size, box_rows, box_cols))

    techniques_used: set[str] = set()
    changed = True

    while changed:
        changed = False

        # --- Naked singles ---
        for r in range(size):
            for c in range(size):
                if work[r][c] == 0 and len(cand[r][c]) == 1:
                    val = next(iter(cand[r][c]))
                    work[r][c] = val
                    cand[r][c] = set()
                    # Remove from peers
                    for i in range(size):
                        cand[r][i].discard(val)
                        cand[i][c].discard(val)
                    br = (r // box_rows) * box_rows
                    bc = (c // box_cols) * box_cols
                    for rr in range(br, br + box_rows):
                        for cc in range(bc, bc + box_cols):
                            cand[rr][cc].discard(val)
                    techniques_used.add("naked_singles")
                    changed = True

        if changed:
            continue

        # --- Hidden singles ---
        for r in range(size):
            for c in range(size):
                if work[r][c] != 0:
                    continue
                for val in list(cand[r][c]):
                    # Check row
                    if all(val not in cand[r][cc] for cc in range(size) if cc != c and work[r][cc] == 0):
                        work[r][c] = val
                        cand[r][c] = set()
                        for i in range(size):
                            cand[r][i].discard(val)
                            cand[i][c].discard(val)
                        br = (r // box_rows) * box_rows
                        bc = (c // box_cols) * box_cols
                        for rr in range(br, br + box_rows):
                            for cc in range(bc, bc + box_cols):
                                cand[rr][cc].discard(val)
                        techniques_used.add("hidden_singles")
                        changed = True
                        break
                    # Check column
                    if all(val not in cand[rr][c] for rr in range(size) if rr != r and work[rr][c] == 0):
                        work[r][c] = val
                        cand[r][c] = set()
                        for i in range(size):
                            cand[r][i].discard(val)
                            cand[i][c].discard(val)
                        br = (r // box_rows) * box_rows
                        bc = (c // box_cols) * box_cols
                        for rr in range(br, br + box_rows):
                            for cc in range(bc, bc + box_cols):
                                cand[rr][cc].discard(val)
                        techniques_used.add("hidden_singles")
                        changed = True
                        break
                    # Check box
                    br = (r // box_rows) * box_rows
                    bc = (c // box_cols) * box_cols
                    found_elsewhere = False
                    for rr in range(br, br + box_rows):
                        for cc in range(bc, bc + box_cols):
                            if (rr, cc) != (r, c) and work[rr][cc] == 0 and val in cand[rr][cc]:
                                found_elsewhere = True
                                break
                        if found_elsewhere:
                            break
                    if not found_elsewhere:
                        work[r][c] = val
                        cand[r][c] = set()
                        for i in range(size):
                            cand[r][i].discard(val)
                            cand[i][c].discard(val)
                        for rr in range(br, br + box_rows):
                            for cc in range(bc, bc + box_cols):
                                cand[rr][cc].discard(val)
                        techniques_used.add("hidden_singles")
                        changed = True
                        break
                if changed:
                    break

        if changed:
            continue

        # --- Pointing pairs ---
        for box_r_start in range(0, size, box_rows):
            for box_c_start in range(0, size, box_cols):
                for val in range(1, size + 1):
                    positions = []
                    for rr in range(box_r_start, box_r_start + box_rows):
                        for cc in range(box_c_start, box_c_start + box_cols):
                            if work[rr][cc] == 0 and val in cand[rr][cc]:
                                positions.append((rr, cc))
                    if len(positions) < 2:
                        continue
                    # All in same row?
                    rows_set = {p[0] for p in positions}
                    if len(rows_set) == 1:
                        row = positions[0][0]
                        for cc in range(size):
                            if cc < box_c_start or cc >= box_c_start + box_cols:
                                if val in cand[row][cc]:
                                    cand[row][cc].discard(val)
                                    techniques_used.add("pointing_pairs")
                                    changed = True
                    # All in same col?
                    cols_set = {p[1] for p in positions}
                    if len(cols_set) == 1:
                        col = positions[0][1]
                        for rr in range(size):
                            if rr < box_r_start or rr >= box_r_start + box_rows:
                                if val in cand[rr][col]:
                                    cand[rr][col].discard(val)
                                    techniques_used.add("pointing_pairs")
                                    changed = True

        if changed:
            continue

        # If we still have empty cells but can't solve with these techniques,
        # mark remaining as needing advanced techniques
        remaining = sum(1 for r in range(size) for c in range(size) if work[r][c] == 0)
        if remaining > 0:
            techniques_used.add("naked_pairs")
            break

    # Return in difficulty order
    return [t for t in _TECHNIQUE_ORDER if t in techniques_used]


# ---------------------------------------------------------------------------
# Difficulty calculation
# ---------------------------------------------------------------------------

def calculate_difficulty(givens_count: int,
                         techniques_required: list[str],
                         size: int = 9) -> float:
    """
    Calculate a difficulty score from 0 to 100.

    Factors:
      - Fewer givens = harder (50% weight)
      - More advanced techniques = harder (50% weight)
    """
    total_cells = size * size
    # Givens component: 0 (all filled) → 100 (none filled)
    givens_ratio = 1.0 - (givens_count / total_cells)
    givens_score = givens_ratio * 100.0

    # Technique component: score by hardest technique required
    technique_weights = {
        "naked_singles": 10,
        "hidden_singles": 25,
        "pointing_pairs": 40,
        "box_line_reduction": 50,
        "naked_pairs": 60,
        "hidden_pairs": 70,
        "naked_triples": 80,
        "x_wing": 90,
        "swordfish": 100,
    }
    tech_score = 0.0
    for t in techniques_required:
        tech_score = max(tech_score, technique_weights.get(t, 0))

    return round(givens_score * 0.5 + tech_score * 0.5, 2)


# ---------------------------------------------------------------------------
# Puzzle generation (remove numbers with uniqueness verification)
# ---------------------------------------------------------------------------

def _target_givens(size: int, difficulty: str) -> int:
    """Return a random target given-count for the requested difficulty."""
    lo_9, hi_9 = _DIFFICULTY_RANGES_9.get(difficulty, (27, 35))
    # Scale proportionally for non-9x9 sizes
    scale = (size * size) / 81.0
    lo = max(1, round(lo_9 * scale))
    hi = max(lo, round(hi_9 * scale))
    return random.randint(lo, hi)


def generate_sudoku(size: int = 9, difficulty: str = "medium") -> dict[str, Any]:
    """
    Generate a Sudoku puzzle.

    Parameters
    ----------
    size : int
        Grid size. Must be 4, 6, or 9.
    difficulty : str
        One of "easy", "medium", "hard".

    Returns
    -------
    dict with keys:
        grid            – 2-D list (0 = empty)
        solution        – 2-D list (complete)
        givens_count    – int
        difficulty_score – float 0-100
        techniques_required – list[str]
        content_hash    – str (SHA-256)
        svg             – str (rendered SVG)
    """
    if size not in _SIZE_CONFIG:
        raise ValueError(f"Unsupported size {size}. Choose from {list(_SIZE_CONFIG.keys())}.")
    difficulty = difficulty.lower()
    if difficulty not in _DIFFICULTY_RANGES_9:
        raise ValueError(f"Unknown difficulty '{difficulty}'. Choose easy/medium/hard.")

    box_rows, box_cols = _SIZE_CONFIG[size]

    # Step 1: generate full solution
    solution = _generate_full_solution(size, box_rows, box_cols)

    # Step 2-4: remove numbers while keeping unique solution
    grid = copy.deepcopy(solution)
    target = _target_givens(size, difficulty)

    cells = [(r, c) for r in range(size) for c in range(size)]
    random.shuffle(cells)

    current_givens = size * size
    for r, c in cells:
        if current_givens <= target:
            break
        backup = grid[r][c]
        grid[r][c] = 0
        if verify_unique_solution(grid, size):
            current_givens -= 1
        else:
            grid[r][c] = backup  # restore — removal would create ambiguity

    # Detect techniques
    techniques = _detect_techniques(grid, solution, size, box_rows, box_cols)

    # Calculate difficulty
    score = calculate_difficulty(current_givens, techniques, size)

    content_hash = generate_content_hash({"grid": grid, "solution": solution})

    svg = render_sudoku_svg(grid, solution, size, box_rows, box_cols)

    return {
        "grid": grid,
        "solution": solution,
        "givens_count": current_givens,
        "difficulty_score": score,
        "techniques_required": techniques,
        "content_hash": content_hash,
        "svg": svg,
    }


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------

def render_sudoku_svg(grid: list[list[int]], solution: list[list[int]],
                      size: int, box_rows: int, box_cols: int,
                      cell_size: int = 50) -> str:
    """Render the puzzle grid to SVG."""
    padding = 20
    total = size * cell_size + 2 * padding
    parts: list[str] = [svg_header(total, total)]

    # Background
    parts.append(svg_rect(0, 0, total, total, fill="white", stroke="none"))

    # Thin grid lines
    parts.append(svg_grid(size, size, cell_size, offset_x=padding, offset_y=padding))

    # Thick box lines
    for i in range(size // box_cols + 1):
        x = padding + i * box_cols * cell_size
        parts.append(
            f'  <line x1="{x}" y1="{padding}" '
            f'x2="{x}" y2="{padding + size * cell_size}" '
            f'stroke="black" stroke-width="3"/>\n'
        )
    for i in range(size // box_rows + 1):
        y = padding + i * box_rows * cell_size
        parts.append(
            f'  <line x1="{padding}" y1="{y}" '
            f'x2="{padding + size * cell_size}" y2="{y}" '
            f'stroke="black" stroke-width="3"/>\n'
        )

    # Numbers (givens)
    font_size = max(12, cell_size // 2)
    for r in range(size):
        for c in range(size):
            if grid[r][c] != 0:
                cx = padding + c * cell_size + cell_size // 2
                cy = padding + r * cell_size + cell_size // 2
                parts.append(svg_text(cx, cy, str(grid[r][c]), font_size,
                                      font_weight="bold"))

    parts.append(svg_footer())
    return "".join(parts)
