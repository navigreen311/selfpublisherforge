"""
Comprehensive unit tests for all puzzle generation algorithms.

Blueprint Section 17.3 — 30 test cases covering:
  Word Search, Crossword, Maze, Sudoku, Word Scramble,
  Cryptogram, Number Search, Utils (hashing), SVG rendering,
  and difficulty score ranges.
"""

import pytest

from app.modules.specialty.puzzles.algorithms.crossword import (
    calculate_difficulty as cw_calculate_difficulty,
)
from app.modules.specialty.puzzles.algorithms.crossword import (
    generate_crossword,
)
from app.modules.specialty.puzzles.algorithms.crossword import (
    render_to_svg as cw_render_to_svg,
)
from app.modules.specialty.puzzles.algorithms.cryptogram import (
    ALPHABET,
    _apply_cipher,
    _generate_derangement,
    generate_cryptogram,
)
from app.modules.specialty.puzzles.algorithms.cryptogram import (
    calculate_difficulty as crypto_calculate_difficulty,
)
from app.modules.specialty.puzzles.algorithms.maze import (
    calculate_difficulty as maze_calculate_difficulty,
)
from app.modules.specialty.puzzles.algorithms.maze import (
    generate_maze,
)
from app.modules.specialty.puzzles.algorithms.maze import (
    render_to_svg as maze_render_to_svg,
)
from app.modules.specialty.puzzles.algorithms.number_search import (
    generate_number_search,
)
from app.modules.specialty.puzzles.algorithms.sudoku import (
    _DIFFICULTY_RANGES_9,
    generate_sudoku,
    verify_unique_solution,
)
from app.modules.specialty.puzzles.algorithms.sudoku import (
    calculate_difficulty as sudoku_calculate_difficulty,
)
from app.modules.specialty.puzzles.algorithms.utils import (
    COMMON_WORDS,
    generate_content_hash,
)
from app.modules.specialty.puzzles.algorithms.word_scramble import (
    generate_word_scramble,
)
from app.modules.specialty.puzzles.algorithms.word_search import (
    DIRECTION_SETS,
    DIRECTION_VECTORS,
    generate_word_search,
)
from app.modules.specialty.puzzles.algorithms.word_search import (
    calculate_difficulty as ws_calculate_difficulty,
)
from app.modules.specialty.puzzles.algorithms.word_search import (
    render_to_svg as ws_render_to_svg,
)

# ============================================================================
# Fixtures
# ============================================================================

WORD_LIST = ["PYTHON", "TESTING", "PUZZLE", "SEARCH", "GRID", "CODE", "BOOK", "PAGE"]
CROSSWORD_WORDS = ["PYTHON", "TESTING", "PRINT", "NOVEL", "INK", "PAGE", "TYPE"]
CROSSWORD_CLUES = {
    "PYTHON": "A programming language",
    "TESTING": "Verifying correctness",
    "PRINT": "Put on paper",
    "NOVEL": "A long story",
    "INK": "Pen fluid",
    "PAGE": "Part of a book",
    "TYPE": "Kind or sort",
}


# ============================================================================
# 1. Word Search — valid grids with configurable directions (2, 4, 8)
# ============================================================================


