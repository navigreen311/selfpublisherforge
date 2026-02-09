"""Integration tests for AI Writing Studio API endpoints.

Uses FastAPI TestClient with mocked auth and database.
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.dependencies import get_current_user
from app.database import get_db


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

MOCK_USER = {
    "user_id": uuid.uuid4(),
    "org_id": uuid.uuid4(),
    "role": "owner",
}

BOOK_ID = uuid.uuid4()
CHAPTER_ID = uuid.uuid4()


def _override_current_user():
    return MOCK_USER


class FakeChapter:
    """Mimics the Chapter ORM model for service return values."""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.book_id = kwargs.get("book_id", BOOK_ID)
        self.manuscript_id = kwargs.get("manuscript_id", uuid.uuid4())
        self.title = kwargs.get("title", "Test Chapter")
        self.content = kwargs.get("content", "Chapter content here.")
        self.synopsis = kwargs.get("synopsis", "")
        self.order = kwargs.get("order", 1)
        self.word_count = kwargs.get("word_count", 3)
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))


@pytest.fixture
def override_deps():
    """Override auth dependency for all tests."""
    app.dependency_overrides[get_current_user] = _override_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def async_client(override_deps):
    """Provide an async test client."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ---------------------------------------------------------------------------
# Manuscript & chapter endpoints
# ---------------------------------------------------------------------------

