"""
Puzzle generation algorithms for SelfPublisherForge.

All puzzles are generated algorithmically (NOT by AI).
Each generator produces valid, solvable puzzles with solution data,
difficulty scores, content hashes, and SVG rendering.
"""

from .crossword import (
    calculate_difficulty as crossword_difficulty,
    generate_crossword,
    render_to_svg as render_crossword_svg,
)
from .maze import (
    calculate_difficulty as maze_difficulty,
    generate_maze,
    render_to_svg as render_maze_svg,
)
from .word_search import (
    calculate_difficulty as word_search_difficulty,
    generate_word_search,
    render_to_svg as render_word_search_svg,
)

__all__ = [
    # Word Search
    "generate_word_search",
    "word_search_difficulty",
    "render_word_search_svg",
    # Crossword
    "generate_crossword",
    "crossword_difficulty",
    "render_crossword_svg",
    # Maze
    "generate_maze",
    "maze_difficulty",
    "render_maze_svg",
]
