"""Crossword puzzle generator using intersection-based placement.

Algorithm:
1. Sort words longest first
2. Place first word horizontally in center
3. For each remaining word, find intersecting letters with placed words
4. Score each valid placement (prefer more intersections, balanced grid)
5. Place word at best position
6. If word can't be placed, skip (track unplaced)
7. Determine grid bounds, add black squares
8. Number cells (standard crossword numbering)
9. Calculate difficulty score
10. Generate content hash for duplicate detection
"""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any

DIFFICULTY_PRESETS: dict[str, dict[str, Any]] = {
    "easy": {"max_words": 10, "prefer_short": True},
    "medium": {"max_words": 20, "prefer_short": False},
    "hard": {"max_words": 30, "prefer_short": False},
}


def _sanitize_words(words: list[str]) -> list[str]:
    """Uppercase, strip, deduplicate, alpha-only."""
    seen: set[str] = set()
    result: list[str] = []
    for w in words:
        clean = w.strip().upper()
        if not clean or not clean.isalpha():
            continue
        if clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


class _PlacedWord:
    """Internal record of a word placed on the working grid."""

    __slots__ = ("word", "row", "col", "direction")

    def __init__(self, word: str, row: int, col: int, direction: str) -> None:
        self.word = word
        self.row = row
        self.col = col
        self.direction = direction  # "across" or "down"

    @property
    def positions(self) -> list[tuple[int, int]]:
        dr, dc = (0, 1) if self.direction == "across" else (1, 0)
        return [(self.row + dr * i, self.col + dc * i) for i in range(len(self.word))]


class _WorkingGrid:
    """Unbounded working grid backed by a dict for flexible placement."""

    def __init__(self) -> None:
        self.cells: dict[tuple[int, int], str] = {}
        self.placed: list[_PlacedWord] = []
        # Track which cells are occupied along which axis to prevent parallel adjacency
        self.occupied_across: set[tuple[int, int]] = set()
        self.occupied_down: set[tuple[int, int]] = set()

    def get(self, r: int, c: int) -> str | None:
        return self.cells.get((r, c))

    def _word_cells(self, word: str, row: int, col: int, direction: str) -> list[tuple[int, int, str]]:
        dr, dc = (0, 1) if direction == "across" else (1, 0)
        return [(row + dr * i, col + dc * i, ch) for i, ch in enumerate(word)]

    def can_place(self, word: str, row: int, col: int, direction: str) -> bool:
        """Check if word can be validly placed."""
        cells = self._word_cells(word, row, col, direction)
        dr, dc = (0, 1) if direction == "across" else (1, 0)

        has_intersection = False
        for i, (r, c, ch) in enumerate(cells):
            existing = self.get(r, c)
            if existing is not None:
                if existing != ch:
                    return False
                has_intersection = True
            else:
                # Check perpendicular neighbours — word should not run parallel
                # adjacent to another word in the same direction
                if direction == "across":
                    # Cells above and below should be empty unless they are
                    # part of a crossing (down) word that intersects here
                    for nr in (r - 1, r + 1):
                        if self.get(nr, c) is not None and (nr, c) not in self.occupied_down:
                            # It belongs to an across word → parallel adjacency
                            if (nr, c) in self.occupied_across:
                                return False
                else:
                    for nc in (c - 1, c + 1):
                        if self.get(r, nc) is not None and (r, nc) not in self.occupied_across:
                            if (r, nc) in self.occupied_down:
                                return False

        # Cell before and after word must be empty (no extending existing words)
        before_r, before_c = row - dr, col - dc
        after_r, after_c = row + dr * len(word), col + dc * len(word)
        if self.get(before_r, before_c) is not None:
            return False
        if self.get(after_r, after_c) is not None:
            return False

        # First word doesn't need intersection; all subsequent do
        if self.placed and not has_intersection:
            return False

        return True

    def place(self, word: str, row: int, col: int, direction: str) -> _PlacedWord:
        pw = _PlacedWord(word, row, col, direction)
        for r, c, ch in self._word_cells(word, row, col, direction):
            self.cells[(r, c)] = ch
            if direction == "across":
                self.occupied_across.add((r, c))
            else:
                self.occupied_down.add((r, c))
        self.placed.append(pw)
        return pw

    def intersection_count(self, word: str, row: int, col: int, direction: str) -> int:
        count = 0
        for r, c, ch in self._word_cells(word, row, col, direction):
            if self.get(r, c) == ch:
                count += 1
        return count

    def bounds(self) -> tuple[int, int, int, int]:
        """Return (min_row, min_col, max_row, max_col)."""
        if not self.cells:
            return (0, 0, 0, 0)
        rows = [r for r, _ in self.cells]
        cols = [c for _, c in self.cells]
        return (min(rows), min(cols), max(rows), max(cols))


def _find_placements(
    grid: _WorkingGrid, word: str
) -> list[tuple[int, int, str, int]]:
    """Find all valid placements for *word*, returning (row, col, direction, intersections)."""
    candidates: list[tuple[int, int, str, int]] = []

    for pw in grid.placed:
        for i, ch_placed in enumerate(pw.word):
            for j, ch_new in enumerate(word):
                if ch_placed != ch_new:
                    continue
                # Try perpendicular placement
                if pw.direction == "across":
                    # Place new word going down, crossing at pw's i-th letter
                    r_start = pw.row - j
                    c_start = pw.col + i
                    direction = "down"
                else:
                    r_start = pw.row + i
                    c_start = pw.col - j
                    direction = "across"

                if grid.can_place(word, r_start, c_start, direction):
                    ix = grid.intersection_count(word, r_start, c_start, direction)
                    candidates.append((r_start, c_start, direction, ix))

    return candidates


