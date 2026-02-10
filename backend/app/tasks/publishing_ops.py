"""Celery tasks for the Publishing Operations Center.

Async tasks for:
- EPUB export generation
- PDF export generation
- Listing sync with external platforms
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.tasks import celery_app


@celery_app.task(
    name="publishing.generate_epub",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def task_generate_epub(
    self,
    export_id: str,
    book_id: str,
    chapters: list[dict],
    title: str = "Untitled",
    authors: list[str] | None = None,
    language: str = "en",
    style_settings: dict | None = None,
    include_toc: bool = True,
    include_cover: bool = True,
    cover_image_url: str | None = None,
) -> dict:
    """Generate an EPUB file asynchronously.

    This task is queued when a user requests an EPUB export. It:
    1. Rebuilds the ExportRequest from serialised data
    2. Calls the epub_generator to produce bytes
    3. Uploads to S3 (placeholder)
    4. Updates the export record with file URL and size
    """
    from app.modules.publishing_ops.schemas import (
        ChapterInput,
        ExportRequest,
        ExportFormat,
        TemplateStyleSettings,
    )
    from app.modules.publishing_ops.epub_generator import generate_epub

    try:
        chapter_inputs = [ChapterInput(**ch) for ch in chapters]
        request = ExportRequest(
            book_id=uuid.UUID(book_id),
            format=ExportFormat.EPUB,
            chapters=chapter_inputs,
            include_toc=include_toc,
            include_cover=include_cover,
            cover_image_url=cover_image_url,
        )

        settings = TemplateStyleSettings(**style_settings) if style_settings else None
        epub_bytes = generate_epub(
            request,
            title=title,
            authors=authors,
            language=language,
            style_settings=settings,
        )

        # In production: upload epub_bytes to S3 and get the URL
        file_url = f"/exports/{export_id}.epub"
        file_size = len(epub_bytes)

        return {
            "export_id": export_id,
            "status": "completed",
            "file_url": file_url,
            "file_size_bytes": file_size,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="publishing.generate_pdf",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def task_generate_pdf(
    self,
    export_id: str,
    book_id: str,
    chapters: list[dict],
    title: str = "Untitled",
    authors: list[str] | None = None,
    trim_size: str = "6x9",
    isbn: str | None = None,
    include_isbn_barcode: bool = False,
    style_settings: dict | None = None,
) -> dict:
    """Generate a print-ready PDF asynchronously.

    Similar flow to EPUB but uses pdf_generator and includes
    trim-size / ISBN barcode handling.
    """
    from app.modules.publishing_ops.schemas import (
        ChapterInput,
        ExportRequest,
        ExportFormat,
        TemplateStyleSettings,
        TrimSize,
    )
    from app.modules.publishing_ops.pdf_generator import generate_pdf_bytes

    try:
        chapter_inputs = [ChapterInput(**ch) for ch in chapters]
        request = ExportRequest(
            book_id=uuid.UUID(book_id),
            format=ExportFormat.PDF,
            chapters=chapter_inputs,
            trim_size=TrimSize(trim_size),
            isbn=isbn,
            include_isbn_barcode=include_isbn_barcode,
        )

        settings = TemplateStyleSettings(**style_settings) if style_settings else None
        pdf_bytes = generate_pdf_bytes(
            request,
            title=title,
            authors=authors,
            style_settings=settings,
        )

        file_url = f"/exports/{export_id}.pdf"
        file_size = len(pdf_bytes)

        return {
            "export_id": export_id,
            "status": "completed",
            "file_url": file_url,
            "file_size_bytes": file_size,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="publishing.sync_listing",
    bind=True,
    max_retries=5,
    default_retry_delay=120,
    acks_late=True,
)
def task_sync_listing(
    self,
    listing_id: str,
    platform: str,
    account_credentials: dict | None = None,
) -> dict:
    """Sync a book listing with an external publishing platform.

    In production this would:
    1. Authenticate with the platform API using stored credentials
    2. Fetch current listing data (price, rank, reviews, status)
    3. Push any local metadata updates to the platform
    4. Update the local listing record
    """
    try:
        # Placeholder: simulate a successful sync
        return {
            "listing_id": listing_id,
            "platform": platform,
            "status": "synced",
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Successfully synced listing with {platform}",
        }
    except Exception as exc:
        raise self.retry(exc=exc)