class TestWordSearch:
    @pytest.mark.parametrize("direction_count", [2, 4, 8])
    def test_generates_valid_grids_with_configurable_directions(self, direction_count):
        """Test 1: Word Search generates valid grids with configurable directions."""
        result = generate_word_search(
            WORD_LIST,
            grid_size=15,
            directions=direction_count,
            seed=42,
        )
        grid = result["grid"]

        # Grid dimensions are correct
        assert len(grid) == 15
        assert all(len(row) == 15 for row in grid)
        # Every cell is a single uppercase letter
        assert all(len(cell) == 1 and cell.isalpha() and cell.isupper() for row in grid for cell in row)
        # Direction setting recorded
        assert result["directions"] == direction_count
        # At least some words were placed
        assert len(result["placed_words"]) > 0

        # Placed words only use allowed directions
        allowed = set(DIRECTION_SETS[direction_count])
        for pw in result["placed_words"]:
            assert pw["direction"] in allowed

    # ========================================================================
    # 2. Word Search — all words findable in the grid
    # ========================================================================

    def test_all_words_findable_in_grid(self):
        """Test 2: All placed words are actually present in the grid."""
        result = generate_word_search(WORD_LIST, grid_size=15, directions=8, seed=7)
        grid = result["grid"]

        for pw in result["placed_words"]:
            word = pw["word"]
            row, col = pw["row"], pw["col"]
            dr, dc = DIRECTION_VECTORS[pw["direction"]]

            extracted = ""
            for i in range(len(word)):
                r = row + i * dr
                c = col + i * dc
                extracted += grid[r][c]

            assert extracted == word, f"Word '{word}' not found at stated position"

    # ========================================================================
    # 3. Word Search — difficulty score calculated correctly
    # ========================================================================

    def test_difficulty_score_calculated_correctly(self):
        """Test 3: Difficulty score reflects parameters."""
        # Easy: small grid, few directions
        easy = ws_calculate_difficulty(
            grid_size=10,
            word_count=5,
            direction_count=2,
            overlap_rate=0.0,
        )
        # Hard: large grid, many directions
        hard = ws_calculate_difficulty(
            grid_size=20,
            word_count=25,
            direction_count=8,
            overlap_rate=0.3,
        )
        assert 0 <= easy <= 100
        assert 0 <= hard <= 100
        assert hard > easy


# ============================================================================
# 4-6. Crossword
# ============================================================================


class TestCrossword:
    def _make_crossword(self, seed=42):
        return generate_crossword(
            CROSSWORD_WORDS,
            CROSSWORD_CLUES,
            max_width=20,
            max_height=20,
            max_attempts=3,
            seed=seed,
        )

    # 4. Crossword generates valid intersecting grids
    def test_generates_valid_intersecting_grids(self):
        """Test 4: Crossword generates a grid with intersecting words."""
        result = self._make_crossword()
        placements = result["placements"]
        assert len(placements) >= 2, "Need at least 2 words placed for intersections"

        # At least one pair of words must share a cell (intersection)
        occupied: dict[tuple[int, int], list[str]] = {}
        for p in placements:
            word = p["word"]
            for i, letter in enumerate(word):
                if p["direction"] == "across":
                    pos = (p["row"], p["col"] + i)
                else:
                    pos = (p["row"] + i, p["col"])
                occupied.setdefault(pos, []).append(word)

        intersections = {pos for pos, words in occupied.items() if len(words) > 1}
        assert len(intersections) > 0, "No word intersections found"

    # 5. Crossword numbering (across/down) is correct
    def test_numbering_across_down_correct(self):
        """Test 5: Numbers are assigned and clues reference valid numbers."""
        result = self._make_crossword()
        across = result["across_clues"]
        down = result["down_clues"]

        # At least one across and/or down clue exists
        assert len(across) + len(down) > 0

        # Every placement that has a number appears in across or down clues
        for p in result["placements"]:
            if p["number"] is not None:
                num_str = str(p["number"])
                if p["direction"] == "across":
                    assert num_str in across
                else:
                    assert num_str in down

    # 6. Crossword all placed words are connected
    def test_all_placed_words_connected(self):
        """Test 6: Every placed word shares at least one cell with the rest."""
        result = self._make_crossword()
        placements = result["placements"]
        if len(placements) <= 1:
            pytest.skip("Only one word placed; connectivity trivially satisfied")

        # Build adjacency via shared cells
        word_cells: dict[str, set[tuple[int, int]]] = {}
        for p in placements:
            cells = set()
            for i in range(len(p["word"])):
                if p["direction"] == "across":
                    cells.add((p["row"], p["col"] + i))
                else:
                    cells.add((p["row"] + i, p["col"]))
            word_cells[p["word"]] = cells

        # BFS connectivity: start from first word
        words = list(word_cells.keys())
        visited = {words[0]}
        queue = [words[0]]
        while queue:
            current = queue.pop(0)
            for other in words:
                if other not in visited and word_cells[current] & word_cells[other]:
                    visited.add(other)
                    queue.append(other)

        assert visited == set(words), f"Disconnected words: {set(words) - visited}"


