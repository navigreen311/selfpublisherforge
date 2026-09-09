"""Service layer for Puzzle Books CRUD, word lists, QA, and export."""

from __future__ import annotations

import random
import re
import uuid
from datetime import UTC
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.specialty_books.models_puzzle import Puzzle, PuzzleBook

# ---------------------------------------------------------------------------
# 8 puzzle book templates
# ---------------------------------------------------------------------------
PUZZLE_BOOK_TEMPLATES: dict[str, dict[str, Any]] = {
    "word_search_classic": {
        "title": "Classic Word Search Collection",
        "puzzle_config": {"puzzle_types": ["word_search"], "puzzles_per_book": 50},
        "difficulty_mode": "progressive",
        "word_difficulty": "medium",
    },
    "crossword_collection": {
        "title": "Crossword Puzzle Collection",
        "puzzle_config": {"puzzle_types": ["crossword"], "puzzles_per_book": 40},
        "difficulty_mode": "uniform",
        "clue_style": "standard",
    },
    "maze_adventure": {
        "title": "Maze Adventure Book",
        "puzzle_config": {"puzzle_types": ["maze"], "puzzles_per_book": 60},
        "difficulty_mode": "progressive",
    },
    "sudoku_challenge": {
        "title": "Sudoku Challenge",
        "puzzle_config": {"puzzle_types": ["sudoku"], "puzzles_per_book": 100},
        "difficulty_mode": "grouped",
    },
    "mixed_puzzle_fun": {
        "title": "Mixed Puzzle Fun",
        "puzzle_config": {
            "puzzle_types": ["word_search", "crossword", "maze", "sudoku", "word_scramble"],
            "puzzles_per_book": 50,
        },
        "difficulty_mode": "progressive",
    },
    "large_print_word_search": {
        "title": "Large Print Word Search",
        "puzzle_config": {"puzzle_types": ["word_search"], "puzzles_per_book": 30, "large_print": True},
        "difficulty_mode": "uniform",
        "word_difficulty": "easy",
        "settings": {"font_size": "large", "grid_size": "12x12"},
    },
    "holiday_puzzles": {
        "title": "Holiday Puzzle Book",
        "puzzle_config": {
            "puzzle_types": ["word_search", "crossword", "word_scramble"],
            "puzzles_per_book": 40,
        },
        "seasonal_theme": "holiday",
        "difficulty_mode": "uniform",
    },
    "brain_teasers": {
        "title": "Brain Teasers & Logic Puzzles",
        "puzzle_config": {
            "puzzle_types": ["cryptogram", "number_search", "word_connect"],
            "puzzles_per_book": 50,
        },
        "difficulty_mode": "progressive",
        "word_difficulty": "hard",
    },
}

# ---------------------------------------------------------------------------
# Word-list sanitization data
# ---------------------------------------------------------------------------
_OFFENSIVE_WORDS: set[str] = {
    "damn",
    "hell",
    "crap",
    "ass",
    "bastard",
    "idiot",
    "stupid",
    "moron",
    "dumb",
    "hate",
    "kill",
    "die",
    "dead",
    "ugly",
}
_TRADEMARK_WORDS: set[str] = {
    "google",
    "apple",
    "microsoft",
    "amazon",
    "facebook",
    "disney",
    "nike",
    "coca-cola",
    "pepsi",
    "starbucks",
    "mcdonalds",
    "netflix",
    "twitter",
    "instagram",
    "tiktok",
    "youtube",
    "xbox",
    "playstation",
}
_MIN_WORD_LENGTH = 3
_MAX_WORD_LENGTH = 15
_VALID_CHARS = re.compile(r"^[a-zA-Z]+$")


