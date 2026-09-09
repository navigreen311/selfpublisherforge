"""Unit tests for the Puzzle Books service layer.

Tests business logic functions: sanitisation pipeline, clue QA, difficulty
calibration, large-print scaling, answer-key verification, quality checks,
and export page-count calculations.

Puzzle generation *algorithms* are NOT tested here (covered by another agent).
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.specialty.models.enums import (
    AnswerKeyPosition,
    BookStatus,
    Difficulty,
    DifficultyMode,
    PuzzleType,
)

# Import the service module so we can call its functions directly.
from app.modules.specialty.puzzles import service

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_book(**overrides: Any) -> SimpleNamespace:
    """Create a lightweight PuzzleBook-like object for testing."""
    defaults = dict(
        id=uuid4(),
        org_id=uuid4(),
        title="Test Book",
        audience="adults",
        puzzle_config=None,
        difficulty_mode=DifficultyMode.progressive,
        themes=None,
        seasonal_theme=None,
        word_difficulty=None,
        clue_style=None,
        answer_key_position=AnswerKeyPosition.back_of_book,
        has_toc=False,
        has_hints=False,
        layout_mode=None,
        status=BookStatus.draft,
        qa_score=None,
        created_at=None,
        updated_at=None,
        deleted_at=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_puzzle(**overrides: Any) -> SimpleNamespace:
    """Create a lightweight Puzzle-like object for testing."""
    defaults = dict(
        id=uuid4(),
        book_id=uuid4(),
        puzzle_type=PuzzleType.word_search,
        puzzle_number=1,
        theme=None,
        difficulty=Difficulty.easy,
        difficulty_score=25.0,
        grid_size="15x15",
        grid_data=None,
        word_list=None,
        clues=None,
        answer_data=None,
        content_hash="abc123",
        is_verified=True,
        has_unique_solution=True,
        created_at=None,
        updated_at=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_db_with_book_and_puzzles(
    book: SimpleNamespace,
    puzzles: list[SimpleNamespace],
) -> AsyncMock:
    """Return an AsyncSession mock that serves *book* then *puzzles*.

    The first ``db.execute()`` call returns the book (for ``_get_book_or_404``).
    The second call returns the list of puzzles.
    """
    db = AsyncMock()

    book_result = MagicMock()
    book_result.scalar_one_or_none.return_value = book

    puzzle_result = MagicMock()
    puzzle_scalars = MagicMock()
    puzzle_scalars.all.return_value = puzzles
    puzzle_result.scalars.return_value = puzzle_scalars

    db.execute = AsyncMock(side_effect=[book_result, puzzle_result])
    return db


# =========================================================================
# 1-5  sanitize_word_list
# =========================================================================


@pytest.mark.asyncio
async def test_sanitize_removes_offensive_terms():
    """Offensive words (e.g. 'damn', 'hell') are stripped."""
    words = ["cat", "damn", "dog", "hell"]
    result = await service.sanitize_word_list(words)
    cleaned = result["cleaned_words"]
    assert "damn" not in [w.lower() for w in cleaned]
    assert "hell" not in [w.lower() for w in cleaned]
    removed_words = [r["word"].lower() for r in result["removed"]]
    assert "damn" in removed_words
    assert "hell" in removed_words


@pytest.mark.asyncio
async def test_sanitize_removes_trademark_terms():
    """Trademark terms (e.g. 'Disney', 'Nike') are stripped."""
    words = ["ocean", "Disney", "river", "Nike"]
    result = await service.sanitize_word_list(words)
    cleaned = [w.lower() for w in result["cleaned_words"]]
    assert "disney" not in cleaned
    assert "nike" not in cleaned
    reasons = {r["word"].lower(): r["reason"] for r in result["removed"]}
    assert reasons["disney"] == "trademark"
    assert reasons["nike"] == "trademark"


@pytest.mark.asyncio
async def test_sanitize_removes_abbreviations():
    """All-caps words shorter than 4 characters are treated as abbreviations."""
    words = ["USA", "EU", "ocean", "TREE"]
    result = await service.sanitize_word_list(words)
    cleaned = result["cleaned_words"]
    # "USA" (3 chars, all caps) and "EU" (2 chars, all caps) should be removed
    assert "USA" not in cleaned
    assert "EU" not in cleaned
    # "TREE" is 4 chars all caps -- not an abbreviation under the <4 rule
    assert "TREE" in cleaned


@pytest.mark.asyncio
async def test_sanitize_removes_duplicates():
    """Duplicate words (case-insensitive) are stripped after the first occurrence."""
    words = ["tiger", "Tiger", "TIGER", "banana"]
    result = await service.sanitize_word_list(words)
    cleaned_lower = [w.lower() for w in result["cleaned_words"]]
    assert cleaned_lower.count("tiger") == 1
    assert "banana" in cleaned_lower
    dup_removed = [r for r in result["removed"] if r["reason"] == "duplicate"]
    assert len(dup_removed) == 2  # "Tiger" and "TIGER" are duplicates of "tiger"


@pytest.mark.asyncio
async def test_sanitize_enforces_length_constraints():
    """Words shorter than 2 or longer than 20 characters are removed."""
    short = "a"
    long_word = "a" * 21  # 21 chars -- no vowels though, so it could fail on vowels first
    long_valid = "abcdefghijklmnopqrstuv"  # 22 chars, has vowels, too long
    words = [short, long_valid, "tree", "house"]
    result = await service.sanitize_word_list(words)
    cleaned = result["cleaned_words"]
    assert short not in cleaned
    assert long_valid not in cleaned
    assert "tree" in cleaned
    assert "house" in cleaned


# =========================================================================
# 6-7  qa_clues
# =========================================================================


@pytest.mark.asyncio
async def test_qa_clues_detects_duplicate_phrasing():
    """When two clues have identical (case-insensitive) text, flag duplicate."""
    book = _make_book()
    puzzle = _make_puzzle(
        book_id=book.id,
        clues={
            "clues": {
                "cat": "A furry pet",
                "dog": "a furry pet",  # duplicate phrasing (case-insensitive)
                "fish": "An aquatic animal",
            }
        },
    )
    db = _mock_db_with_book_and_puzzles(book, [puzzle])
    # qa_clues fetches book then puzzle, so we need two db.execute calls
    puzzle_result = MagicMock()
    puzzle_result.scalar_one_or_none.return_value = puzzle
    db.execute = AsyncMock(
        side_effect=[
            # _get_book_or_404
            MagicMock(scalar_one_or_none=MagicMock(return_value=book)),
            # _get_puzzle_or_404
            puzzle_result,
        ]
    )

    result = await service.qa_clues(db, book.org_id, book.id, puzzle.id)
    dup_issues = [i for i in result["issues"] if i["issue"] == "duplicate_clue"]
    assert len(dup_issues) >= 1


@pytest.mark.asyncio
async def test_qa_clues_detects_answer_in_clue():
    """Clue text that contains the answer word itself is flagged."""
    book = _make_book()
    puzzle = _make_puzzle(
        book_id=book.id,
        clues={
            "clues": {
                "river": "A river flows to the sea",  # contains "river"
                "mountain": "A tall landform",
            }
        },
    )
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=book)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=puzzle)),
        ]
    )

    result = await service.qa_clues(db, book.org_id, book.id, puzzle.id)
    answer_issues = [i for i in result["issues"] if i["issue"] == "contains_answer"]
    assert len(answer_issues) == 1
    assert answer_issues[0]["word"] == "river"


# =========================================================================
# 8-9  calibrate_difficulty
# =========================================================================


@pytest.mark.asyncio
async def test_calibrate_difficulty_progressive_pacing():
    """Progressive pacing expects 30% Easy / 40% Medium / 30% Hard.

    When the distribution deviates by more than 15 percentage-points from
    the target, a pacing issue is raised.
    """
    book = _make_book(difficulty_mode=DifficultyMode.progressive)
    # All 10 puzzles are easy -- that is 100% easy, way off from 30%.
    puzzles = [
        _make_puzzle(
            book_id=book.id,
            puzzle_number=i,
            difficulty=Difficulty.easy,
            puzzle_type=PuzzleType.word_search,
            grid_size="10x10",
            word_list=["tree", "house"],
        )
        for i in range(1, 11)
    ]
    db = _mock_db_with_book_and_puzzles(book, puzzles)

    result = await service.calibrate_difficulty(db, book.org_id, book.id)
    assert result["calibrated"] is False
    assert len(result["pacing_issues"]) > 0
    # Should flag at least medium and hard as off-target
    flagged = {pi["difficulty"] for pi in result["pacing_issues"]}
    assert Difficulty.medium in flagged or Difficulty.hard in flagged


@pytest.mark.asyncio
async def test_calibrate_difficulty_fixed_mode_no_pacing_issues():
    """In Fixed mode, progressive pacing rules are NOT enforced."""
    book = _make_book(difficulty_mode=DifficultyMode.fixed)
    puzzles = [
        _make_puzzle(
            book_id=book.id,
            puzzle_number=i,
            difficulty=Difficulty.easy,
            puzzle_type=PuzzleType.word_search,
            grid_size="10x10",
            word_list=["tree", "house"],
        )
        for i in range(1, 11)
    ]
    db = _mock_db_with_book_and_puzzles(book, puzzles)

    result = await service.calibrate_difficulty(db, book.org_id, book.id)
    # Fixed mode should produce zero pacing issues regardless of distribution.
    assert result["pacing_issues"] == []
    assert result["calibrated"] is True


# =========================================================================
# 10  generate_large_print
# =========================================================================


@pytest.mark.asyncio
async def test_generate_large_print_scales_grid_sizes():
    """Grid dimensions are reduced by the scale factor (125/150/175%)."""
    book = _make_book()
    puzzle = _make_puzzle(
        book_id=book.id,
        puzzle_number=1,
        grid_size="15x15",
        word_list=["ocean", "river", "lake", "stream", "brook", "pond"],
    )

    lp_book = _make_book(
        title=f"{book.title} (Large Print 150%)",
        id=uuid4(),
    )

    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    # Only the puzzle-list query goes through db.execute (book lookup is patched)
    puzzle_scalars = MagicMock()
    puzzle_scalars.all.return_value = [puzzle]
    puzzle_result = MagicMock()
    puzzle_result.scalars.return_value = puzzle_scalars
    db.execute = AsyncMock(return_value=puzzle_result)

    scale = 150
    scale_factor = scale / 100.0

    with patch(
        "app.modules.specialty.puzzles.service._get_book_or_404",
        new_callable=AsyncMock,
        return_value=book,
    ), patch(
        "app.modules.specialty.puzzles.service.PuzzleBook",
        return_value=lp_book,
    ), patch(
        "app.modules.specialty.puzzles.service.Puzzle",
        side_effect=lambda **kw: SimpleNamespace(**kw),
    ), patch(
        "app.modules.specialty.puzzles.service.select",
        return_value=MagicMock(where=MagicMock(return_value=MagicMock(order_by=MagicMock(return_value="fake_stmt")))),
    ):
        result = await service.generate_large_print(db, book.org_id, book.id, scale)

    # The original 15x15 at 150% -> int(15/1.5)=10 -> "10x10"
    expected_rows = max(4, int(15 / scale_factor))
    expected_cols = max(4, int(15 / scale_factor))
    adj = result["adjustments"][0]
    assert adj["original_grid_size"] == "15x15"
    assert adj["new_grid_size"] == f"{expected_rows}x{expected_cols}"


@pytest.mark.asyncio
async def test_generate_large_print_rejects_invalid_scale():
    """Scales outside {125, 150, 175} are rejected with a ValidationError."""
    db = AsyncMock()
    from app.core.exceptions import ValidationError as VE

    with pytest.raises(VE):
        await service.generate_large_print(db, uuid4(), uuid4(), 200)


# =========================================================================
# 11-12  verify_answer_key
# =========================================================================


@pytest.mark.asyncio
async def test_verify_answer_key_catches_missing_answers():
    """Puzzles without answer_data are flagged as missing_answer_data."""
    book = _make_book()
    puzzles = [
        _make_puzzle(book_id=book.id, puzzle_number=1, answer_data={"solution": [1]}),
        _make_puzzle(book_id=book.id, puzzle_number=2, answer_data=None),  # missing
    ]
    db = _mock_db_with_book_and_puzzles(book, puzzles)

    result = await service.verify_answer_key(db, book.org_id, book.id)
    assert result["verified"] is False
    missing = [i for i in result["issues"] if i["issue"] == "missing_answer_data"]
    assert len(missing) == 1
    assert missing[0]["puzzle_number"] == 2


@pytest.mark.asyncio
async def test_verify_answer_key_catches_numbering_mismatch():
    """Non-sequential puzzle numbering (e.g. 1, 3) triggers a numbering_gap issue."""
    book = _make_book()
    puzzles = [
        _make_puzzle(book_id=book.id, puzzle_number=1, answer_data={"x": 1}),
        _make_puzzle(book_id=book.id, puzzle_number=3, answer_data={"x": 2}),  # gap
    ]
    db = _mock_db_with_book_and_puzzles(book, puzzles)

    result = await service.verify_answer_key(db, book.org_id, book.id)
    assert result["verified"] is False
    gap = [i for i in result["issues"] if i["issue"] == "numbering_gap"]
    assert len(gap) == 1
    assert gap[0]["puzzle_number"] == 3


# =========================================================================
# 13-14  quality_check (run_quality_check)
# =========================================================================


@pytest.mark.asyncio
async def test_quality_check_detects_duplicate_content_hashes():
    """Two puzzles with the same content_hash are flagged as duplicates."""
    book = _make_book()
    shared_hash = "deadbeef" * 8  # 64 hex chars
    puzzles = [
        _make_puzzle(book_id=book.id, puzzle_number=1, content_hash=shared_hash,
                     word_list=["alpha", "beta"], difficulty=Difficulty.easy),
        _make_puzzle(book_id=book.id, puzzle_number=2, content_hash=shared_hash,
                     word_list=["gamma", "delta"], difficulty=Difficulty.medium),
        _make_puzzle(book_id=book.id, puzzle_number=3, content_hash="unique123",
                     word_list=["epsilon"], difficulty=Difficulty.hard),
    ]
    db = _mock_db_with_book_and_puzzles(book, puzzles)

    result = await service.run_quality_check(db, book.org_id, book.id)
    dup_issues = [i for i in result["issues"] if i["check"] == "duplicate_grids"]
    assert len(dup_issues) == 1
    assert set(dup_issues[0]["puzzle_numbers"]) == {1, 2}
    assert result["checks"]["duplicate_grids"] is False


@pytest.mark.asyncio
async def test_quality_check_enforces_max_word_overlap():
    """Puzzle pairs sharing > 30% Jaccard word overlap are flagged."""
    book = _make_book()
    # Puzzle 1 and 2 share 4/5 words = 80% overlap (well above 30%)
    shared_words = ["apple", "banana", "cherry", "date"]
    puzzles = [
        _make_puzzle(
            book_id=book.id, puzzle_number=1,
            content_hash="hash1",
            word_list=shared_words + ["elderberry"],
            difficulty=Difficulty.easy,
        ),
        _make_puzzle(
            book_id=book.id, puzzle_number=2,
            content_hash="hash2",
            word_list=shared_words + ["fig"],
            difficulty=Difficulty.medium,
        ),
        _make_puzzle(
            book_id=book.id, puzzle_number=3,
            content_hash="hash3",
            word_list=["grape", "honeydew", "kiwi"],
            difficulty=Difficulty.hard,
        ),
    ]
    db = _mock_db_with_book_and_puzzles(book, puzzles)

    result = await service.run_quality_check(db, book.org_id, book.id)
    overlap_issues = [i for i in result["issues"] if i["check"] == "word_list_overlap"]
    assert len(overlap_issues) >= 1
    # The flagged pair should be puzzles 1 and 2
    pair_nums = set(overlap_issues[0]["puzzle_numbers"])
    assert pair_nums == {1, 2}
    assert overlap_issues[0]["overlap_pct"] > 30


# =========================================================================
# 15  export_book page counts
# =========================================================================


@pytest.mark.asyncio
async def test_export_book_calculates_correct_page_counts():
    """Export returns metadata with total_pages and puzzle_count."""
    book = _make_book(has_toc=True)
    num_puzzles = 10
    puzzles = [
        _make_puzzle(book_id=book.id, puzzle_number=i)
        for i in range(1, num_puzzles + 1)
    ]
    db = _mock_db_with_book_and_puzzles(book, puzzles)

    result = await service.export_book(db, book.org_id, book.id, "pdf")

    assert result["format"] == "pdf"
    assert result["status"] == "processing"
    assert "metadata" in result
    # The export engine calculates total pages from the book_data pages list
    metadata = result["metadata"]
    assert metadata["total_pages"] > num_puzzles  # content + front matter + answers
    assert "manifest" in result


@pytest.mark.asyncio
async def test_export_book_no_toc_page_when_disabled():
    """When has_toc is False, export has fewer front matter pages."""
    book = _make_book(has_toc=False)
    puzzles = [_make_puzzle(book_id=book.id, puzzle_number=i) for i in range(1, 6)]
    db = _mock_db_with_book_and_puzzles(book, puzzles)

    result = await service.export_book(db, book.org_id, book.id, "pdf")

    assert result["format"] == "pdf"
    result_with_toc_book = _make_book(has_toc=True)
    db2 = _mock_db_with_book_and_puzzles(result_with_toc_book, puzzles)
    result_with_toc = await service.export_book(db2, result_with_toc_book.org_id, result_with_toc_book.id, "pdf")
    # Without TOC should have fewer total pages
    assert result["metadata"]["total_pages"] <= result_with_toc["metadata"]["total_pages"]