# ============================================================================
# 7-9. Maze
# ============================================================================


class TestMaze:
    # 7. Maze generates solvable mazes (solution path exists)
    def test_generates_solvable_mazes(self):
        """Test 7: Generated maze has a non-empty solution path."""
        result = generate_maze(width=15, height=15, shape="rectangle", seed=42)
        assert len(result["solution_path"]) >= 2, "Solution path must exist"
        # Path starts at entrance and ends at exit
        assert result["solution_path"][0] == result["entrance"]
        assert result["solution_path"][-1] == result["exit"]

    # 8. Maze shape variants work
    @pytest.mark.parametrize(
        "shape",
        ["rectangle", "circle", "heart", "star", "christmas_tree", "pumpkin"],
    )
    def test_shape_variants_work(self, shape):
        """Test 8: All shape variants produce a valid, solvable maze."""
        result = generate_maze(width=20, height=20, shape=shape, seed=99)
        assert result["shape"] == shape
        assert result["active_cell_count"] > 0
        assert len(result["solution_path"]) >= 2

    # 9. Maze entrance and exit at correct positions
    def test_entrance_exit_correct_positions(self):
        """Test 9: Entrance is in the top-left region; exit in bottom-right."""
        result = generate_maze(width=20, height=20, shape="rectangle", seed=42)
        entrance = result["entrance"]
        exit_cell = result["exit"]

        # Entrance should be the first active cell (top-left scan)
        assert entrance[0] == 0 and entrance[1] == 0

        # Exit should be the last active cell (bottom-right scan)
        assert exit_cell[0] == 19 and exit_cell[1] == 19

        # They must differ
        assert entrance != exit_cell


# ============================================================================
# 10-13. Sudoku
# ============================================================================


class TestSudoku:
    # 10. Sudoku generates valid complete solutions
    def test_valid_complete_solutions_no_conflicts(self):
        """Test 10: Solution grid has no row/col/box conflicts."""
        result = generate_sudoku(size=9, difficulty="easy")
        solution = result["solution"]
        size = 9
        box_rows, box_cols = 3, 3

        # Check all rows
        for r in range(size):
            assert sorted(solution[r]) == list(range(1, size + 1)), f"Row {r} invalid: {solution[r]}"

        # Check all columns
        for c in range(size):
            col_vals = [solution[r][c] for r in range(size)]
            assert sorted(col_vals) == list(range(1, size + 1)), f"Col {c} invalid"

        # Check all boxes
        for br in range(0, size, box_rows):
            for bc in range(0, size, box_cols):
                box_vals = []
                for r in range(br, br + box_rows):
                    for c in range(bc, bc + box_cols):
                        box_vals.append(solution[r][c])
                assert sorted(box_vals) == list(range(1, size + 1)), f"Box at ({br},{bc}) invalid"

    # 11. Sudoku generated puzzles have unique solutions
    def test_puzzles_have_unique_solutions(self):
        """Test 11: The generated puzzle grid has exactly one solution."""
        result = generate_sudoku(size=4, difficulty="easy")
        grid = result["grid"]
        assert verify_unique_solution(grid, size=4)

    # 12. Sudoku difficulty calibrated by givens count
    def test_difficulty_calibrated_by_givens_count(self):
        """Test 12: Givens count falls within expected range per difficulty."""
        for diff, (lo_9, hi_9) in _DIFFICULTY_RANGES_9.items():
            result = generate_sudoku(size=9, difficulty=diff)
            givens = result["givens_count"]
            # Allow small slack because unique-solution constraint may prevent
            # removing enough numbers.
            assert givens >= lo_9 - 5, f"{diff}: givens {givens} below floor {lo_9}"
            assert givens <= hi_9 + 5, f"{diff}: givens {givens} above ceiling {hi_9}"

    # 13. Sudoku 4x4 and 6x6 kids variants
    @pytest.mark.parametrize("size", [4, 6])
    def test_kids_variants(self, size):
        """Test 13: 4x4 and 6x6 kids variants generate valid puzzles."""
        result = generate_sudoku(size=size, difficulty="easy")
        solution = result["solution"]
        assert len(solution) == size
        assert all(len(row) == size for row in solution)

        # Validate solution: all rows contain 1..size
        for r in range(size):
            assert sorted(solution[r]) == list(range(1, size + 1))

        # Validate columns
        for c in range(size):
            assert sorted(solution[r][c] for r in range(size)) == list(range(1, size + 1))

        # Puzzle grid has zeros (blanks)
        flat = [cell for row in result["grid"] for cell in row]
        assert 0 in flat


