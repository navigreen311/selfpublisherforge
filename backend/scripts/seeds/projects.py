"""Seed demo projects and books."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentType, Manuscript, ManuscriptStatus
from app.models.project import (
    Book,
    BookFormat,
    BookStatus,
    PenName,
    Project,
    ProjectStatus,
    ProjectType,
)


async def seed_projects(db: AsyncSession, org_id: uuid.UUID) -> dict[str, dict[str, uuid.UUID]]:
    """Seed demo projects and books for an organization.

    Args:
        db: Database session
        org_id: Organization ID (should be Jane's org)

    Returns:
        Dict with project_ids and book_ids mappings
    """
    # Check if PenName exists for this org
    pen_name_result = await db.execute(select(PenName).where(PenName.org_id == org_id, PenName.name == "Jane Doe"))
    pen_name = pen_name_result.scalar_one_or_none()

    if not pen_name:
        pen_name = PenName(
            org_id=org_id,
            name="Jane Doe",
            bio="Award-winning author of fantasy and romance novels",
            active=True,
            brand_guidelines={
                "tone": "engaging and immersive",
                "themes": ["magic", "adventure", "love"],
            },
        )
        db.add(pen_name)
        await db.flush()

    books_data = [
        {
            "title": "The Dragon's Prophecy",
            "subtitle": "Book 1 of the Fire Chronicles",
            "genre": "Fantasy",
            "word_count": 85000,
            "status": BookStatus.PUBLISHED,
            "project_status": ProjectStatus.COMPLETED,
            "isbn": "978-1234567890",
            "asin": "B08ABCD123",
            "metadata": {
                "genre": "Epic Fantasy",
                "target_age": "Adult",
                "keywords": ["dragon", "prophecy", "magic", "quest"],
                "published_date": "2025-06-15",
                "price_usd": 4.99,
                "pages": 340,
            },
        },
        {
            "title": "Cooking with Code",
            "subtitle": "A Developer's Guide to the Kitchen",
            "genre": "Nonfiction",
            "word_count": 35000,
            "status": BookStatus.WRITING,
            "project_status": ProjectStatus.ACTIVE,
            "isbn": None,
            "asin": None,
            "metadata": {
                "genre": "Cookbook/Technology",
                "target_age": "Adult",
                "keywords": ["cooking", "programming", "recipes", "tech"],
                "price_usd": 9.99,
            },
        },
        {
            "title": "Midnight in Manhattan",
            "subtitle": "A Contemporary Romance",
            "genre": "Romance",
            "word_count": 12000,
            "status": BookStatus.DRAFT,
            "project_status": ProjectStatus.DRAFT,
            "isbn": None,
            "asin": None,
            "metadata": {
                "genre": "Contemporary Romance",
                "target_age": "Adult",
                "keywords": ["romance", "new york", "city", "love story"],
            },
        },
    ]

    project_map = {}
    book_map = {}

    for book_data in books_data:
        # Check if book already exists by title
        result = await db.execute(
            select(Book)
            .join(Project)
            .where(
                Project.org_id == org_id,
                Book.title == book_data["title"],
            )
        )
        existing_book = result.scalar_one_or_none()

        if existing_book:
            book_map[book_data["title"]] = existing_book.id
            project_map[book_data["title"]] = existing_book.project_id
            continue

        # Create project
        project = Project(
            org_id=org_id,
            title=book_data["title"],
            type=ProjectType.BOOK,
            status=book_data["project_status"],
            pen_name_id=pen_name.id,
            settings={
                "genre": book_data["genre"],
                "target_word_count": book_data["word_count"],
            },
        )
        db.add(project)
        await db.flush()

        # Create book
        book = Book(
            project_id=project.id,
            title=book_data["title"],
            subtitle=book_data["subtitle"],
            isbn=book_data["isbn"],
            asin=book_data["asin"],
            format=BookFormat.EBOOK,
            status=book_data["status"],
            metadata_=book_data["metadata"],
        )
        db.add(book)
        await db.flush()

        # Create manuscript
        content_type = ContentType.FICTION if book_data["genre"] in ["Fantasy", "Romance"] else ContentType.NONFICTION
        manuscript_status = (
            ManuscriptStatus.FINAL if book_data["status"] == BookStatus.PUBLISHED else ManuscriptStatus.DRAFT
        )

        manuscript = Manuscript(
            book_id=book.id,
            content_type=content_type,
            word_count=book_data["word_count"],
            status=manuscript_status,
            content=f"This is the manuscript content for {book_data['title']}...",
        )
        db.add(manuscript)
        await db.flush()

        project_map[book_data["title"]] = project.id
        book_map[book_data["title"]] = book.id

    await db.commit()

    print(f"✓ Seeded {len(project_map)} projects and books")

    return {"projects": project_map, "books": book_map}