class TestManuscriptEndpoints:
    @pytest.mark.asyncio
    async def test_get_manuscript(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import ManuscriptResponse

        mock_response = ManuscriptResponse(
            book_id=BOOK_ID,
            title="Test Book",
            chapters=[],
            total_word_count=0,
        )
        with patch.object(service, "get_manuscript", new_callable=AsyncMock, return_value=mock_response):
            resp = await async_client.get(f"/api/v1/books/{BOOK_ID}/manuscript")
            assert resp.status_code == 200
            data = resp.json()
            assert data["book_id"] == str(BOOK_ID)

    @pytest.mark.asyncio
    async def test_list_chapters(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import ChapterContent

        mock_chapters = [
            ChapterContent(
                id=CHAPTER_ID,
                book_id=BOOK_ID,
                title="Chapter 1",
                content="Some content.",
                order=1,
                synopsis="Synopsis",
                word_count=2,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]
        with patch.object(service, "list_chapters", new_callable=AsyncMock, return_value=mock_chapters):
            resp = await async_client.get(f"/api/v1/books/{BOOK_ID}/manuscript/chapters")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["title"] == "Chapter 1"

    @pytest.mark.asyncio
    async def test_get_chapter(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import ChapterContent

        mock_chapter = ChapterContent(
            id=CHAPTER_ID,
            book_id=BOOK_ID,
            title="Chapter 1",
            content="Content here.",
            order=1,
            word_count=2,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        with patch.object(service, "get_chapter", new_callable=AsyncMock, return_value=mock_chapter):
            resp = await async_client.get(
                f"/api/v1/books/{BOOK_ID}/manuscript/chapters/{CHAPTER_ID}"
            )
            assert resp.status_code == 200
            assert resp.json()["title"] == "Chapter 1"

    @pytest.mark.asyncio
    async def test_get_chapter_not_found(self, async_client):
        from app.modules.ai_writing import service

        with patch.object(service, "get_chapter", new_callable=AsyncMock, return_value=None):
            resp = await async_client.get(
                f"/api/v1/books/{BOOK_ID}/manuscript/chapters/{uuid.uuid4()}"
            )
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_chapter(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import ChapterContent

        mock_chapter = ChapterContent(
            id=CHAPTER_ID,
            book_id=BOOK_ID,
            title="New Chapter",
            content="Fresh content.",
            order=1,
            word_count=2,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        with patch.object(service, "create_chapter", new_callable=AsyncMock, return_value=mock_chapter):
            resp = await async_client.post(
                f"/api/v1/books/{BOOK_ID}/manuscript/chapters",
                json={"title": "New Chapter", "content": "Fresh content.", "order": 1},
            )
            assert resp.status_code == 201
            assert resp.json()["title"] == "New Chapter"

    @pytest.mark.asyncio
    async def test_update_chapter(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import ChapterContent

        mock_chapter = ChapterContent(
            id=CHAPTER_ID,
            book_id=BOOK_ID,
            title="Updated Title",
            content="Updated content.",
            order=1,
            word_count=2,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        with patch.object(service, "update_chapter", new_callable=AsyncMock, return_value=mock_chapter):
            resp = await async_client.put(
                f"/api/v1/books/{BOOK_ID}/manuscript/chapters/{CHAPTER_ID}",
                json={"title": "Updated Title", "content": "Updated content."},
            )
            assert resp.status_code == 200
            assert resp.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_chapter_not_found(self, async_client):
        from app.modules.ai_writing import service

        with patch.object(service, "update_chapter", new_callable=AsyncMock, return_value=None):
            resp = await async_client.put(
                f"/api/v1/books/{BOOK_ID}/manuscript/chapters/{uuid.uuid4()}",
                json={"title": "Nope"},
            )
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_reorder_chapters(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import ChapterContent

        ch1_id = uuid.uuid4()
        ch2_id = uuid.uuid4()
        mock_chapters = [
            ChapterContent(
                id=ch1_id, book_id=BOOK_ID, title="Ch 1", content="", order=2,
                word_count=0, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
            ),
            ChapterContent(
                id=ch2_id, book_id=BOOK_ID, title="Ch 2", content="", order=1,
                word_count=0, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
            ),
        ]
        with patch.object(service, "reorder_chapters", new_callable=AsyncMock, return_value=mock_chapters):
            resp = await async_client.patch(
                f"/api/v1/books/{BOOK_ID}/manuscript/chapters/reorder",
                json={
                    "chapters": [
                        {"chapter_id": str(ch1_id), "order": 2},
                        {"chapter_id": str(ch2_id), "order": 1},
                    ]
                },
            )
            assert resp.status_code == 200
            assert len(resp.json()) == 2


# ---------------------------------------------------------------------------
# Analysis / Readability
# ---------------------------------------------------------------------------

class TestAnalysisEndpoints:
    @pytest.mark.asyncio
    async def test_analyze_manuscript(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import ManuscriptAnalysis, ReadabilityScore

        mock_analysis = ManuscriptAnalysis(
            book_id=BOOK_ID,
            readability=ReadabilityScore(
                flesch_kincaid_grade=5.0,
                flesch_reading_ease=70.0,
                gunning_fog=6.0,
                smog_index=5.0,
                word_count=500,
                sentence_count=25,
                syllable_count=650,
                avg_words_per_sentence=20.0,
                avg_syllables_per_word=1.3,
                reading_level="Middle School",
            ),
            total_word_count=500,
            chapter_count=3,
            avg_chapter_word_count=166.7,
            pacing_notes=["Chapters are short. Consider expanding key scenes."],
        )
        with patch.object(service, "analyze_manuscript", new_callable=AsyncMock, return_value=mock_analysis):
            resp = await async_client.post(f"/api/v1/books/{BOOK_ID}/manuscript/analyze")
            assert resp.status_code == 200
            data = resp.json()
            assert "readability" in data
            assert data["total_word_count"] == 500

    @pytest.mark.asyncio
    async def test_readability_score(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import ReadabilityScore

        mock_score = ReadabilityScore(
            flesch_kincaid_grade=8.0,
            flesch_reading_ease=55.0,
            gunning_fog=10.0,
            smog_index=9.0,
            word_count=1000,
            sentence_count=50,
            syllable_count=1400,
            avg_words_per_sentence=20.0,
            avg_syllables_per_word=1.4,
            reading_level="High School",
        )
        with patch.object(service, "get_readability_score", new_callable=AsyncMock, return_value=mock_score):
            resp = await async_client.get(
                f"/api/v1/books/{BOOK_ID}/manuscript/readability-score"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["reading_level"] == "High School"


# ---------------------------------------------------------------------------
# Generation endpoint
# ---------------------------------------------------------------------------

class TestGenerateEndpoint:
    @pytest.mark.asyncio
    async def test_generate_non_streaming(self, async_client):
        from app.modules.ai_writing.schemas import GenerateResponse, GenerationType

        mock_response = GenerateResponse(
            request_id=uuid.uuid4(),
            generation_type=GenerationType.blurb,
            content="A great blurb.",
            tokens_used=5,
            quality_results={},
            model_used="claude-sonnet-4-5-20250929",
            created_at=datetime.now(timezone.utc),
        )
        with patch(
            "app.modules.ai_writing.router.generate_sync",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            resp = await async_client.post(
                "/api/v1/generate",
                json={
                    "generation_type": "blurb",
                    "project_id": str(uuid.uuid4()),
                    "instructions": "Write a blurb",
                    "stream": False,
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["content"] == "A great blurb."

    @pytest.mark.asyncio
    async def test_generate_streaming_returns_event_stream(self, async_client):
        from app.modules.ai_writing import generator

        async def mock_stream(request):
            yield 'event: token\ndata: {"text": "Hello"}\n\n'
            yield 'event: complete\ndata: {"content": "Hello"}\n\n'

        with patch.object(generator, "generate_stream", side_effect=mock_stream):
            resp = await async_client.post(
                "/api/v1/generate",
                json={
                    "generation_type": "chapter",
                    "project_id": str(uuid.uuid4()),
                    "instructions": "Write a chapter",
                    "stream": True,
                },
            )
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# Outline endpoint
# ---------------------------------------------------------------------------

class TestOutlineEndpoint:
    @pytest.mark.asyncio
    async def test_generate_outline(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import OutlineResponse, OutlineChapter

        mock_response = OutlineResponse(
            book_id=BOOK_ID,
            chapters=[
                OutlineChapter(
                    title="Chapter 1: The Beginning",
                    synopsis="The story begins.",
                    key_points=["Introduction", "Setting"],
                ),
            ],
            summary="A hero's journey story.",
            generated_at=datetime.now(timezone.utc),
        )
        with patch.object(service, "generate_outline", new_callable=AsyncMock, return_value=mock_response):
            resp = await async_client.post(
                f"/api/v1/books/{BOOK_ID}/outline/generate",
                json={"genre": "fantasy", "premise": "A hero's journey", "num_chapters": 12},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["chapters"]) == 1


# ---------------------------------------------------------------------------
# Writing sessions
# ---------------------------------------------------------------------------

class TestWritingSessionEndpoint:
    @pytest.mark.asyncio
    async def test_record_session(self, async_client):
        from app.modules.ai_writing import service
        from app.modules.ai_writing.schemas import WritingSessionRecord

        session_id = uuid.uuid4()
        mock_record = WritingSessionRecord(
            id=session_id,
            user_id=MOCK_USER["user_id"],
            book_id=BOOK_ID,
            words_written=500,
            duration_minutes=30,
            chapter_id=None,
            notes="Good session",
            created_at=datetime.now(timezone.utc),
        )
        with patch.object(service, "record_writing_session", new_callable=AsyncMock, return_value=mock_record):
            resp = await async_client.post(
                "/api/v1/writing-sessions",
                json={
                    "book_id": str(BOOK_ID),
                    "words_written": 500,
                    "duration_minutes": 30,
                    "notes": "Good session",
                },
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["words_written"] == 500


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestRequestValidation:
    @pytest.mark.asyncio
    async def test_generate_missing_instructions(self, async_client):
        resp = await async_client.post(
            "/api/v1/generate",
            json={
                "generation_type": "chapter",
                "project_id": str(uuid.uuid4()),
                # instructions is missing
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_invalid_type(self, async_client):
        resp = await async_client.post(
            "/api/v1/generate",
            json={
                "generation_type": "invalid_type",
                "project_id": str(uuid.uuid4()),
                "instructions": "Do something",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_chapter_empty_title(self, async_client):
        resp = await async_client.post(
            f"/api/v1/books/{BOOK_ID}/manuscript/chapters",
            json={"title": "", "content": "something"},
        )
        assert resp.status_code == 422