# ============================================================================
# 14-15. Word Scramble
# ============================================================================


class TestWordScramble:
    # 14. Word Scramble generates valid scrambles
    def test_generates_valid_scrambles_different_from_original(self):
        """Test 14: Scrambled word differs from the original."""
        words = ["PUZZLE", "ENIGMA", "RIDDLE", "MYSTERY", "CIPHER"]
        result = generate_word_scramble(words, hint_mode="first_letter")

        for entry in result["scrambles"]:
            assert (
                entry["scrambled"] != entry["original"]
            ), f"Scrambled '{entry['scrambled']}' same as original '{entry['original']}'"
            # Same letters (sorted)
            assert sorted(entry["scrambled"]) == sorted(entry["original"])

    # 15. Word Scramble — scrambled word is not another valid word
    def test_scrambled_word_not_common_word(self):
        """Test 15: Scrambled version is not a common English word."""
        words = ["LISTEN", "DANGER", "GARDEN", "SPREAD"]
        result = generate_word_scramble(words, hint_mode="none")

        for entry in result["scrambles"]:
            assert entry["scrambled"].lower() not in COMMON_WORDS, f"Scrambled '{entry['scrambled']}' is a common word"


# ============================================================================
# 16-17. Cryptogram
# ============================================================================


class TestCryptogram:
    # 16. Substitution cipher — no letter maps to itself
    def test_no_letter_maps_to_itself(self):
        """Test 16: Derangement cipher has no fixed points."""
        for _ in range(20):
            cipher = _generate_derangement()
            for letter in ALPHABET:
                assert cipher[letter] != letter, f"Letter '{letter}' maps to itself"

    # 17. Cryptogram can be decoded back to original
    def test_decoded_back_to_original(self):
        """Test 17: Applying the reverse cipher recovers the original."""
        phrase = "The quick brown fox jumps over the lazy dog"
        result = generate_cryptogram(phrase, reveal_count=0)

        cipher_map = result["cipher_map"]
        reverse_map = {v: k for k, v in cipher_map.items()}

        decoded = _apply_cipher(result["encoded"], reverse_map)
        assert decoded == phrase


# ============================================================================
# 18. Number Search
# ============================================================================


class TestNumberSearch:
    def test_generates_valid_grids_with_numbers_placed(self):
        """Test 18: Number search places digit sequences in the grid."""
        numbers = ["314", "2718", "42", "1618", "99"]
        result = generate_number_search(numbers, grid_size=12, directions=4)
        grid = result["grid"]

        assert len(grid) == 12
        assert all(len(row) == 12 for row in grid)
        # Every cell is a single digit
        assert all(len(cell) == 1 and cell.isdigit() for row in grid for cell in row)
        # At least some numbers were placed
        assert len(result["placed_numbers"]) > 0

        # Verify placed numbers are actually in the grid
        for entry in result["placed_numbers"]:
            extracted = "".join(grid[r][c] for r, c in entry["positions"])
            assert extracted == entry["number"]


# ============================================================================
# 19. Content hash generation is deterministic
# ============================================================================