def _number_cells(
    placed_words: list[_PlacedWord],
    min_row: int,
    min_col: int,
) -> dict[tuple[int, int], int]:
    """Assign standard crossword numbers to cells.

    A cell gets a number if it starts an Across or Down word.
    """
    starts: set[tuple[int, int]] = set()
    for pw in placed_words:
        starts.add((pw.row, pw.col))

    sorted_starts = sorted(starts, key=lambda rc: (rc[0] - min_row, rc[1] - min_col))
    numbering: dict[tuple[int, int], int] = {}
    for idx, pos in enumerate(sorted_starts, start=1):
        numbering[pos] = idx
    return numbering


def _difficulty_score(
    grid_rows: int,
    grid_cols: int,
    placed: list[_PlacedWord],
    filled_cells: int,
    total_cells: int,
    clues: dict[str, str] | None,
) -> int:
    """Calculate difficulty 0-100.

    Factors: black-square density, avg word length, clue grade level proxy.
    """
    black_squares = total_cells - filled_cells
    black_density = black_squares / total_cells if total_cells > 0 else 0

    avg_word_len = (
        sum(len(pw.word) for pw in placed) / len(placed) if placed else 0
    )
    # Normalise avg word length: 3=0, 15=100
    word_len_score = min(100, max(0, (avg_word_len - 3) / 12 * 100))

    # Simple clue complexity proxy: average clue length in characters
    clue_score = 0.0
    if clues:
        placed_words_set = {pw.word for pw in placed}
        relevant = [v for k, v in clues.items() if k.upper() in placed_words_set]
        if relevant:
            avg_clue_len = sum(len(c) for c in relevant) / len(relevant)
            clue_score = min(100, avg_clue_len / 80 * 100)

    score = int(black_density * 40 + word_len_score * 0.35 + clue_score * 0.25)
    return max(0, min(100, score))


def _content_hash(grid: list[list[str | None]], words: list[str]) -> str:
    payload = json.dumps({"grid": grid, "words": sorted(words)}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def generate_crossword(
    words: list[str],
    clues: dict[str, str] | None = None,
    difficulty: str = "medium",
    seed: int | None = None,
) -> dict:
    """Generate a crossword puzzle.

    Parameters
    ----------
    words:
        Raw word list.
    clues:
        Optional mapping of word -> clue text.  Keys are case-insensitive.
    difficulty:
        Preset name (easy / medium / hard).
    seed:
        Optional RNG seed for reproducibility.

    Returns
    -------
    dict with keys: grid, size, words, solution, across_clues, down_clues,
                    difficulty_score, content_hash, unplaced_words
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    clean_words = _sanitize_words(words)
    if not clean_words:
        raise ValueError("No valid words provided after sanitization.")

    # Sort longest first
    clean_words.sort(key=len, reverse=True)

    # Normalise clues dict
    norm_clues: dict[str, str] = {}
    if clues:
        for k, v in clues.items():
            norm_clues[k.strip().upper()] = v

    wg = _WorkingGrid()

    # Place first word horizontally at origin
    first = clean_words[0]
    wg.place(first, 0, 0, "across")

    unplaced: list[str] = []
    remaining = clean_words[1:]
    rng.shuffle(remaining)

    for word in remaining:
        candidates = _find_placements(wg, word)
        if not candidates:
            unplaced.append(word)
            continue
        # Score: prefer more intersections, then balanced position
        candidates.sort(key=lambda c: -c[3])
        best = candidates[0]
        wg.place(word, best[0], best[1], best[2])

    # Build output grid
    min_r, min_c, max_r, max_c = wg.bounds()
    rows = max_r - min_r + 1
    cols = max_c - min_c + 1

    grid: list[list[str | None]] = [[None for _ in range(cols)] for _ in range(rows)]
    solution: list[list[str | None]] = [[None for _ in range(cols)] for _ in range(rows)]

    for (r, c), ch in wg.cells.items():
        grid[r - min_r][c - min_c] = ""  # empty cell for solver
        solution[r - min_r][c - min_c] = ch

    numbering = _number_cells(wg.placed, min_r, min_c)

    # Build word records and clue dicts
    across_clues: dict[int, str] = {}
    down_clues: dict[int, str] = {}
    word_records: list[dict] = []

    for pw in wg.placed:
        num = numbering.get((pw.row, pw.col), 0)
        clue_text = norm_clues.get(pw.word, f"Clue for {pw.word}")
        record = {
            "word": pw.word,
            "row": pw.row - min_r,
            "col": pw.col - min_c,
            "direction": pw.direction,
            "number": num,
            "clue": clue_text,
        }
        word_records.append(record)
        if pw.direction == "across":
            across_clues[num] = clue_text
        else:
            down_clues[num] = clue_text

    total_cells = rows * cols
    filled_cells = len(wg.cells)

    score = _difficulty_score(rows, cols, wg.placed, filled_cells, total_cells, norm_clues)
    chash = _content_hash(solution, [pw.word for pw in wg.placed])

    return {
        "grid": grid,
        "size": {"rows": rows, "cols": cols},
        "words": word_records,
        "solution": solution,
        "across_clues": across_clues,
        "down_clues": down_clues,
        "difficulty_score": score,
        "content_hash": chash,
        "unplaced_words": unplaced,
    }
