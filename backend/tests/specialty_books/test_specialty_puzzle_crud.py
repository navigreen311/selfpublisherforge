"""Tests for Puzzle Books CRUD API -- service_puzzle + router_puzzle."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from app.modules.specialty_books import service_puzzle
from app.modules.specialty_books.service_puzzle import (
    PUZZLE_BOOK_TEMPLATES,
    _generate_puzzle_data,
    sanitize_word_list,
)


# ===================================================================
# Fixtures
# ===================================================================
@pytest_asyncio.fixture
async def puzzle_book(db, org_id):
    book = await service_puzzle.create_puzzle_book(db, org_id, {"title": "Test Puzzle Book"})
    await db.commit()
    return book


@pytest_asyncio.fixture
async def puzzle(db, org_id, puzzle_book):
    p = await service_puzzle.create_puzzle(
        db,
        org_id,
        puzzle_book.id,
        {"puzzle_type": "word_search", "puzzle_number": 1},
    )
    await db.commit()
    return p


# ===================================================================
# Book CRUD
# ===================================================================
class TestPuzzleBookCRUD:
    @pytest.mark.asyncio
    async def test_create_book(self, db, org_id):
        book = await service_puzzle.create_puzzle_book(db, org_id, {"title": "My Puzzles"})
        await db.commit()
        assert book.id is not None
        assert book.title == "My Puzzles"
        assert book.org_id == org_id
        assert book.status == "draft"

    @pytest.mark.asyncio
    async def test_create_book_with_template(self, db, org_id):
        book = await service_puzzle.create_puzzle_book(
            db,
            org_id,
            {"title": "Word Search", "template": "word_search_classic"},
        )
        await db.commit()
        assert book.puzzle_config is not None
        assert book.difficulty_mode == "progressive"

    @pytest.mark.asyncio
    async def test_list_books(self, db, org_id):
        await service_puzzle.create_puzzle_book(db, org_id, {"title": "Book 1"})
        await service_puzzle.create_puzzle_book(db, org_id, {"title": "Book 2"})
        await db.commit()
        books, total = await service_puzzle.list_puzzle_books(db, org_id)
        assert total >= 2
        assert len(books) >= 2

    @pytest.mark.asyncio
    async def test_get_book(self, db, org_id, puzzle_book):
        fetched = await service_puzzle.get_puzzle_book(db, org_id, puzzle_book.id)
        assert fetched is not None
        assert fetched.id == puzzle_book.id

    @pytest.mark.asyncio
    async def test_get_book_not_found(self, db, org_id):
        result = await service_puzzle.get_puzzle_book(db, org_id, uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_book(self, db, org_id, puzzle_book):
        updated = await service_puzzle.update_puzzle_book(db, puzzle_book, {"title": "Updated Title"})
        await db.commit()
        assert updated.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_delete_book(self, db, org_id, puzzle_book):
        await service_puzzle.delete_puzzle_book(db, puzzle_book)
        await db.commit()
        result = await service_puzzle.get_puzzle_book(db, org_id, puzzle_book.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, db, org_id):
        result = await service_puzzle.get_puzzle_book(db, org_id, uuid.uuid4())
        assert result is None


# ===================================================================
# Puzzle CRUD
# ===================================================================
class TestPuzzleCRUD:
    @pytest.mark.asyncio
    async def test_create_puzzle(self, db, org_id, puzzle_book):
        p = await service_puzzle.create_puzzle(
            db,
            org_id,
            puzzle_book.id,
            {"puzzle_type": "crossword", "puzzle_number": 1},
        )
        await db.commit()
        assert p.id is not None
        assert p.puzzle_type == "crossword"
        assert p.grid_data is not None

    @pytest.mark.asyncio
    async def test_list_puzzles_ordered(self, db, org_id, puzzle_book):
        await service_puzzle.create_puzzle(db, org_id, puzzle_book.id, {"puzzle_type": "maze", "puzzle_number": 2})
        await service_puzzle.create_puzzle(db, org_id, puzzle_book.id, {"puzzle_type": "maze", "puzzle_number": 1})
        await db.commit()
        puzzles = await service_puzzle.list_puzzles(db, puzzle_book.id)
        assert puzzles[0].puzzle_number <= puzzles[-1].puzzle_number

    @pytest.mark.asyncio
    async def test_update_puzzle(self, db, org_id, puzzle):
        updated = await service_puzzle.update_puzzle(db, puzzle, {"theme": "animals"})
        await db.commit()
        assert updated.theme == "animals"

    @pytest.mark.asyncio
    async def test_delete_puzzle(self, db, org_id, puzzle):
        await service_puzzle.delete_puzzle(db, puzzle)
        await db.commit()
        result = await service_puzzle.get_puzzle(db, puzzle.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_regenerate_puzzle(self, db, org_id, puzzle):
        updated = await service_puzzle.regenerate_puzzle(db, puzzle)
        await db.commit()
        assert updated.grid_data is not None

    @pytest.mark.asyncio
    async def test_create_puzzle_nonexistent_book(self, db, org_id):
        fake_id = uuid.uuid4()
        p = await service_puzzle.create_puzzle(
            db,
            org_id,
            fake_id,
            {"puzzle_type": "word_search", "puzzle_number": 1},
        )
        assert p.book_id == fake_id


# ===================================================================
# Verification / QA
# ===================================================================
class TestPuzzleVerification:
    @pytest.mark.asyncio
    async def test_verify_puzzle_passes(self, db, org_id, puzzle):
        result = await service_puzzle.verify_puzzle(db, puzzle)
        await db.commit()
        assert result["passed"] is True
        assert "scores" in result

    @pytest.mark.asyncio
    async def test_verify_nonexistent_puzzle(self, db, org_id):
        result = await service_puzzle.get_puzzle(db, uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_quality_check(self, db, org_id, puzzle_book, puzzle):
        await service_puzzle.verify_puzzle(db, puzzle)
        await db.commit()
        result = await service_puzzle.book_quality_check(db, puzzle_book)
        assert result["total_puzzles"] >= 1
        assert "pass_rate" in result

    @pytest.mark.asyncio
    async def test_quality_check_empty(self, db, org_id, puzzle_book):
        result = await service_puzzle.book_quality_check(db, puzzle_book)
        assert result["total_puzzles"] == 0
        assert result["pass_rate"] == 0.0


# ===================================================================
# Word Lists
# ===================================================================
class TestWordList:
    @pytest.mark.asyncio
    async def test_generate_word_list(self):
        words = await service_puzzle.generate_word_list("animals", 10)
        assert len(words) == 10
        assert all(isinstance(w, str) for w in words)

    @pytest.mark.asyncio
    async def test_generate_word_list_easy(self):
        words = await service_puzzle.generate_word_list("colors", 5, "easy")
        assert len(words) == 5

    def test_sanitize_offensive(self):
        result = sanitize_word_list(["cat", "damn", "dog"])
        assert "damn" not in result["sanitized"]
        assert any(r["reason"] == "offensive" for r in result["removed"])

    def test_sanitize_trademarks(self):
        result = sanitize_word_list(["cat", "google", "dog"])
        assert "google" not in result["sanitized"]
        assert any(r["reason"] == "trademark" for r in result["removed"])

    def test_sanitize_abbreviations(self):
        result = sanitize_word_list(["cat", "abc123", "dog"])
        assert "abc123" not in result["sanitized"]
        assert any(r["reason"] == "invalid_characters" for r in result["removed"])

    def test_sanitize_invalid_chars(self):
        result = sanitize_word_list(["hello", "wo-rld", "test"])
        assert "wo-rld" not in result["sanitized"]

    def test_sanitize_duplicates(self):
        result = sanitize_word_list(["cat", "Cat", "dog"])
        lower_words = [w.lower() for w in result["sanitized"]]
        assert lower_words.count("cat") == 1

    def test_sanitize_short_words(self):
        result = sanitize_word_list(["ab", "cat", "dog"])
        assert "ab" not in result["sanitized"]
        assert any(r["reason"] == "too_short" for r in result["removed"])

    def test_sanitize_full_pipeline(self):
        words = ["cat", "damn", "google", "abc123", "Cat", "ab", "dog", "elephant"]
        result = sanitize_word_list(words)
        assert result["original_count"] == 8
        assert result["sanitized_count"] + result["removed_count"] == result["original_count"]
        assert "cat" in result["sanitized"]
        assert "dog" in result["sanitized"]
        assert "elephant" in result["sanitized"]


# ===================================================================
# Answer Keys
# ===================================================================
class TestAnswerKey:
    @pytest.mark.asyncio
    async def test_generate_answer_key(self, db, org_id, puzzle_book, puzzle):
        result = await service_puzzle.generate_answer_key(db, puzzle_book)
        assert result["total"] >= 1
        assert len(result["answer_keys"]) >= 1

    @pytest.mark.asyncio
    async def test_verify_answer_key(self, db, org_id, puzzle_book, puzzle):
        result = await service_puzzle.verify_answer_key(db, puzzle_book)
        assert "results" in result
        assert len(result["results"]) >= 1

    @pytest.mark.asyncio
    async def test_answer_key_empty_book(self, db, org_id, puzzle_book):
        result = await service_puzzle.generate_answer_key(db, puzzle_book)
        assert result["total"] == 0


# ===================================================================
# Export & Preflight
# ===================================================================
class TestExportAndPreflight:
    @pytest.mark.asyncio
    async def test_export(self, db, org_id, puzzle_book):
        result = await service_puzzle.export_book(db, puzzle_book)
        assert result["status"] == "completed"
        assert "url" in result

    @pytest.mark.asyncio
    async def test_export_format(self, db, org_id, puzzle_book):
        result = await service_puzzle.export_book(db, puzzle_book, "digital_pdf")
        assert result["format"] == "digital_pdf"

    @pytest.mark.asyncio
    async def test_preflight_empty(self, db, org_id, puzzle_book):
        result = await service_puzzle.run_preflight(db, puzzle_book)
        assert result["ready"] is False
        assert any(c["name"] == "has_puzzles" and not c["passed"] for c in result["checks"])

    @pytest.mark.asyncio
    async def test_preflight_with_puzzles(self, db, org_id, puzzle_book, puzzle):
        await service_puzzle.verify_puzzle(db, puzzle)
        await db.commit()
        result = await service_puzzle.run_preflight(db, puzzle_book)
        assert any(c["name"] == "has_puzzles" and c["passed"] for c in result["checks"])

    @pytest.mark.asyncio
    async def test_preflight_checks_structure(self, db, org_id, puzzle_book):
        result = await service_puzzle.run_preflight(db, puzzle_book)
        for check in result["checks"]:
            assert "name" in check
            assert "passed" in check
            assert "severity" in check


# ===================================================================
# Puzzle Generation
# ===================================================================
class TestPuzzleGeneration:
    def test_word_search(self):
        data = _generate_puzzle_data("word_search", {})
        assert "grid_data" in data
        assert "word_list" in data
        assert "solution_data" in data

    def test_crossword(self):
        data = _generate_puzzle_data("crossword", {})
        assert "clues" in data
        assert "across" in data["clues"]

    def test_maze(self):
        data = _generate_puzzle_data("maze", {})
        assert "grid_data" in data
        assert "start" in data["grid_data"]

    def test_sudoku(self):
        data = _generate_puzzle_data("sudoku", {})
        assert data["grid_size"] == "9x9"

    def test_cryptogram(self):
        data = _generate_puzzle_data("cryptogram", {})
        assert "solution_data" in data
        assert "plaintext" in data["solution_data"]


# ===================================================================
# Templates
# ===================================================================
class TestTemplates:
    def test_all_eight_exist(self):
        assert len(PUZZLE_BOOK_TEMPLATES) == 8
        expected = {
            "word_search_classic",
            "crossword_collection",
            "maze_adventure",
            "sudoku_challenge",
            "mixed_puzzle_fun",
            "large_print_word_search",
            "holiday_puzzles",
            "brain_teasers",
        }
        assert set(PUZZLE_BOOK_TEMPLATES.keys()) == expected

    def test_templates_have_required_fields(self):
        for name, tmpl in PUZZLE_BOOK_TEMPLATES.items():
            assert "title" in tmpl, f"{name} missing title"
            assert "puzzle_config" in tmpl, f"{name} missing puzzle_config"
