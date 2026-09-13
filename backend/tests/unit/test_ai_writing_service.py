"""Unit tests for the AI Writing service layer.

Tests manuscript management, chapter CRUD, outline generation, readability analysis,
and writing session tracking.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import AppException
from app.models.content import (
    Chapter,
    ContentType,
    Manuscript,
    ManuscriptStatus,
)
from app.modules.ai_writing import service
from app.modules.ai_writing.schemas import (
    ChapterCreate,
    ChapterReorderRequest,
    ChapterUpdate,
    OutlineGenerateRequest,
    OutlineRequest,
    WritingSessionCreate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_manuscript(db, book_id: uuid.UUID | None = None) -> Manuscript:
    """Create a manuscript with some chapters."""
    book_id = book_id or uuid.uuid4()
    manuscript = Manuscript(
        id=uuid.uuid4(),
        book_id=book_id,
        content_type=ContentType.FICTION,
        status=ManuscriptStatus.DRAFT,
    )
    db.add(manuscript)
    await db.flush()
    return manuscript


async def _seed_chapter(
    db,
    manuscript_id: uuid.UUID,
    title: str = "Test Chapter",
    content: str = "This is test content.",
    order: int = 1,
) -> Chapter:
    """Create a single chapter."""
    chapter = Chapter(
        id=uuid.uuid4(),
        manuscript_id=manuscript_id,
        title=title,
        content=content,
        order_index=order,
        word_count=len(content.split()),
    )
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)
    return chapter


# ---------------------------------------------------------------------------
# Manuscript CRUD tests
# ---------------------------------------------------------------------------


class TestGetManuscript:
    @pytest.mark.asyncio
    async def test_get_manuscript_creates_if_missing(self, db_session):
        """If no manuscript exists for a book, one should be created."""
        book_id = uuid.uuid4()
        result = await service.get_manuscript(db_session, book_id)
        assert result.book_id == book_id
        assert result.total_word_count == 0
        assert len(result.chapters) == 0

    @pytest.mark.asyncio
    async def test_get_manuscript_returns_existing(self, db_session):
        """Should return the existing manuscript with chapters."""
        manuscript = await _seed_manuscript(db_session)
        await _seed_chapter(db_session, manuscript.id, "Chapter 1", "Content one.", 1)
        await _seed_chapter(db_session, manuscript.id, "Chapter 2", "Content two.", 2)

        result = await service.get_manuscript(db_session, manuscript.book_id)
        assert result.book_id == manuscript.book_id
        assert len(result.chapters) == 2
        assert result.chapters[0].title == "Chapter 1"
        assert result.chapters[1].title == "Chapter 2"

    @pytest.mark.asyncio
    async def test_get_manuscript_calculates_total_words(self, db_session):
        """Total word count should sum all chapter word counts."""
        manuscript = await _seed_manuscript(db_session)
        await _seed_chapter(db_session, manuscript.id, "C1", "word word word", 1)
        await _seed_chapter(db_session, manuscript.id, "C2", "one two three four", 2)

        result = await service.get_manuscript(db_session, manuscript.book_id)
        assert result.total_word_count == 7


# ---------------------------------------------------------------------------
# Chapter CRUD tests
# ---------------------------------------------------------------------------


class TestListChapters:
    @pytest.mark.asyncio
    async def test_list_chapters_empty(self, db_session):
        """Listing chapters for a book with no manuscript creates one and returns empty list."""
        book_id = uuid.uuid4()
        result = await service.list_chapters(db_session, book_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_list_chapters_ordered(self, db_session):
        """Chapters should be returned in order."""
        manuscript = await _seed_manuscript(db_session)
        await _seed_chapter(db_session, manuscript.id, "Second", "b", 2)
        await _seed_chapter(db_session, manuscript.id, "First", "a", 1)
        await _seed_chapter(db_session, manuscript.id, "Third", "c", 3)

        result = await service.list_chapters(db_session, manuscript.book_id)
        assert len(result) == 3
        assert result[0].title == "First"
        assert result[1].title == "Second"
        assert result[2].title == "Third"


class TestGetChapter:
    @pytest.mark.asyncio
    async def test_get_chapter_success(self, db_session):
        """Should retrieve a single chapter by ID."""
        manuscript = await _seed_manuscript(db_session)
        chapter = await _seed_chapter(db_session, manuscript.id, "My Chapter", "Content here", 1)

        result = await service.get_chapter(db_session, manuscript.book_id, chapter.id)
        assert result.id == chapter.id
        assert result.title == "My Chapter"

    @pytest.mark.asyncio
    async def test_get_chapter_not_found(self, db_session):
        """Should raise exception if chapter doesn't exist."""
        book_id = uuid.uuid4()
        chapter_id = uuid.uuid4()

        with pytest.raises(AppException) as exc_info:
            await service.get_chapter(db_session, book_id, chapter_id)
        assert exc_info.value.code == "CHAPTER_NOT_FOUND"