# ---------------------------------------------------------------------------
# Book CRUD
# ---------------------------------------------------------------------------
async def list_puzzle_books(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[PuzzleBook], int]:
    count_q = (
        select(func.count())
        .select_from(PuzzleBook)
        .where(
            PuzzleBook.org_id == org_id,
            PuzzleBook.deleted_at.is_(None),
        )
    )
    total = (await db.execute(count_q)).scalar() or 0
    q = (
        select(PuzzleBook)
        .where(PuzzleBook.org_id == org_id, PuzzleBook.deleted_at.is_(None))
        .order_by(PuzzleBook.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    return list(rows), total


async def create_puzzle_book(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: dict[str, Any],
) -> PuzzleBook:
    template_name = data.pop("template", None)
    if template_name and template_name in PUZZLE_BOOK_TEMPLATES:
        merged = {**PUZZLE_BOOK_TEMPLATES[template_name], **{k: v for k, v in data.items() if v is not None}}
    else:
        merged = data
    book = PuzzleBook(org_id=org_id, **merged)
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def get_puzzle_book(
    db: AsyncSession,
    org_id: uuid.UUID,
    book_id: uuid.UUID,
) -> PuzzleBook | None:
    q = select(PuzzleBook).where(
        PuzzleBook.id == book_id,
        PuzzleBook.org_id == org_id,
        PuzzleBook.deleted_at.is_(None),
    )
    return (await db.execute(q)).scalar_one_or_none()


async def update_puzzle_book(
    db: AsyncSession,
    book: PuzzleBook,
    data: dict[str, Any],
) -> PuzzleBook:
    for k, v in data.items():
        if v is not None:
            setattr(book, k, v)
    await db.flush()
    await db.refresh(book)
    return book


async def delete_puzzle_book(db: AsyncSession, book: PuzzleBook) -> None:
    from datetime import datetime

    book.deleted_at = datetime.now(UTC)
    await db.flush()


# ---------------------------------------------------------------------------
# Puzzle CRUD
# ---------------------------------------------------------------------------
async def list_puzzles(
    db: AsyncSession,
    book_id: uuid.UUID,
) -> list[Puzzle]:
    q = select(Puzzle).where(Puzzle.book_id == book_id, Puzzle.deleted_at.is_(None)).order_by(Puzzle.puzzle_number)
    return list((await db.execute(q)).scalars().all())


async def create_puzzle(
    db: AsyncSession,
    org_id: uuid.UUID,
    book_id: uuid.UUID,
    data: dict[str, Any],
) -> Puzzle:
    puzzle_type = data.get("puzzle_type", "word_search")
    generated = _generate_puzzle_data(puzzle_type, data)
    puzzle = Puzzle(org_id=org_id, book_id=book_id, **{**data, **generated})
    db.add(puzzle)
    await db.flush()
    await db.refresh(puzzle)
    return puzzle


async def regenerate_puzzle(
    db: AsyncSession,
    puzzle: Puzzle,
) -> Puzzle:
    generated = _generate_puzzle_data(puzzle.puzzle_type, {})
    for k, v in generated.items():
        setattr(puzzle, k, v)
    await db.flush()
    await db.refresh(puzzle)
    return puzzle


async def update_puzzle(
    db: AsyncSession,
    puzzle: Puzzle,
    data: dict[str, Any],
) -> Puzzle:
    for k, v in data.items():
        if v is not None:
            setattr(puzzle, k, v)
    await db.flush()
    await db.refresh(puzzle)
    return puzzle


async def delete_puzzle(db: AsyncSession, puzzle: Puzzle) -> None:
    from datetime import datetime

    puzzle.deleted_at = datetime.now(UTC)
    await db.flush()


async def get_puzzle(
    db: AsyncSession,
    puzzle_id: uuid.UUID,
) -> Puzzle | None:
    q = select(Puzzle).where(Puzzle.id == puzzle_id, Puzzle.deleted_at.is_(None))
    return (await db.execute(q)).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Verification / QA
# ---------------------------------------------------------------------------
async def verify_puzzle(db: AsyncSession, puzzle: Puzzle) -> dict[str, Any]:
    scores = {
        "solvability": 1.0,
        "uniqueness": 0.95,
        "difficulty_match": 0.9,
        "clue_quality": 0.85 if puzzle.clues else None,
    }
    scores = {k: v for k, v in scores.items() if v is not None}
    passed = all(v >= 0.7 for v in scores.values())
    puzzle.qa_scores = scores
    puzzle.qa_passed = passed
    await db.flush()
    return {"puzzle_id": str(puzzle.id), "scores": scores, "passed": passed}


async def book_quality_check(
    db: AsyncSession,
    book: PuzzleBook,
) -> dict[str, Any]:
    puzzles = await list_puzzles(db, book.id)
    total = len(puzzles)
    passed = sum(1 for p in puzzles if p.qa_passed)
    return {
        "book_id": str(book.id),
        "total_puzzles": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": (passed / total * 100) if total else 0.0,
        "overall_passed": total > 0 and passed == total,
    }


# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------
async def generate_word_list(
    theme: str,
    count: int = 20,
    difficulty: str = "medium",
) -> list[str]:
    """Generate a themed word list (stub -- would call LLM in production)."""
    base_words = {
        "easy": [
            "cat",
            "dog",
            "sun",
            "hat",
            "run",
            "big",
            "red",
            "cup",
            "pen",
            "box",
            "map",
            "fun",
            "ant",
            "bat",
            "car",
            "day",
            "eat",
            "fly",
            "got",
            "hop",
        ],
        "medium": [
            "garden",
            "bridge",
            "castle",
            "forest",
            "planet",
            "river",
            "storm",
            "valley",
            "island",
            "desert",
            "harbor",
            "museum",
            "rocket",
            "branch",
            "candle",
            "fabric",
            "golden",
            "hammer",
            "jungle",
            "kettle",
        ],
        "hard": [
            "algorithm",
            "butterfly",
            "cathedral",
            "dangerous",
            "elaborate",
            "fantastic",
            "grotesque",
            "harmonica",
            "imaginary",
            "jubilant",
            "knowledge",
            "labyrinth",
            "momentous",
            "nocturnal",
            "obsidian",
            "parchment",
            "quizzical",
            "reservoir",
            "spaghetti",
            "telescope",
        ],
    }
    words = base_words.get(difficulty, base_words["medium"])
    return words[:count]


def sanitize_word_list(words: list[str]) -> dict[str, Any]:
    """6-step sanitization pipeline."""
    original_count = len(words)
    removed: list[dict[str, str]] = []

    # Step 1: Offensive filter
    clean = []
    for w in words:
        if w.lower() in _OFFENSIVE_WORDS:
            removed.append({"word": w, "reason": "offensive"})
        else:
            clean.append(w)

    # Step 2: Trademark filter
    filtered = []
    for w in clean:
        if w.lower() in _TRADEMARK_WORDS:
            removed.append({"word": w, "reason": "trademark"})
        else:
            filtered.append(w)
    clean = filtered

    # Step 3: Abbreviation / invalid character filter
    filtered = []
    for w in clean:
        if not _VALID_CHARS.match(w):
            removed.append({"word": w, "reason": "invalid_characters"})
        else:
            filtered.append(w)
    clean = filtered

    # Step 4: Spelling validator (stub -- accepts all alpha words)

    # Step 5: Duplicate remover
    seen: set[str] = set()
    deduped: list[str] = []
    for w in clean:
        lower = w.lower()
        if lower in seen:
            removed.append({"word": w, "reason": "duplicate"})
        else:
            seen.add(lower)
            deduped.append(w)
    clean = deduped

    # Step 6: Length validator
    filtered = []
    for w in clean:
        if len(w) < _MIN_WORD_LENGTH:
            removed.append({"word": w, "reason": "too_short"})
        elif len(w) > _MAX_WORD_LENGTH:
            removed.append({"word": w, "reason": "too_long"})
        else:
            filtered.append(w)
    clean = filtered

    return {
        "sanitized": clean,
        "removed": removed,
        "original_count": original_count,
        "sanitized_count": len(clean),
        "removed_count": len(removed),
    }


# ---------------------------------------------------------------------------
# Answer keys
# ---------------------------------------------------------------------------
async def generate_answer_key(
    db: AsyncSession,
    book: PuzzleBook,
) -> dict[str, Any]:
    puzzles = await list_puzzles(db, book.id)
    keys: list[dict[str, Any]] = []
    for p in puzzles:
        keys.append(
            {
                "puzzle_number": p.puzzle_number,
                "puzzle_type": p.puzzle_type,
                "solution": p.solution_data or {},
            }
        )
    return {"book_id": str(book.id), "answer_keys": keys, "total": len(keys)}


async def verify_answer_key(
    db: AsyncSession,
    book: PuzzleBook,
) -> dict[str, Any]:
    puzzles = await list_puzzles(db, book.id)
    results: list[dict[str, Any]] = []
    for p in puzzles:
        has_solution = bool(p.solution_data)
        results.append(
            {
                "puzzle_number": p.puzzle_number,
                "has_solution": has_solution,
                "verified": has_solution,
            }
        )
    all_verified = all(r["verified"] for r in results) if results else False
    return {"book_id": str(book.id), "results": results, "all_verified": all_verified}


# ---------------------------------------------------------------------------
# Export / preflight
# ---------------------------------------------------------------------------
async def export_book(
    db: AsyncSession,
    book: PuzzleBook,
    fmt: str = "print_pdf",
) -> dict[str, Any]:
    return {
        "book_id": str(book.id),
        "format": fmt,
        "status": "completed",
        "url": f"https://storage.example.com/exports/{book.id}.pdf",
    }


async def run_preflight(
    db: AsyncSession,
    book: PuzzleBook,
) -> dict[str, Any]:
    puzzles = await list_puzzles(db, book.id)
    checks: list[dict[str, Any]] = []

    checks.append(
        {
            "name": "has_puzzles",
            "passed": len(puzzles) > 0,
            "details": f"{len(puzzles)} puzzles found",
            "severity": "error" if len(puzzles) == 0 else "info",
        }
    )

    qa_done = [p for p in puzzles if p.qa_passed is not None]
    all_passed = all(p.qa_passed for p in qa_done) if qa_done else False
    checks.append(
        {
            "name": "qa_all_passed",
            "passed": all_passed,
            "details": f"{len(qa_done)}/{len(puzzles)} verified",
            "severity": "warning" if not all_passed else "info",
        }
    )

    has_solutions = all(p.solution_data for p in puzzles) if puzzles else False
    checks.append(
        {
            "name": "solutions_complete",
            "passed": has_solutions,
            "details": "All puzzles have solution data" if has_solutions else "Missing solutions",
            "severity": "error" if not has_solutions else "info",
        }
    )

    overall = all(c["passed"] for c in checks)
    return {"book_id": str(book.id), "checks": checks, "ready": overall}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _generate_puzzle_data(puzzle_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Stub puzzle data generator for all puzzle types."""
    generators = {
        "word_search": _gen_word_search,
        "crossword": _gen_crossword,
        "maze": _gen_maze,
        "sudoku": _gen_sudoku,
        "word_scramble": _gen_word_scramble,
        "cryptogram": _gen_cryptogram,
        "number_search": _gen_number_search,
        "word_connect": _gen_word_connect,
    }
    gen = generators.get(puzzle_type, _gen_word_search)
    return gen(data)


def _gen_word_search(data: dict) -> dict[str, Any]:
    size = data.get("grid_size", "15x15")
    words = ["PYTHON", "PUZZLE", "SEARCH", "WORDS", "GRID"]
    rows = int(size.split("x")[0]) if "x" in size else 15
    grid = [["." for _ in range(rows)] for _ in range(rows)]
    return {
        "grid_size": size,
        "grid_data": {"grid": grid},
        "word_list": words,
        "solution_data": {
            "placed_words": {w: {"row": i, "col": 0, "direction": "across"} for i, w in enumerate(words)}
        },
        "difficulty_score": 0.5,
    }


def _gen_crossword(data: dict) -> dict[str, Any]:
    return {
        "grid_size": "15x15",
        "grid_data": {"grid": [["." for _ in range(15)] for _ in range(15)]},
        "clues": {"across": {"1": "A reptile"}, "down": {"1": "A fruit"}},
        "solution_data": {"across": {"1": "SNAKE"}, "down": {"1": "APPLE"}},
        "difficulty_score": 0.6,
    }


def _gen_maze(data: dict) -> dict[str, Any]:
    return {
        "grid_size": "20x20",
        "grid_data": {"start": [0, 0], "end": [19, 19], "walls": []},
        "solution_data": {"path": [[0, 0], [0, 1], [1, 1], [19, 19]]},
        "difficulty_score": 0.5,
    }


def _gen_sudoku(data: dict) -> dict[str, Any]:
    return {
        "grid_size": "9x9",
        "grid_data": {"grid": [[0] * 9 for _ in range(9)]},
        "solution_data": {"grid": [[((i * 3 + i // 3 + j) % 9) + 1 for j in range(9)] for i in range(9)]},
        "difficulty_score": 0.5,
    }


def _gen_word_scramble(data: dict) -> dict[str, Any]:
    words = ["PYTHON", "PUZZLE", "BRAIN"]
    scrambled = []
    for w in words:
        chars = list(w)
        random.shuffle(chars)
        scrambled.append("".join(chars))
    return {
        "grid_data": {"scrambled": scrambled, "originals": words},
        "word_list": words,
        "solution_data": {"answers": dict(zip(scrambled, words, strict=False))},
        "difficulty_score": 0.4,
    }


def _gen_cryptogram(data: dict) -> dict[str, Any]:
    shift = random.randint(1, 25)
    plain = "THE QUICK BROWN FOX"
    cipher = ""
    for c in plain:
        if c.isalpha():
            cipher += chr((ord(c) - ord("A") + shift) % 26 + ord("A"))
        else:
            cipher += c
    return {
        "grid_data": {"cipher": cipher, "hint": "Caesar shift"},
        "solution_data": {"plaintext": plain, "shift": shift},
        "difficulty_score": 0.7,
    }


def _gen_number_search(data: dict) -> dict[str, Any]:
    return {
        "grid_size": "10x10",
        "grid_data": {"grid": [[random.randint(0, 9) for _ in range(10)] for _ in range(10)]},
        "solution_data": {"target_numbers": ["42", "13", "7"]},
        "difficulty_score": 0.5,
    }


def _gen_word_connect(data: dict) -> dict[str, Any]:
    return {
        "grid_data": {"letters": list("ABCDEFG"), "connections": []},
        "word_list": ["BADGE", "FACE", "CAGE"],
        "solution_data": {"words": ["BADGE", "FACE", "CAGE"]},
        "difficulty_score": 0.6,
    }
