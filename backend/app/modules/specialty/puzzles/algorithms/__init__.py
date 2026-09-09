"""
Puzzle generation algorithms for SelfPublisherForge.

All puzzles are generated algorithmically (NOT by AI).
Each generator produces valid, solvable puzzles with solution data,
difficulty scores, content hashes, and SVG rendering.
"""

from .crossword import (
    calculate_difficulty as crossword_difficulty,
)
from .crossword import (
    generate_crossword,
)
from .crossword import (
    render_to_svg as render_crossword_svg,
)
from .cryptogram import (
    calculate_difficulty as cryptogram_difficulty,
)
from .cryptogram import (
    generate_cryptogram,
    render_cryptogram_svg,
)
from .maze import (
    calculate_difficulty as maze_difficulty,
)
from .maze import (
    generate_maze,
)
from .maze import (
    render_to_svg as render_maze_svg,
)
from .number_search import (
    generate_number_search,
    render_number_search_svg,
)
from .sudoku import (
    calculate_difficulty as sudoku_difficulty,
)
from .sudoku import (
    generate_sudoku,
    render_sudoku_svg,
)
from .word_connect import (
    calculate_difficulty as word_connect_difficulty,
)
from .word_connect import (
    generate_word_connect,
)
from .word_connect import (
    render_to_svg as render_word_connect_svg,
)
from .word_scramble import (
    calculate_difficulty as word_scramble_difficulty,
)
from .word_scramble import (
    generate_word_scramble,
    render_word_scramble_svg,
)
from .word_search import (
    calculate_difficulty as word_search_difficulty,
)
from .word_search import (
    generate_word_search,
)
from .word_search import (
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
    # Word Connect
    "generate_word_connect",
    "word_connect_difficulty",
    "render_word_connect_svg",
    # Sudoku
    "generate_sudoku",
    "sudoku_difficulty",
    "render_sudoku_svg",
    # Cryptogram
    "generate_cryptogram",
    "cryptogram_difficulty",
    "render_cryptogram_svg",
    # Number Search
    "generate_number_search",
    "render_number_search_svg",
    # Word Scramble
    "generate_word_scramble",
    "word_scramble_difficulty",
    "render_word_scramble_svg",
]
