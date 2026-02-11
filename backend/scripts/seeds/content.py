"""Seed demo chapters and content for books."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Chapter, ChapterStatus, Manuscript


# Sample chapter data for each book type
FANTASY_CHAPTERS = [
    "The Awakening",
    "Whispers in the Dark",
    "The Dragon's Lair",
    "Ancient Prophecies",
    "The Final Battle",
]

COOKBOOK_CHAPTERS = [
    "Getting Started: Your Dev Kitchen",
    "Debugging Dinner: Troubleshooting Recipes",
    "Main Functions: Entrees That Scale",
    "Side Dishes: Modular Meal Components",
    "Dessert Exceptions: Sweet Error Handling",
]

ROMANCE_CHAPTERS = [
    "First Encounter",
    "Coffee Shop Conversations",
    "Unexpected Connections",
    "Midnight Confessions",
    "Happily Ever After",
]


async def seed_content(db: AsyncSession, book_ids: dict[str, uuid.UUID]) -> None:
    """Seed demo chapters for books.

    Args:
        db: Database session
        book_ids: Dict mapping book titles to book IDs
    """
    books_chapters = {
        "The Dragon's Prophecy": FANTASY_CHAPTERS,
        "Cooking with Code": COOKBOOK_CHAPTERS,
        "Midnight in Manhattan": ROMANCE_CHAPTERS,
    }

    total_chapters = 0

    for book_title, chapter_titles in books_chapters.items():
        if book_title not in book_ids:
            continue

        book_id = book_ids[book_title]

        # Get the manuscript for this book
        result = await db.execute(
            select(Manuscript).where(Manuscript.book_id == book_id)
        )
        manuscript = result.scalar_one_or_none()

        if not manuscript:
            print(f"⚠ No manuscript found for {book_title}, skipping chapters")
            continue

        # Check if chapters already exist
        existing_result = await db.execute(
            select(Chapter).where(Chapter.manuscript_id == manuscript.id).limit(1)
        )
        if existing_result.scalar_one_or_none():
            print(f"✓ Chapters already exist for {book_title}, skipping")
            continue

        # Create chapters
        for idx, chapter_title in enumerate(chapter_titles, start=1):
            # Determine chapter status based on book status
            if book_title == "The Dragon's Prophecy":
                # Published book - all chapters are final
                status = ChapterStatus.FINAL
                word_count = 17000  # 85k / 5 chapters
            elif book_title == "Cooking with Code":
                # In-progress book - mix of statuses
                if idx <= 3:
                    status = ChapterStatus.FINAL
                    word_count = 7000  # 35k / 5 chapters
                else:
                    status = ChapterStatus.DRAFT
                    word_count = 3500
            else:
                # Draft book - all chapters are outline/draft
                status = ChapterStatus.OUTLINE if idx > 2 else ChapterStatus.DRAFT
                word_count = 2400 if idx <= 2 else 0

            chapter = Chapter(
                manuscript_id=manuscript.id,
                title=chapter_title,
                order_index=idx - 1,
                word_count=word_count,
                status=status,
                content=f"Chapter content for '{chapter_title}'...\n\n"
                + (
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                    * (word_count // 10)
                )
                if word_count > 0
                else "",
                ai_metrics={
                    "readability_score": 75.5 + (idx * 2),
                    "sentiment": "positive",
                    "pacing": "moderate",
                },
            )
            db.add(chapter)
            total_chapters += 1

    await db.commit()

    print(f"✓ Seeded {total_chapters} chapters across {len(books_chapters)} books")
