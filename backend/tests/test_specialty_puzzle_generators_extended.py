"""Tests for Maze, Sudoku, Word Scramble, and Cryptogram generators."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app.modules.specialty_books.generators.cryptogram import generate_cryptogram
from app.modules.specialty_books.generators.maze import generate_maze
from app.modules.specialty_books.generators.sudoku import generate_sudoku
from app.modules.specialty_books.generators.svg_renderer_extended import (
    render_cryptogram_svg,
    render_maze_svg,
    render_sudoku_svg,
    render_word_scramble_svg,
)
from app.modules.specialty_books.generators.word_scramble import generate_word_scramble


class TestMazeGenerator:
    def test_maze_is_solvable(self):
        r = generate_maze(grid_size=10, difficulty="easy", seed=42)
        assert len(r["solution_path"]) > 0
        assert r["solution_path"][0] == r["start"] and r["solution_path"][-1] == r["end"]

    def test_maze_rectangle_shape(self):
        for row in generate_maze(grid_size=10, shape="rectangle", seed=1)["grid"]:
            for cell in row:
                assert cell["masked"] is False

    def test_maze_circle_shape_masks_correctly(self):
        r = generate_maze(grid_size=20, shape="circle", seed=10)
        assert r["grid"][0][0]["masked"] is True
        assert r["grid"][r["size"] // 2][r["size"] // 2]["masked"] is False

    def test_maze_star_shape(self):
        assert (
            sum(1 for row in generate_maze(grid_size=20, shape="star", seed=5)["grid"] for c in row if c["masked"]) > 0
        )

    def test_maze_christmas_tree_shape(self):
        assert len(generate_maze(grid_size=20, shape="christmas_tree", seed=7)["solution_path"]) > 0

    def test_maze_pumpkin_shape(self):
        assert len(generate_maze(grid_size=20, shape="pumpkin", seed=8)["solution_path"]) > 0

    def test_maze_heart_shape(self):
        assert len(generate_maze(grid_size=20, shape="heart", seed=9)["solution_path"]) > 0

    def test_maze_difficulty_scales(self):
        assert generate_maze(difficulty="easy", seed=1)["size"] < generate_maze(difficulty="hard", seed=1)["size"]

    def test_maze_content_hash_deterministic(self):
        assert (
            generate_maze(grid_size=10, seed=99)["content_hash"] == generate_maze(grid_size=10, seed=99)["content_hash"]
        )

    def test_maze_invalid_shape_raises(self):
        with pytest.raises(ValueError, match="Invalid shape"):
            generate_maze(shape="hexagon")


class TestSudokuGenerator:
    def test_sudoku_solution_valid_rows(self):
        for row in generate_sudoku(grid_size=9, seed=42)["solution"]:
            assert sorted(row) == list(range(1, 10))

    def test_sudoku_solution_valid_cols(self):
        r = generate_sudoku(grid_size=9, seed=42)
        for c in range(9):
            assert sorted(r["solution"][row][c] for row in range(9)) == list(range(1, 10))

    def test_sudoku_solution_valid_boxes(self):
        r = generate_sudoku(grid_size=9, seed=42)
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                assert sorted(r["solution"][row][c] for row in range(br, br + 3) for c in range(bc, bc + 3)) == list(
                    range(1, 10)
                )

    def test_sudoku_has_unique_solution(self):
        assert generate_sudoku(grid_size=9, difficulty="easy", seed=1)["has_unique_solution"] is True

    def test_sudoku_givens_count_easy(self):
        assert 36 <= generate_sudoku(grid_size=9, difficulty="easy", seed=10)["givens_count"] <= 45

    def test_sudoku_givens_count_hard(self):
        assert 22 <= generate_sudoku(grid_size=9, difficulty="hard", seed=10)["givens_count"] <= 26

    def test_sudoku_4x4_variant(self):
        r = generate_sudoku(grid_size=4, difficulty="easy", seed=5)
        assert r["size"] == 4
        for row in r["solution"]:
            assert sorted(row) == [1, 2, 3, 4]

    def test_sudoku_6x6_variant(self):
        r = generate_sudoku(grid_size=6, difficulty="medium", seed=5)
        assert r["size"] == 6
        for row in r["solution"]:
            assert sorted(row) == [1, 2, 3, 4, 5, 6]

    def test_sudoku_content_hash_deterministic(self):
        assert (
            generate_sudoku(grid_size=4, seed=77)["content_hash"]
            == generate_sudoku(grid_size=4, seed=77)["content_hash"]
        )


class TestWordScrambleGenerator:
    def test_scramble_differs_from_original(self):
        for e in generate_word_scramble(words=["PYTHON", "ALGORITHM", "PUZZLE"], seed=42)["scrambles"]:
            assert e["scrambled"] != e["original"]

    def test_scramble_same_letters(self):
        for e in generate_word_scramble(words=["TESTING", "SCRAMBLE"], seed=42)["scrambles"]:
            assert sorted(e["scrambled"]) == sorted(e["original"])

    def test_scramble_not_real_word(self):
        for e in generate_word_scramble(words=["STOP", "CARE", "DEAL"], seed=42)["scrambles"]:
            assert e["scrambled"] != e["original"]

    def test_scramble_content_hash_deterministic(self):
        assert (
            generate_word_scramble(words=["ABC", "DEF"], seed=10)["content_hash"]
            == generate_word_scramble(words=["ABC", "DEF"], seed=10)["content_hash"]
        )

    def test_scramble_invalid_words_filtered(self):
        o = [
            s["original"]
            for s in generate_word_scramble(words=["GOOD", "", "123", "OK!!!", "FINE"], seed=1)["scrambles"]
        ]
        assert "GOOD" in o and "FINE" in o

    def test_scramble_hints_easy(self):
        for e in generate_word_scramble(words=["PYTHON", "TESTING"], difficulty="easy", seed=1)["scrambles"]:
            assert "hint" in e


class TestCryptogramGenerator:
    def test_no_letter_maps_to_itself(self):
        for k, v in generate_cryptogram("The quick brown fox", seed=42)["cipher_map"].items():
            assert k != v

    def test_can_decode_back_to_original(self):
        phrase = "HELLO WORLD"
        r = generate_cryptogram(phrase, seed=42)
        inv = {v: k for k, v in r["cipher_map"].items()}
        decoded = "".join(inv.get(ch.upper(), ch) for ch in r["encoded"])
        assert decoded.upper() == phrase.upper()

    def test_cryptogram_hints_easy(self):
        assert (
            2
            <= len(
                generate_cryptogram("The quick brown fox jumps over the lazy dog", difficulty="easy", seed=42)["hints"]
            )
            <= 3
        )

    def test_cryptogram_hints_hard(self):
        assert (
            len(generate_cryptogram("The quick brown fox jumps over the lazy dog", difficulty="hard", seed=42)["hints"])
            == 0
        )

    def test_cryptogram_content_hash_deterministic(self):
        assert (
            generate_cryptogram("Test phrase", seed=55)["content_hash"]
            == generate_cryptogram("Test phrase", seed=55)["content_hash"]
        )

    def test_cryptogram_preserves_punctuation(self):
        r = generate_cryptogram("Hello, World! 123", seed=42)
        assert "," in r["encoded"] and "!" in r["encoded"] and "123" in r["encoded"]


class TestSVGRenderers:
    def _v(self, s):
        ET.fromstring(s)

    def test_maze_svg_valid_xml(self):
        self._v(render_maze_svg(generate_maze(grid_size=10, seed=1)))

    def test_maze_svg_with_solution(self):
        s = render_maze_svg(generate_maze(grid_size=10, seed=1), show_solution=True)
        self._v(s)
        assert "polyline" in s

    def test_sudoku_svg_valid_xml(self):
        self._v(render_sudoku_svg(generate_sudoku(grid_size=9, seed=1)))

    def test_sudoku_svg_with_solution(self):
        self._v(render_sudoku_svg(generate_sudoku(grid_size=9, seed=1), show_solution=True))

    def test_word_scramble_svg_valid_xml(self):
        self._v(render_word_scramble_svg(generate_word_scramble(words=["HELLO", "WORLD"], seed=1)))

    def test_cryptogram_svg_valid_xml(self):
        self._v(render_cryptogram_svg(generate_cryptogram("Test phrase here", seed=1)))
