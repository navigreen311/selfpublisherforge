"""Writer user behavior - content creation pattern.

WriterUser represents 30% of traffic:
- Creates and edits manuscripts
- Generates AI content
- Updates chapters
- Searches knowledge vault for research

Wait time: 2-5 seconds between requests (thoughtful content creation)
"""
from __future__ import annotations

import random
import uuid

from locust import between, task

from ..config import WAIT_TIMES
from . import AuthenticatedUser

wait_config = WAIT_TIMES["writer"]


class WriterUser(AuthenticatedUser):
    """Content creator pattern - writing and editing."""

    wait_time = between(wait_config["min"], wait_config["max"])
    weight = 30  # 30% of total traffic

    # Track created resources for this user
    manuscript_ids: list[str] = []
    chapter_ids: dict[str, list[str]] = {}  # manuscript_id -> [chapter_ids]

    def on_start(self) -> None:
        """Initialize and fetch existing manuscripts."""
        super().on_start()
        self.load_existing_manuscripts()

    def load_existing_manuscripts(self) -> None:
        """Load existing manuscripts for the user."""
        # Get books that might have manuscripts
        response = self.api_get("portfolio/books", name="GET /portfolio/books")
        if response.status_code == 200:
            data = response.json()
            books = data.get("items", [])
            # Store some book IDs as potential manuscript containers
            self.manuscript_ids = [book.get("id") for book in books[:5] if book.get("id")]

    @task(10)
    def work_on_manuscript(self) -> None:
        """Main workflow - work on an existing manuscript or create new chapters."""
        if not self.manuscript_ids:
            return

        book_id = random.choice(self.manuscript_ids)

        # Get manuscript chapters
        response = self.api_get(
            f"ai-writing/books/{book_id}/manuscript/chapters",
            name="GET /ai-writing/books/:id/manuscript/chapters",
        )

        if response.status_code == 200:
            data = response.json()
            chapters = data.get("items", [])

            if chapters:
                # Update an existing chapter (70% of the time)
                if random.random() < 0.7:
                    chapter = random.choice(chapters)
                    chapter_id = chapter.get("id")
                    if chapter_id:
                        self.update_chapter(book_id, chapter_id)
            else:
                # No chapters yet, create one
                self.create_chapter(book_id)

    @task(8)
    def search_knowledge_for_research(self) -> None:
        """Search knowledge vault for content research."""
        research_topics = [
            "character development",
            "plot structure",
            "dialogue tips",
            "world building",
            "genre conventions",
            "writing style",
            "pacing techniques",
            "conflict resolution",
            "story arc",
            "narrative voice",
        ]
        query = random.choice(research_topics)
        self.api_get(
            "knowledge/search",
            params={"query": query, "limit": 10},
            name="GET /knowledge/search",
        )

    @task(7)
    def create_chapter(self, book_id: str | None = None) -> None:
        """Create a new chapter."""
        if not book_id and self.manuscript_ids:
            book_id = random.choice(self.manuscript_ids)

        if not book_id:
            return

        chapter_data = {
            "title": f"Chapter {random.randint(1, 50)}",
            "content": f"This is test content for load testing. {uuid.uuid4()}",
            "order_index": random.randint(1, 100),
        }

        response = self.api_post(
            f"ai-writing/books/{book_id}/manuscript/chapters",
            json=chapter_data,
            name="POST /ai-writing/books/:id/manuscript/chapters",
        )

        if response.status_code == 201:
            chapter = response.json()
            chapter_id = chapter.get("id")
            if chapter_id:
                if book_id not in self.chapter_ids:
                    self.chapter_ids[book_id] = []
                self.chapter_ids[book_id].append(chapter_id)

    @task(6)
    def update_chapter(self, book_id: str, chapter_id: str) -> None:
        """Update an existing chapter."""
        update_data = {
            "content": f"Updated content at {uuid.uuid4()}",
            "status": random.choice(["draft", "in_progress", "completed"]),
        }

        self.api_put(
            f"ai-writing/books/{book_id}/manuscript/chapters/{chapter_id}",
            json=update_data,
            name="PUT /ai-writing/books/:id/manuscript/chapters/:id",
        )

    @task(5)
    def generate_ai_content(self) -> None:
        """Generate AI content (non-streaming for load testing)."""
        generation_prompts = [
            "Write a compelling opening paragraph",
            "Create a dialogue between two characters",
            "Describe a scene in vivid detail",
            "Generate a plot twist",
            "Write a character backstory",
        ]

        request_data = {
            "prompt": random.choice(generation_prompts),
            "operation": "generate_text",
            "stream": False,  # Synchronous for load testing
            "max_tokens": 500,
        }

        self.api_post(
            "ai-writing/generate",
            json=request_data,
            name="POST /ai-writing/generate",
        )

    @task(4)
    def view_manuscript_analysis(self) -> None:
        """Analyze manuscript for readability and quality."""
        if not self.manuscript_ids:
            return

        book_id = random.choice(self.manuscript_ids)
        self.api_get(
            f"ai-writing/books/{book_id}/manuscript/readability-score",
            name="GET /ai-writing/books/:id/manuscript/readability-score",
        )

    @task(3)
    def generate_outline(self) -> None:
        """Generate a writing outline."""
        outline_data = {
            "title": f"Test Book {uuid.uuid4()}",
            "genre": random.choice(["fiction", "non-fiction", "mystery", "romance", "sci-fi"]),
            "description": "A test outline for load testing",
            "target_word_count": random.choice([50000, 75000, 100000]),
        }

        self.api_post(
            "ai-writing/writing/outline/generate",
            json=outline_data,
            name="POST /ai-writing/writing/outline/generate",
        )

    @task(3)
    def view_writing_sessions(self) -> None:
        """View writing session history."""
        self.api_get("ai-writing/writing-sessions", name="GET /ai-writing/writing-sessions")

    @task(2)
    def record_writing_session(self) -> None:
        """Record a writing session."""
        if not self.manuscript_ids:
            return

        session_data = {
            "book_id": random.choice(self.manuscript_ids),
            "words_written": random.randint(100, 2000),
            "duration_minutes": random.randint(15, 120),
        }

        self.api_post(
            "ai-writing/writing-sessions",
            json=session_data,
            name="POST /ai-writing/writing-sessions",
        )

    @task(2)
    def browse_style_clones(self) -> None:
        """Browse available style clones."""
        self.api_get("style-cloning/styles", name="GET /style-cloning/styles")

    @task(1)
    def check_knowledge_vault(self) -> None:
        """Check knowledge vault entries."""
        self.api_get(
            "knowledge",
            params={"limit": 20},
            name="GET /knowledge",
        )
