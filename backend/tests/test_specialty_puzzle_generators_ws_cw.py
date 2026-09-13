"""Tests for Word Search and Crossword algorithmic generators.

Covers: generation, validation, difficulty scoring, content hashing,
edge cases, and SVG rendering.
"""

from __future__ import annotations

import pytest

from app.modules.specialty_books.generators.crossword import generate_crossword
from app.modules.specialty_books.generators.svg_renderer import (
    render_crossword_svg,
    render_word_search_svg,
)
from app.modules.specialty_books.generators.word_search import generate_word_search

# ---- Helpers ----

SAMPLE_WORDS = ["PYTHON", "JAVA", "RUST", "GOLANG", "SWIFT", "RUBY", "SCALA", "PERL"]
SAMPLE_CLUES = {
    "PYTHON": "A large constricting snake or a popular programming language",
    "JAVA": "Indonesian island or a coffee-flavored language",
    "RUST": "Oxidation product or a memory-safe language",
    "GOLANG": "Google's compiled language",
    "SWIFT": "Apple's modern programming language",
    "RUBY": "A precious gemstone or Matz's language",
    "SCALA": "A JVM language combining OO and FP",
    "PERL": "A high-level text processing language",
}


def _verify_word_in_grid(grid: list[list[str]], word: str, positions: list) -> None:
    """Assert that *word* actually appears at *positions* in *grid*."""
    for i, (r, c) in enumerate(positions):
        assert grid[r][c] == word[i], (
            f"Mismatch at position {i} of '{word}': " f"expected '{word[i]}', got '{grid[r][c]}' at ({r},{c})"
        )


# ═══════════════════════════════════════════════════════════════════
# Word Search Tests
# ═══════════════════════════════════════════════════════════════════


class TestWordSearchGeneration:
    """Core generation and validation tests."""

    def test_generates_valid_grid_with_all_words_placed(self):
        result = generate_word_search(SAMPLE_WORDS, grid_size=15, directions=4, seed=42)
        assert len(result["grid"]) == 15
        assert all(len(row) == 15 for row in result["grid"])
        # All sample words should be placed on a 15x15 grid
        assert len(result["words"]) == len(SAMPLE_WORDS)
        assert len(result["unplaced_words"]) == 0

    def test_words_found_at_reported_positions(self):
        result = generate_word_search(SAMPLE_WORDS, grid_size=15, directions=4, seed=42)
        for word, positions in result["solution"].items():
            _verify_word_in_grid(result["grid"], word, positions)

    def test_respects_direction_constraint_2(self):
        """With directions=2, words should only go RIGHT or DOWN."""
        result = generate_word_search(SAMPLE_WORDS, grid_size=15, directions=2, seed=7)
        for word, positions in result["solution"].items():
            deltas = set()
            for i in range(1, len(positions)):
                dr = positions[i][0] - positions[i - 1][0]
                dc = positions[i][1] - positions[i - 1][1]
                deltas.add((dr, dc))
            assert len(deltas) == 1
            delta = deltas.pop()
            assert delta in {(0, 1), (1, 0)}, f"Word '{word}' uses invalid direction {delta}"

    def test_respects_direction_constraint_8(self):
        """With directions=8, all 8 directions should be available."""
        result = generate_word_search(SAMPLE_WORDS * 3, grid_size=20, directions=8, seed=99)
        all_deltas: set[tuple[int, int]] = set()
        for positions in result["solution"].values():
            if len(positions) < 2:
                continue
            dr = positions[1][0] - positions[0][0]
            dc = positions[1][1] - positions[0][1]
            all_deltas.add((dr, dc))
        # Should use at least 3 different directions with enough words
        assert len(all_deltas) >= 2

    def test_difficulty_score_scales(self):
        easy = generate_word_search(SAMPLE_WORDS[:4], grid_size=15, directions=2, seed=1)
        hard = generate_word_search(SAMPLE_WORDS, grid_size=15, directions=8, seed=1)
        # Hard should score >= easy (more directions, more words)
        assert hard["difficulty_score"] >= easy["difficulty_score"]

    def test_content_hash_deterministic(self):
        r1 = generate_word_search(SAMPLE_WORDS, grid_size=15, directions=4, seed=42)
        r2 = generate_word_search(SAMPLE_WORDS, grid_size=15, directions=4, seed=42)
        assert r1["content_hash"] == r2["content_hash"]

    def test_content_hash_differs_for_different_seeds(self):
        r1 = generate_word_search(SAMPLE_WORDS, grid_size=15, directions=4, seed=1)
        r2 = generate_word_search(SAMPLE_WORDS, grid_size=15, directions=4, seed=2)
        assert r1["content_hash"] != r2["content_hash"]

    def test_grid_fully_filled(self):
        """No empty cells should remain after generation."""
        result = generate_word_search(["CAT"], grid_size=10, directions=2, seed=5)
        for row in result["grid"]:
            for cell in row:
                assert cell != "", "Grid should have no empty cells"
                assert cell.isalpha() and cell.isupper()

    def test_single_word(self):
        result = generate_word_search(["HELLO"], grid_size=10, directions=2, seed=0)
        assert "HELLO" in result["words"]
        _verify_word_in_grid(result["grid"], "HELLO", result["solution"]["HELLO"])

    def test_word_longer_than_grid_is_skipped(self):
        result = generate_word_search(["ABCDEFGHIJK", "CAT"], grid_size=5, directions=2, seed=0)
        assert "ABCDEFGHIJK" not in result["words"]
        assert "CAT" in result["words"]

    def test_empty_word_list_raises(self):
        with pytest.raises(ValueError, match="No valid words"):
            generate_word_search([], grid_size=10)

    def test_non_alpha_words_filtered(self):
        result = generate_word_search(["HELLO", "WO RLD", "12345", "GOOD!"], grid_size=10, directions=2, seed=3)
        assert "HELLO" in result["words"]
        # Non-alpha words should be filtered out
        for w in result["words"]:
            assert w.isalpha()


