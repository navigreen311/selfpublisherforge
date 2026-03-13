"""Puzzle generators for Specialty Books module."""

from app.modules.specialty_books.generators.maze import generate_maze
from app.modules.specialty_books.generators.sudoku import generate_sudoku
from app.modules.specialty_books.generators.word_scramble import generate_word_scramble
from app.modules.specialty_books.generators.cryptogram import generate_cryptogram
from app.modules.specialty_books.generators.svg_renderer_extended import (
    render_maze_svg, render_sudoku_svg, render_word_scramble_svg, render_cryptogram_svg,
)

__all__ = [
    "generate_maze", "generate_sudoku", "generate_word_scramble", "generate_cryptogram",
    "render_maze_svg", "render_sudoku_svg", "render_word_scramble_svg", "render_cryptogram_svg",
]
