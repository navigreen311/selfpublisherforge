"""
Number Search puzzle generator.

Same algorithm as word search but operates on digit sequences instead of letters.

Algorithm:
  1. Accept a list of number strings and a grid size.
  2. Place each number in the grid using random position + direction.
  3. Check for conflicts (overlap OK if same digit).
  4. Fill remaining cells with random digits.
  5. Record placement positions for the solution.
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

# Direction vectors: (row_delta, col_delta)
_DIRECTIONS_4 = [
    (0, 1),   # right
    (1, 0),   # down
    (0, -1),  # left
    (-1, 0),  # up
]

_DIRECTIONS_8 = _DIRECTIONS_4 + [
    (1, 1),   # down-right
    (1, -1),  # down-left
    (-1, 1),  # up-right
    (-1, -1), # up-left
]


def _get_directions(direction_count: int) -> list[tuple[int, int]]:
    if direction_count <= 4:
        return _DIRECTIONS_4
    return _DIRECTIONS_8


# ---------------------------------------------------------------------------
# Placement helpers
# ---------------------------------------------------------------------------

def _can_place(grid: list[list[str]], number: str,
               row: int, col: int, dr: int, dc: int,
               grid_size: int) -> bool:
    """Check whether *number* can be placed starting at (row, col) in direction (dr, dc)."""
    for i, digit in enumerate(number):
        r = row + i * dr
        c = col + i * dc
        if r < 0 or r >= grid_size or c < 0 or c >= grid_size:
            return False
        cell = grid[r][c]
        if cell != "" and cell != digit:
            return False
    return True


def _place(grid: list[list[str]], number: str,
           row: int, col: int, dr: int, dc: int) -> list[tuple[int, int]]:
    """Place *number* into the grid. Returns list of (row, col) positions."""
    positions: list[tuple[int, int]] = []
    for i, digit in enumerate(number):
        r = row + i * dr
        c = col + i * dc
        grid[r][c] = digit
        positions.append((r, c))
    return positions


def _try_place_number(grid: list[list[str]], number: str,
                      grid_size: int, directions: list[tuple[int, int]],
                      max_attempts: int = 200) -> list[tuple[int, int]] | None:
    """Attempt to place *number* at a random position/direction."""
    for _ in range(max_attempts):
        dr, dc = random.choice(directions)
        row = random.randint(0, grid_size - 1)
        col = random.randint(0, grid_size - 1)
        if _can_place(grid, number, row, col, dr, dc, grid_size):
            return _place(grid, number, row, col, dr, dc)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_number_search(numbers: list[str],
                           grid_size: int = 12,
                           directions: int = 4) -> dict[str, Any]:
    """
    Generate a number search puzzle.

    Parameters
    ----------
    numbers : list[str]
        Digit sequences to hide in the grid, e.g. ["314", "271828", "42"].
    grid_size : int
        Side length of the square grid.
    directions : int
        Number of allowed directions (4 = cardinal, 8 = cardinal + diagonal).

    Returns
    -------
    dict with keys:
        grid            – 2-D list of single-digit strings
        placed_numbers  – list of {number, positions: [(r,c), ...]}
        not_placed      – list of numbers that couldn't fit
        solution        – 2-D list with only placed digits (rest empty)
        content_hash    – SHA-256 hex string
        svg             – rendered SVG string
    """
    # Sanitize: keep only digit characters
    clean_numbers: list[str] = []
    for n in numbers:
        sanitized = "".join(ch for ch in str(n) if ch.isdigit())
        if sanitized and len(sanitized) <= grid_size:
            clean_numbers.append(sanitized)

    if not clean_numbers:
        raise ValueError("No valid digit sequences provided.")

    # Sort longest first for better placement success
    clean_numbers.sort(key=len, reverse=True)

    dir_vectors = _get_directions(directions)
    grid: list[list[str]] = [[""] * grid_size for _ in range(grid_size)]

    placed_numbers: list[dict[str, Any]] = []
    not_placed: list[str] = []

    for number in clean_numbers:
        positions = _try_place_number(grid, number, grid_size, dir_vectors)
        if positions is not None:
            placed_numbers.append({
                "number": number,
                "positions": positions,
            })
        else:
            not_placed.append(number)

    # Build solution grid (only placed digits)
    solution: list[list[str]] = [[""] * grid_size for _ in range(grid_size)]
    for entry in placed_numbers:
        for r, c in entry["positions"]:
            solution[r][c] = grid[r][c]

    # Fill remaining cells with random digits
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == "":
                grid[r][c] = str(random.randint(0, 9))

    content_hash = generate_content_hash({
        "grid": grid,
        "placed_numbers": [p["number"] for p in placed_numbers],
    })

    svg = render_number_search_svg(grid, placed_numbers, grid_size)

    return {
        "grid": grid,
        "placed_numbers": placed_numbers,
        "not_placed": not_placed,
        "solution": solution,
        "content_hash": content_hash,
        "svg": svg,
    }


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------

def render_number_search_svg(grid: list[list[str]],
                              placed_numbers: list[dict[str, Any]],
                              grid_size: int,
                              cell_size: int = 40) -> str:
    """Render the number search grid and number list to SVG."""
    padding = 30
    grid_total = grid_size * cell_size
    # Extra space at the bottom for the number list
    list_height = 60
    width = padding * 2 + grid_total
    height = padding * 2 + grid_total + list_height

    parts: list[str] = [svg_header(width, height)]
    parts.append(svg_rect(0, 0, width, height, fill="white", stroke="none"))

    # Title
    parts.append(svg_text(width // 2, padding - 5, "Number Search",
                          font_size=20, font_weight="bold",
                          font_family="sans-serif"))

    # Grid lines
    gy = padding + 10
    parts.append(svg_grid(grid_size, grid_size, cell_size,
                          offset_x=padding, offset_y=gy))

    # Digits
    font_size = max(12, cell_size // 2)
    for r in range(grid_size):
        for c in range(grid_size):
            cx = padding + c * cell_size + cell_size // 2
            cy = gy + r * cell_size + cell_size // 2
            parts.append(svg_text(cx, cy, grid[r][c], font_size,
                                  font_family="monospace"))

    # Number list at bottom
    list_y = gy + grid_total + 25
    nums_label = "Find: " + "  ".join(p["number"] for p in placed_numbers)
    parts.append(svg_text(width // 2, list_y, nums_label,
                          font_size=14, font_family="sans-serif"))

    parts.append(svg_footer())
    return "".join(parts)
