"""Sudoku generator using generate-and-remove algorithm."""

from __future__ import annotations

import hashlib
import json
import random

GIVENS_TARGETS = {
    (4, "easy"): (10, 12),
    (4, "medium"): (7, 9),
    (4, "hard"): (5, 6),
    (6, "easy"): (20, 24),
    (6, "medium"): (15, 19),
    (6, "hard"): (10, 14),
    (9, "easy"): (36, 45),
    (9, "medium"): (27, 35),
    (9, "hard"): (22, 26),
}
VALID_GRID_SIZES = (4, 6, 9)


def _box_dims(size):
    if size == 4:
        return 2, 2
    if size == 6:
        return 2, 3
    if size == 9:
        return 3, 3
    raise ValueError(f"Unsupported grid size: {size}")


def _is_valid(grid, row, col, num, size, box_r, box_c):
    if num in grid[row]:
        return False
    for r in range(size):
        if grid[r][col] == num:
            return False
    br, bc = (row // box_r) * box_r, (col // box_c) * box_c
    for r in range(br, br + box_r):
        for c in range(bc, bc + box_c):
            if grid[r][c] == num:
                return False
    return True


def _generate_solution(size, rng):
    box_r, box_c = _box_dims(size)
    grid = [[0] * size for _ in range(size)]
    nums = list(range(1, size + 1))
    for bi in range(0, size, box_r if box_r == box_c else min(box_r, box_c)):
        if bi + box_r > size or bi + box_c > size:
            break
        sh = nums[:]
        rng.shuffle(sh)
        idx = 0
        for r in range(bi, bi + box_r):
            for c in range(bi, bi + box_c):
                grid[r][c] = sh[idx]
                idx += 1
    if _solve(grid, size, box_r, box_c, rng):
        return grid
    grid = [[0] * size for _ in range(size)]
    _solve(grid, size, box_r, box_c, rng)
    return grid


def _solve(grid, size, box_r, box_c, rng=None):
    for r in range(size):
        for c in range(size):
            if grid[r][c] == 0:
                nums = list(range(1, size + 1))
                if rng:
                    rng.shuffle(nums)
                for num in nums:
                    if _is_valid(grid, r, c, num, size, box_r, box_c):
                        grid[r][c] = num
                        if _solve(grid, size, box_r, box_c, rng):
                            return True
                        grid[r][c] = 0
                return False
    return True


def _count_solutions(grid, size, box_r, box_c, limit=2):
    counter = [0]

    def bt():
        for r in range(size):
            for c in range(size):
                if grid[r][c] == 0:
                    for num in range(1, size + 1):
                        if _is_valid(grid, r, c, num, size, box_r, box_c):
                            grid[r][c] = num
                            if bt():
                                return True
                            grid[r][c] = 0
                    return False
        counter[0] += 1
        return counter[0] >= limit

    bt()
    return counter[0]


def _has_unique(grid, size, box_r, box_c):
    return _count_solutions([r[:] for r in grid], size, box_r, box_c, 2) == 1


def generate_sudoku(grid_size=9, difficulty="medium", seed=None):
    """Generate a Sudoku puzzle with a guaranteed unique solution."""
    if grid_size not in VALID_GRID_SIZES:
        raise ValueError(f"grid_size must be one of {VALID_GRID_SIZES}")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy/medium/hard")
    rng = random.Random(seed)
    box_r, box_c = _box_dims(grid_size)
    solution = _generate_solution(grid_size, rng)
    puzzle = [r[:] for r in solution]
    mn, mx = GIVENS_TARGETS[(grid_size, difficulty)]
    target = rng.randint(mn, mx)
    current = grid_size * grid_size
    cells = [(r, c) for r in range(grid_size) for c in range(grid_size)]
    rng.shuffle(cells)
    for r, c in cells:
        if current <= target:
            break
        if puzzle[r][c] == 0:
            continue
        saved = puzzle[r][c]
        puzzle[r][c] = 0
        if _has_unique(puzzle, grid_size, box_r, box_c):
            current -= 1
        else:
            puzzle[r][c] = saved
    gc = sum(1 for r in range(grid_size) for c in range(grid_size) if puzzle[r][c] != 0)
    tc = grid_size * grid_size
    er = (tc - gc) / tc
    base = {"easy": 10, "medium": 40, "hard": 70}.get(difficulty, 40)
    score = max(0, min(100, int(base + er * 30)))
    ch = hashlib.sha256(
        json.dumps({"grid": puzzle, "solution": solution, "size": grid_size}, sort_keys=True).encode()
    ).hexdigest()
    return {
        "grid": puzzle,
        "size": grid_size,
        "solution": solution,
        "givens_count": gc,
        "difficulty_score": score,
        "has_unique_solution": True,
        "content_hash": ch,
    }