class TestCreateChapter:
    @pytest.mark.asyncio
    async def test_create_chapter_success(self, db_session):
        """Should create a new chapter and calculate word count."""
        book_id = uuid.uuid4()
        data = ChapterCreate(
            title="New Chapter",
            content="This is some test content.",
            order=1,
        )

        result = await service.create_chapter(db_session, book_id, data)
        assert result.title == "New Chapter"
        assert result.word_count == 5

    @pytest.mark.asyncio
    async def test_create_chapter_empty_content(self, db_session):
        """Should handle empty content gracefully."""
        book_id = uuid.uuid4()
        data = ChapterCreate(title="Empty", content="", order=1)

        result = await service.create_chapter(db_session, book_id, data)
        assert result.word_count == 0


class TestUpdateChapter:
    @pytest.mark.asyncio
    async def test_update_chapter_title(self, db_session):
        """Should update chapter title."""
        manuscript = await _seed_manuscript(db_session)
        chapter = await _seed_chapter(db_session, manuscript.id)

        update = ChapterUpdate(title="Updated Title")
        result = await service.update_chapter(db_session, manuscript.book_id, chapter.id, update)

        assert result.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_chapter_content_recalculates_words(self, db_session):
        """Should recalculate word count when content changes."""
        manuscript = await _seed_manuscript(db_session)
        chapter = await _seed_chapter(db_session, manuscript.id, "Ch", "old content", 1)

        update = ChapterUpdate(content="new content with more words here")
        result = await service.update_chapter(db_session, manuscript.book_id, chapter.id, update)

        assert result.word_count == 6

    @pytest.mark.asyncio
    async def test_update_chapter_not_found(self, db_session):
        """Should raise exception if chapter doesn't exist."""
        book_id = uuid.uuid4()
        chapter_id = uuid.uuid4()
        update = ChapterUpdate(title="Foo")

        with pytest.raises(AppException) as exc_info:
            await service.update_chapter(db_session, book_id, chapter_id, update)
        assert exc_info.value.code == "CHAPTER_NOT_FOUND"


class TestReorderChapters:
    @pytest.mark.asyncio
    async def test_reorder_chapters_success(self, db_session):
        """Should reorder chapters based on provided mapping."""
        manuscript = await _seed_manuscript(db_session)
        ch1 = await _seed_chapter(db_session, manuscript.id, "First", "a", 1)
        ch2 = await _seed_chapter(db_session, manuscript.id, "Second", "b", 2)
        ch3 = await _seed_chapter(db_session, manuscript.id, "Third", "c", 3)

        from app.modules.ai_writing.schemas import ChapterReorderItem

        reorder = ChapterReorderRequest(
            chapters=[
                ChapterReorderItem(chapter_id=ch3.id, order=1),
                ChapterReorderItem(chapter_id=ch1.id, order=2),
                ChapterReorderItem(chapter_id=ch2.id, order=3),
            ]
        )

        result = await service.reorder_chapters(db_session, manuscript.book_id, reorder)
        assert len(result) == 3
        assert result[0].title == "Third"
        assert result[1].title == "First"
        assert result[2].title == "Second"


# ---------------------------------------------------------------------------
# Readability & analysis tests
# ---------------------------------------------------------------------------


class TestReadabilityScore:
    @pytest.mark.asyncio
    async def test_get_readability_score_empty_manuscript(self, db_session):
        """Should handle empty manuscript gracefully."""
        book_id = uuid.uuid4()
        result = await service.get_readability_score(db_session, book_id)
        assert result.word_count == 0

    @pytest.mark.asyncio
    async def test_get_readability_score_with_content(self, db_session):
        """Should compute readability metrics for full manuscript."""
        manuscript = await _seed_manuscript(db_session)
        content = (
            "This is a simple test sentence. "
            "It contains multiple words and sentences. "
            "The readability analysis should process this content properly."
        )
        await _seed_chapter(db_session, manuscript.id, "Ch1", content, 1)

        result = await service.get_readability_score(db_session, manuscript.book_id)
        assert result.word_count > 0
        assert result.sentence_count > 0


class TestAnalyzeManuscript:
    @pytest.mark.asyncio
    async def test_analyze_manuscript_empty(self, db_session):
        """Should handle analysis of empty manuscript."""
        book_id = uuid.uuid4()
        result = await service.analyze_manuscript(db_session, book_id)
        assert result.total_word_count == 0
        assert result.chapter_count == 0
        assert result.avg_chapter_word_count == 0.0

    @pytest.mark.asyncio
    async def test_analyze_manuscript_with_chapters(self, db_session):
        """Should analyze manuscript and provide pacing notes."""
        manuscript = await _seed_manuscript(db_session)
        await _seed_chapter(db_session, manuscript.id, "Ch1", "word " * 2000, 1)
        await _seed_chapter(db_session, manuscript.id, "Ch2", "word " * 2100, 2)

        result = await service.analyze_manuscript(db_session, manuscript.book_id)
        assert result.chapter_count == 2
        assert result.total_word_count == 4100
        assert result.avg_chapter_word_count == 2050.0

    @pytest.mark.asyncio
    async def test_analyze_manuscript_detects_short_chapters(self, db_session):
        """Should detect chapters that are too short."""
        manuscript = await _seed_manuscript(db_session)
        await _seed_chapter(db_session, manuscript.id, "Ch1", "word " * 2000, 1)
        await _seed_chapter(db_session, manuscript.id, "Ch2", "short", 2)

        result = await service.analyze_manuscript(db_session, manuscript.book_id)
        assert len(result.pacing_notes) > 0


