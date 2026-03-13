"""Puzzle generators for Specialty Books module.

Pure algorithmic generators — NOT AI-based.
AI is only used for word list and clue generation upstream.
"""

from app.modules.specialty_books.generators.word_search import generate_word_search
from app.modules.specialty_books.generators.crossword import generate_crossword
from app.modules.specialty_books.generators.svg_renderer import (
    render_word_search_svg,
    render_crossword_svg,
)

__all__ = [
    "generate_word_search",
    "generate_crossword",
    "render_word_search_svg",
    "render_crossword_svg",
]