class TestContentHash:
    def test_deterministic_hashing(self):
        """Test 19: Same input produces same hash, different input differs."""
        data_a = {"grid": [[1, 2], [3, 4]], "words": ["HELLO"]}
        data_b = {"grid": [[1, 2], [3, 4]], "words": ["HELLO"]}
        data_c = {"grid": [[5, 6], [7, 8]], "words": ["WORLD"]}

        hash_a = generate_content_hash(data_a)
        hash_b = generate_content_hash(data_b)
        hash_c = generate_content_hash(data_c)

        assert hash_a == hash_b, "Same data must produce same hash"
        assert hash_a != hash_c, "Different data must produce different hash"
        assert len(hash_a) == 64, "SHA-256 hex digest is 64 chars"


# ============================================================================
# 20. SVG rendering produces valid SVG strings
# ============================================================================


class TestSVGRendering:
    def test_word_search_svg(self):
        """Test 20a: Word search SVG is valid."""
        puzzle = generate_word_search(WORD_LIST, grid_size=10, directions=4, seed=1)
        svg = ws_render_to_svg(puzzle, show_solution=False)
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_word_search_svg_solution(self):
        """Test 20b: Word search SVG solution highlights."""
        puzzle = generate_word_search(WORD_LIST, grid_size=10, directions=4, seed=1)
        svg = ws_render_to_svg(puzzle, show_solution=True)
        assert "#FFFFCC" in svg  # highlight colour for solution cells

    def test_crossword_svg(self):
        """Test 20c: Crossword SVG is valid."""
        puzzle = generate_crossword(
            CROSSWORD_WORDS,
            CROSSWORD_CLUES,
            seed=42,
        )
        svg = cw_render_to_svg(puzzle, show_solution=False)
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_maze_svg(self):
        """Test 20d: Maze SVG is valid."""
        puzzle = generate_maze(width=10, height=10, shape="rectangle", seed=1)
        svg = maze_render_to_svg(puzzle, show_solution=True)
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_sudoku_svg(self):
        """Test 20e: Sudoku SVG is valid."""
        puzzle = generate_sudoku(size=4, difficulty="easy")
        svg = puzzle["svg"]
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_word_scramble_svg(self):
        """Test 20f: Word scramble SVG is valid."""
        result = generate_word_scramble(["PUZZLE", "TESTING"], hint_mode="both")
        svg = result["svg"]
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_cryptogram_svg(self):
        """Test 20g: Cryptogram SVG is valid."""
        result = generate_cryptogram("Hello World", reveal_count=1)
        svg = result["svg"]
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_number_search_svg(self):
        """Test 20h: Number search SVG is valid."""
        result = generate_number_search(["123", "456"], grid_size=8, directions=4)
        svg = result["svg"]
        assert "<svg" in svg
        assert "</svg>" in svg


# ============================================================================
# 21. Difficulty scores in range 0-100 for all algorithms
# ============================================================================


