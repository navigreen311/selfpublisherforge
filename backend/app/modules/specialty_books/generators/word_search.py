"""Word Search puzzle generator using backtracking placement.

Algorithm:
1. Sanitize word list (uppercase, strip, deduplicate)
2. Create empty grid of grid_size x grid_size
3. For each word, try random position + direction
4. Check conflicts (overlap OK if same letter at position)
5. Backtrack if placement fails after N attempts
6. Fill remaining cells with random letters
7. Calculate difficulty score (0-100)
8. Generate content hash for duplicate detection
"""

from __future__ import annotations

import hashlib
import json
import random
import string
from typing import Any

# Direction vectors: (row_delta, col_delta)
DIRECTION_MAP = {
    "RIGHT": (0, 1),
    "DOWN": (1, 0),
    "DIAG_RIGHT_DOWN": (1, 1),
    "DIAG_LEFT_DOWN": (1, -1),
    "LEFT": (0, -1),
    "UP": (-1, 0),
    "DIAG_RIGHT_UP": (-1, 1),
    "DIAG_LEFT_UP": (-1, -1),
}

DIRECTION_SETS: dict[int, list[str]] = {
    2: ["RIGHT", "DOWN"],
    4: ["RIGHT", "DOWN", "DIAG_RIGHT_DOWN", "DIAG_LEFT_DOWN"],
    8: list(DIRECTION_MAP.keys()),
}

DIFFICULTY_PRESETS: dict[str, dict[str, Any]] = {
    "easy": {"grid_size": 10, "directions": 2},
    "medium": {"grid_size": 15, "directions": 4},
    "hard": {"grid_size": 20, "directions": 8},
}

MAX_PLACEMENT_ATTEMPTS = 200


def _sanitize_words(words: list[str], grid_size: int) -> list[str]:
    """Uppercase, strip, deduplicate, and filter words that exceed grid size."""
    seen: set[str] = set()
    sanitized: list[str] = []
    for w in words:
        clean = w.strip().upper()
        if not clean or not clean.isalpha():
            continue
        if len(clean) > grid_size:
            continue
        if clean not in seen:
            seen.add(clean)
            sanitized.append(clean)
    return sanitized


def _can_place(
    grid: list[list[str]],
    word: str,
    row: int,
    col: int,
    dr: int,
    dc: int,
    grid_size: int,
) -> bool:
    """Check if *word* fits starting at (row, col) in direction (dr, dc)."""
    for i, ch in enumerate(word):
        r = row + dr * i
        c = col + dc * i
        if r < 0 or r >= grid_size or c < 0 or c >= grid_size:
            return False
        if grid[r][c] != "" and grid[r][c] != ch:
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
    """Place *word* on *grid* and return the list of (row, col) positions."""
    positions: list[tuple[int, int]] = []
    for i, ch in enumerate(word):
        r = row + dr * i
        c = col + dc * i
        grid[r][c] = ch
        positions.append((r, c))
    return positions


def _count_overlaps(
    grid: list[list[str]],
    word: str,
    row: int,
    col: int,
    dr: int,
    dc: int,
) -> int:
    """Count how many letters of *word* overlap with already-placed letters."""
    overlaps = 0
    for i, ch in enumerate(word):
        r = row + dr * i
        c = col + dc * i
        if grid[r][c] == ch:
            overlaps += 1
    return overlaps


def _difficulty_score(
    grid_size: int,
    directions: int,
    words: list[str],
    solution: dict[str, list[tuple[int, int]]],
    total_cells: int,
) -> int:
    """Calculate a difficulty score from 0-100.

    Factors:
    - Grid density (total word-letter cells / total grid cells)
    - Direction count (more directions = harder)
    - Word overlap rate (higher overlap = harder to distinguish)
    """
    # Grid density: ratio of cells occupied by words to total cells
    occupied: set[tuple[int, int]] = set()
    for positions in solution.values():
        for pos in positions:
            occupied.add(pos)
    density = len(occupied) / total_cells if total_cells > 0 else 0

    # Direction score
    dir_score = (directions / 8) * 100

    # Overlap rate
    total_word_letters = sum(len(w) for w in words)
    overlap_letters = total_word_letters - len(occupied) if total_word_letters > len(occupied) else 0
    overlap_rate = overlap_letters / total_word_letters if total_word_letters > 0 else 0

    # Weighted combination
    score = int(density * 30 + dir_score * 0.4 + overlap_rate * 30)
    return max(0, min(100, score))


def _content_hash(grid: list[list[str]], words: list[str]) -> str:
    """SHA-256 hash of grid + sorted word list for duplicate detection."""
    payload = json.dumps({"grid": grid, "words": sorted(words)}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def generate_word_search(
    words: list[str],
    grid_size: int = 15,
    directions: int = 4,
    difficulty: str = "medium",
    seed: int | None = None,
) -> dict:
    """Generate a word search puzzle.

    Parameters
    ----------
    words:
        Raw word list (will be sanitized).
    grid_size:
        Grid dimension (10, 15, or 20 recommended).
    directions:
        Number of allowed directions (2, 4, or 8).
    difficulty:
        Preset name; overridden if grid_size/directions are explicitly given.
    seed:
        Optional RNG seed for reproducibility.

    Returns
    -------
    dict with keys: grid, words, solution, difficulty_score, content_hash
    """
    rng = random.Random(seed) if seed is not None else random.Random()

    # Apply preset defaults only when caller uses default grid_size/directions
    preset = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS["medium"])
    if grid_size == 15 and directions == 4:
        grid_size = preset["grid_size"]
        directions = preset["directions"]

    # Validate directions
    if directions not in DIRECTION_SETS:
        directions = 4
    allowed_dirs = DIRECTION_SETS[directions]

    # Sanitize
    clean_words = _sanitize_words(words, grid_size)
    if not clean_words:
        raise ValueError("No valid words provided after sanitization.")

    # Sort longest first for better placement
    clean_words.sort(key=len, reverse=True)

    # Create empty grid
    grid: list[list[str]] = [["" for _ in range(grid_size)] for _ in range(grid_size)]
    solution: dict[str, list[tuple[int, int]]] = {}
    placed_words: list[str] = []
    unplaced_words: list[str] = []

    for word in clean_words:
        placed = False
        for _ in range(MAX_PLACEMENT_ATTEMPTS):
            direction_name = rng.choice(allowed_dirs)
            dr, dc = DIRECTION_MAP[direction_name]
            row = rng.randint(0, grid_size - 1)
            col = rng.randint(0, grid_size - 1)
            if _can_place(grid, word, row, col, dr, dc, grid_size):
                positions = _place_word(grid, word, row, col, dr, dc)
                solution[word] = positions
                placed_words.append(word)
                placed = True
                break
        if not placed:
            unplaced_words.append(word)

    # Fill remaining cells with random uppercase letters
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == "":
                grid[r][c] = rng.choice(string.ascii_uppercase)

    total_cells = grid_size * grid_size
    score = _difficulty_score(grid_size, directions, placed_words, solution, total_cells)
    chash = _content_hash(grid, placed_words)

    # Convert solution positions to plain list-of-lists for JSON serialisation
    serialisable_solution = {w: [list(p) for p in pos] for w, pos in solution.items()}

    return {
        "grid": grid,
        "grid_size": grid_size,
        "words": placed_words,
        "unplaced_words": unplaced_words,
        "solution": serialisable_solution,
        "difficulty_score": score,
        "content_hash": chash,
        "directions": directions,
    }