# ---------------------------------------------------------------------------
# Outline generation tests
# ---------------------------------------------------------------------------


class TestGenerateOutline:
    @pytest.mark.asyncio
    async def test_generate_outline_success(self, db_session):
        """Should generate outline from AI."""
        book_id = uuid.uuid4()
        request = OutlineRequest(
            genre="fantasy",
            premise="A young wizard discovers a hidden power",
            num_chapters=5,
            tone="epic",
            target_audience="YA",
            additional_instructions="Focus on character development",
        )

        mock_llm_response = """{
            "chapters": [
                {"title": "Chapter 1", "synopsis": "The beginning", "key_points": ["point 1"]},
                {"title": "Chapter 2", "synopsis": "The journey", "key_points": ["point 2"]}
            ],
            "summary": "An epic tale of discovery"
        }"""

        with patch("app.modules.ai_writing.generator._call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response

            result = await service.generate_outline(db_session, book_id, request)

        assert result.book_id == book_id
        assert len(result.chapters) == 2
        assert result.chapters[0].title == "Chapter 1"
        assert result.summary == "An epic tale of discovery"

    @pytest.mark.asyncio
    async def test_generate_outline_handles_malformed_json(self, db_session):
        """Should handle malformed JSON from LLM gracefully."""
        book_id = uuid.uuid4()
        request = OutlineRequest(
            genre="mystery",
            premise="A detective solves a case",
            num_chapters=3,
        )

        with patch("app.modules.ai_writing.generator._call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "This is not JSON"

            result = await service.generate_outline(db_session, book_id, request)

        assert len(result.chapters) == 0
        assert "This is not JSON" in result.summary


class TestGenerateOutlineStandalone:
    @pytest.mark.asyncio
    async def test_generate_standalone_outline_success(self, db_session):
        """Should generate standalone outline without book_id."""
        request = OutlineGenerateRequest(
            book_title="My Novel",
            genre="thriller",
            num_chapters=4,
            premise="A spy uncovers a conspiracy",
            target_audience="Adult",
            tone="dark",
        )

        mock_llm_response = """{
            "chapters": [
                {
                    "chapter_number": 1,
                    "title": "The Discovery",
                    "description": "The spy finds the first clue",
                    "key_points": ["clue", "danger"],
                    "estimated_word_count": 3000
                }
            ],
            "synopsis": "A thrilling spy novel"
        }"""

        with patch("app.modules.ai_writing.generator._call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response

            result = await service.generate_outline_standalone(request, db_session)

        assert result.book_title == "My Novel"
        assert result.genre == "thriller"
        assert len(result.chapters) == 1
        assert result.chapters[0].title == "The Discovery"
        assert result.synopsis == "A thrilling spy novel"


# ---------------------------------------------------------------------------
# Writing sessions tests
# ---------------------------------------------------------------------------


async def _seed_book_with_manuscript(db_session) -> tuple[uuid.UUID, uuid.UUID]:
    """Create a book and its manuscript; return (book_id, manuscript_id).

    writing_sessions.manuscript_id is NOT NULL and the service resolves it from
    the book, so a session needs a book that actually has one.
    """
    from app.models.content import ContentType, Manuscript, ManuscriptStatus

    book_id = uuid.uuid4()
    manuscript = Manuscript(
        id=uuid.uuid4(),
        book_id=book_id,
        content_type=ContentType.FICTION,
        status=ManuscriptStatus.DRAFT,
    )
    db_session.add(manuscript)
    await db_session.flush()
    return book_id, manuscript.id


class TestRecordWritingSession:
    @pytest.mark.asyncio
    async def test_record_session_success(self, db_session):
        """Should record a writing session and convert minutes to seconds."""
        user_id = uuid.uuid4()
        book_id, _ = await _seed_book_with_manuscript(db_session)
        chapter_id = None

        data = WritingSessionCreate(
            book_id=book_id,
            chapter_id=chapter_id,
            words_written=500,
            duration_minutes=30,
            notes="Good writing session",
        )

        result = await service.record_writing_session(db_session, user_id, data, org_id=uuid.uuid4())

        assert result.user_id == user_id
        assert result.book_id == book_id
        assert result.words_written == 500
        assert result.duration_minutes == 30

    @pytest.mark.asyncio
    async def test_record_session_no_chapter(self, db_session):
        """Should allow recording session without specific chapter."""
        user_id = uuid.uuid4()
        book_id, _ = await _seed_book_with_manuscript(db_session)

        data = WritingSessionCreate(
            book_id=book_id,
            words_written=300,
            duration_minutes=20,
        )

        result = await service.record_writing_session(db_session, user_id, data, org_id=uuid.uuid4())

        assert result.chapter_id is None
        assert result.words_written == 300