class TestDifficultyScoresInRange:
    def test_word_search_difficulty_range(self):
        """Test 21a: Word search difficulty in [0, 100]."""
        result = generate_word_search(WORD_LIST, grid_size=15, directions=8, seed=1)
        assert 0.0 <= result["difficulty_score"] <= 100.0

    def test_crossword_difficulty_range(self):
        """Test 21b: Crossword difficulty in [0, 100]."""
        result = generate_crossword(CROSSWORD_WORDS, CROSSWORD_CLUES, seed=1)
        assert 0.0 <= result["difficulty_score"] <= 100.0

    def test_maze_difficulty_range(self):
        """Test 21c: Maze difficulty in [0, 100]."""
        result = generate_maze(width=20, height=20, shape="rectangle", seed=1)
        assert 0.0 <= result["difficulty_score"] <= 100.0

    def test_sudoku_difficulty_range(self):
        """Test 21d: Sudoku difficulty in [0, 100]."""
        result = generate_sudoku(size=9, difficulty="medium")
        assert 0.0 <= result["difficulty_score"] <= 100.0

    def test_word_scramble_difficulty_range(self):
        """Test 21e: Word scramble difficulty in [0, 100]."""
        result = generate_word_scramble(["PUZZLE", "ENIGMA", "RIDDLE"])
        assert 0.0 <= result["difficulty_score"] <= 100.0

    def test_cryptogram_difficulty_range(self):
        """Test 21f: Cryptogram difficulty in [0, 100]."""
        result = generate_cryptogram("The quick brown fox jumps over the lazy dog")
        assert 0.0 <= result["difficulty_score"] <= 100.0

    @pytest.mark.parametrize(
        "params",
        [
            dict(grid_size=10, word_count=5, direction_count=2, overlap_rate=0.0),
            dict(grid_size=20, word_count=25, direction_count=8, overlap_rate=0.5),
        ],
    )
    def test_ws_calculate_difficulty_bounds(self, params):
        """Test 21g: ws calculate_difficulty always in [0, 100]."""
        score = ws_calculate_difficulty(**params)
        assert 0.0 <= score <= 100.0

    @pytest.mark.parametrize(
        "params",
        [
            dict(path_length=10, dead_end_count=5, branch_factor=1.8, grid_size=10),
            dict(path_length=500, dead_end_count=200, branch_factor=3.0, grid_size=40),
        ],
    )
    def test_maze_calculate_difficulty_bounds(self, params):
        """Test 21h: maze calculate_difficulty always in [0, 100]."""
        score = maze_calculate_difficulty(**params)
        assert 0.0 <= score <= 100.0

    def test_sudoku_calculate_difficulty_bounds(self):
        """Test 21i: sudoku calculate_difficulty always in [0, 100]."""
        score = sudoku_calculate_difficulty(
            givens_count=30,
            techniques_required=["naked_singles", "hidden_singles"],
        )
        assert 0.0 <= score <= 100.0

    def test_cryptogram_calculate_difficulty_bounds(self):
        """Test 21j: cryptogram calculate_difficulty always in [0, 100]."""
        score = crypto_calculate_difficulty(
            phrase_length=100,
            unique_letters=20,
            letter_frequency_distribution=0.04,
        )
        assert 0.0 <= score <= 100.0


# ============================================================================
# Additional edge-case / robustness tests (extending to ≥30 total)
# ============================================================================


class TestEdgeCases:
    def test_word_search_invalid_direction_count(self):
        """Invalid direction count raises ValueError."""
        with pytest.raises(ValueError, match="directions must be 2, 4, or 8"):
            generate_word_search(["HELLO"], grid_size=10, directions=3)

    def test_word_search_seed_reproducibility(self):
        """Same seed produces identical puzzles."""
        a = generate_word_search(WORD_LIST, grid_size=12, directions=4, seed=123)
        b = generate_word_search(WORD_LIST, grid_size=12, directions=4, seed=123)
        assert a["grid"] == b["grid"]
        assert a["content_hash"] == b["content_hash"]

    def test_maze_invalid_shape_raises(self):
        """Unknown maze shape raises ValueError."""
        with pytest.raises(ValueError, match="Unknown shape"):
            generate_maze(width=10, height=10, shape="hexagon")

    def test_sudoku_invalid_size_raises(self):
        """Unsupported grid size raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported size"):
            generate_sudoku(size=5)

    def test_sudoku_invalid_difficulty_raises(self):
        """Unknown difficulty raises ValueError."""
        with pytest.raises(ValueError, match="Unknown difficulty"):
            generate_sudoku(size=9, difficulty="extreme")

    def test_word_scramble_empty_list_raises(self):
        """Empty word list raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            generate_word_scramble([])

    def test_cryptogram_empty_phrase_raises(self):
        """Non-alpha phrase raises ValueError."""
        with pytest.raises(ValueError, match="at least one alphabetic"):
            generate_cryptogram("12345!!!")

    def test_number_search_no_valid_sequences_raises(self):
        """No valid digit sequences raises ValueError."""
        with pytest.raises(ValueError, match="No valid digit"):
            generate_number_search(["abc", "---"], grid_size=10)

    def test_crossword_difficulty_function_edge(self):
        """Crossword difficulty with extreme inputs stays bounded."""
        score = cw_calculate_difficulty(
            black_square_pct=0.8,
            avg_word_length=12,
            clue_grade_level=12,
        )
        assert 0.0 <= score <= 100.0