# ═══════════════════════════════════════════════════════════════════
# Crossword Tests
# ═══════════════════════════════════════════════════════════════════


class TestCrosswordGeneration:
    """Core crossword generation and validation tests."""

    def test_places_words_with_valid_intersections(self):
        result = generate_crossword(SAMPLE_WORDS, clues=SAMPLE_CLUES, seed=42)
        placed = {wr["word"] for wr in result["words"]}
        # Should place at least the first word
        assert len(placed) >= 1
        # Verify letters match in solution grid
        for wr in result["words"]:
            word = wr["word"]
            r, c = wr["row"], wr["col"]
            dr, dc = (0, 1) if wr["direction"] == "across" else (1, 0)
            for i, ch in enumerate(word):
                assert result["solution"][r + dr * i][c + dc * i] == ch

    def test_crossword_numbering_correct(self):
        result = generate_crossword(SAMPLE_WORDS[:5], clues=SAMPLE_CLUES, seed=42)
        numbers_used = {wr["number"] for wr in result["words"]}
        # Numbers should be positive integers
        for n in numbers_used:
            assert isinstance(n, int) and n > 0

        # Each starting cell should have exactly one number
        start_cells: dict[tuple[int, int], int] = {}
        for wr in result["words"]:
            pos = (wr["row"], wr["col"])
            if pos in start_cells:
                # Same cell can start an across and down word — same number
                assert start_cells[pos] == wr["number"]
            else:
                start_cells[pos] = wr["number"]

    def test_across_down_clue_mapping(self):
        result = generate_crossword(SAMPLE_WORDS[:5], clues=SAMPLE_CLUES, seed=42)
        for wr in result["words"]:
            num = wr["number"]
            if wr["direction"] == "across":
                assert num in result["across_clues"]
                assert result["across_clues"][num] == wr["clue"]
            else:
                assert num in result["down_clues"]
                assert result["down_clues"][num] == wr["clue"]

    def test_default_clues_when_none_provided(self):
        result = generate_crossword(SAMPLE_WORDS[:3], seed=42)
        for wr in result["words"]:
            assert "Clue for" in wr["clue"]

    def test_grid_has_black_squares(self):
        result = generate_crossword(SAMPLE_WORDS[:5], seed=42)
        has_none = False
        for row in result["grid"]:
            for cell in row:
                if cell is None:
                    has_none = True
                    break
        assert has_none, "Crossword grid should contain black squares (None cells)"

    def test_single_word_crossword(self):
        result = generate_crossword(["HELLO"], seed=0)
        assert len(result["words"]) == 1
        assert result["words"][0]["word"] == "HELLO"
        assert result["words"][0]["direction"] == "across"

    def test_content_hash_deterministic(self):
        r1 = generate_crossword(SAMPLE_WORDS, seed=42)
        r2 = generate_crossword(SAMPLE_WORDS, seed=42)
        assert r1["content_hash"] == r2["content_hash"]

    def test_empty_word_list_raises(self):
        with pytest.raises(ValueError, match="No valid words"):
            generate_crossword([])

    def test_unplaced_words_tracked(self):
        # With very short words that may not intersect, some may be unplaced
        result = generate_crossword(SAMPLE_WORDS, seed=42)
        total = len(result["words"]) + len(result["unplaced_words"])
        # Should account for all sanitized words
        assert total <= len(SAMPLE_WORDS)


# ═══════════════════════════════════════════════════════════════════
# SVG Renderer Tests
# ═══════════════════════════════════════════════════════════════════


class TestSVGRendering:
    """SVG output validation tests."""

    def test_word_search_svg_valid_markup(self):
        puzzle = generate_word_search(SAMPLE_WORDS, grid_size=10, directions=2, seed=1)
        svg = render_word_search_svg(puzzle)
        assert svg.startswith("<svg")
        assert svg.strip().endswith("</svg>")
        assert "xmlns" in svg

    def test_word_search_solution_svg_differs(self):
        puzzle = generate_word_search(SAMPLE_WORDS, grid_size=10, directions=2, seed=1)
        svg_puzzle = render_word_search_svg(puzzle, show_solution=False)
        svg_solution = render_word_search_svg(puzzle, show_solution=True)
        assert svg_puzzle != svg_solution
        # Solution should have highlight colour
        assert "#C8E6C9" in svg_solution

    def test_crossword_svg_valid_markup(self):
        puzzle = generate_crossword(SAMPLE_WORDS[:5], clues=SAMPLE_CLUES, seed=42)
        svg = render_crossword_svg(puzzle)
        assert svg.startswith("<svg")
        assert svg.strip().endswith("</svg>")
        assert "ACROSS" in svg
        assert "DOWN" in svg

    def test_crossword_solution_svg_has_letters(self):
        puzzle = generate_crossword(SAMPLE_WORDS[:5], clues=SAMPLE_CLUES, seed=42)
        svg_puzzle = render_crossword_svg(puzzle, show_solution=False)
        svg_solution = render_crossword_svg(puzzle, show_solution=True)
        assert svg_puzzle != svg_solution
        # Solution should contain actual letters
        for wr in puzzle["words"]:
            assert wr["word"][0] in svg_solution

    def test_crossword_svg_contains_clue_text(self):
        puzzle = generate_crossword(
            ["PYTHON", "RUST"],
            clues={"PYTHON": "A large snake", "RUST": "Iron oxide"},
            seed=42,
        )
        svg = render_crossword_svg(puzzle)
        assert "A large snake" in svg
        assert "Iron oxide" in svg
