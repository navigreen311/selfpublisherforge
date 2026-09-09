"""Celery tasks for the Publishing Operations Center.

Async tasks for:
- EPUB export generation
- PDF export generation
- Listing sync with external platforms

Time limit strategy
-------------------
Each task declares explicit ``soft_time_limit`` and ``time_limit`` values
(in seconds) based on expected workload:
  - Quick   (notifications, status updates):   soft=60,   hard=120
  - Medium  (API calls, data sync):            soft=300,  hard=600
  - Long    (bulk imports, report generation):  soft=1800, hard=3600
  - V. Long (full analytics aggregation):       soft=3300, hard=3600
Global defaults in config.py are 3300/3600 but per-task limits take precedence.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from celery.exceptions import SoftTimeLimitExceeded

from app.config import get_settings
from app.tasks import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# S3 upload helper
# ---------------------------------------------------------------------------


def _upload_to_s3(
    file_bytes: bytes,
    s3_key: str,
    content_type: str,
) -> str:
    """Upload bytes to S3 and return the object URL.

    Reads AWS credentials and bucket configuration from application settings.
    Raises on upload failure so the calling task can retry.
    """
    settings = get_settings()
    s3_client = boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )

    s3_client.put_object(
        Bucket=settings.S3_BUCKET,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
    )

    file_url = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{s3_key}"
    logger.info("Uploaded %d bytes to s3://%s/%s", len(file_bytes), settings.S3_BUCKET, s3_key)
    return file_url


# ---------------------------------------------------------------------------
# Platform API availability registry  (v2 feature -- intentionally empty)
# ---------------------------------------------------------------------------
#
# _SUPPORTED_PLATFORM_APIS controls which platform adapters are considered
# "live" for external listing sync.  In v1.0 this set is intentionally empty:
# all sync requests will be accepted and the listing is persisted locally, but
# no outbound API call is made.  The listing is marked ``sync_pending`` so it
# can be automatically synced once the corresponding adapter ships.
#
# Planned platform adapters for v2:
#   - "amazon_kdp"       -- Amazon Kindle Direct Publishing
#   - "apple_books"      -- Apple Books for Authors
#   - "barnes_noble"     -- Barnes & Noble Press
#   - "kobo"             -- Kobo Writing Life
#   - "google_play"      -- Google Play Books Partner Center
#   - "draft2digital"    -- Draft2Digital / Smashwords
#   - "ingramspark"      -- IngramSpark
#
# To enable a platform, implement its adapter in
# ``app.modules.publishing_ops.platform_adapters`` and add its lowercase key
# to this set.
# ---------------------------------------------------------------------------
_SUPPORTED_PLATFORM_APIS: set[str] = set()


@celery_app.task(
    name="publishing.generate_epub",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=1800,
    time_limit=3600,
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
    3. Uploads the EPUB to S3
    4. Updates the export record with file URL and size
    """
    from app.modules.publishing_ops.epub_generator import generate_epub
    from app.modules.publishing_ops.schemas import (
        ChapterInput,
        ExportFormat,
        ExportRequest,
        TemplateStyleSettings,
    )

    try:
        logger.info("Generating EPUB for export_id=%s, book_id=%s", export_id, book_id)

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

        filename = f"{export_id}.epub"
        s3_key = f"exports/{book_id}/epub/{filename}"
        file_url = _upload_to_s3(epub_bytes, s3_key, content_type="application/epub+zip")
        file_size = len(epub_bytes)

        logger.info(
            "EPUB export completed: export_id=%s, size=%d bytes, url=%s",
            export_id,
            file_size,
            file_url,
        )

        return {
            "export_id": export_id,
            "status": "completed",
            "file_url": file_url,
            "file_size_bytes": file_size,
            "generated_at": datetime.now(UTC).isoformat(),
        }
    except ClientError as exc:
        logger.error("S3 upload failed for EPUB export_id=%s: %s", export_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc
    except (ValueError, TypeError, KeyError) as exc:
        logger.error("Data validation error in EPUB generation for export_id=%s: %s", export_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error("EPUB generation failed for export_id=%s: %s", export_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="publishing.generate_pdf",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=1800,
    time_limit=3600,
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
    from app.modules.publishing_ops.pdf_generator import generate_pdf_bytes
    from app.modules.publishing_ops.schemas import (
        ChapterInput,
        ExportFormat,
        ExportRequest,
        TemplateStyleSettings,
        TrimSize,
    )

    try:
        logger.info("Generating PDF for export_id=%s, book_id=%s", export_id, book_id)

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

        filename = f"{export_id}.pdf"
        s3_key = f"exports/{book_id}/pdf/{filename}"
        file_url = _upload_to_s3(pdf_bytes, s3_key, content_type="application/pdf")
        file_size = len(pdf_bytes)

        logger.info(
            "PDF export completed: export_id=%s, size=%d bytes, url=%s",
            export_id,
            file_size,
            file_url,
        )

        return {
            "export_id": export_id,
            "status": "completed",
            "file_url": file_url,
            "file_size_bytes": file_size,
            "generated_at": datetime.now(UTC).isoformat(),
        }
    except ClientError as exc:
        logger.error("S3 upload failed for PDF export_id=%s: %s", export_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc
    except (ValueError, TypeError, KeyError) as exc:
        logger.error("Data validation error in PDF generation for export_id=%s: %s", export_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error("PDF generation failed for export_id=%s: %s", export_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="publishing.sync_listing",
    bind=True,
    max_retries=5,
    default_retry_delay=120,
    acks_late=True,
    soft_time_limit=300,
    time_limit=600,
)
def task_sync_listing(
    self,
    listing_id: str,
    platform: str,
    account_credentials: dict | None = None,
) -> dict:
    """Sync a book listing with an external publishing platform.

    Steps:
    1. Load the listing from the database
    2. Determine the platform from the listing's publishing account
    3. If the platform API is available, perform the sync and mark as synced
    4. If the platform API is not available, set status to sync_pending
    5. Update the last_synced_at timestamp on the listing record
    """
    from sqlalchemy import select

    from app.database import async_session
    from app.models.publishing import (
        Listing as ListingModel,
    )
    from app.models.publishing import (
        ListingStatus as ListingStatusEnum,
    )

    async def _sync():
        async with async_session() as db:
            stmt = select(ListingModel).where(
                ListingModel.id == uuid.UUID(listing_id),
                ListingModel.deleted_at.is_(None),
            )
            result = await db.execute(stmt)
            listing = result.scalar_one_or_none()

            if listing is None:
                logger.warning("Listing %s not found in database", listing_id)
                return {
                    "listing_id": listing_id,
                    "platform": platform,
                    "status": "not_found",
                    "synced_at": datetime.now(UTC).isoformat(),
                    "message": f"Listing {listing_id} not found",
                }

            # Resolve the effective platform from the listing's data or the
            # linked publishing account, falling back to the task argument.
            listing_data = listing.listing_data or {}
            effective_platform = listing_data.get("platform", platform)

            now = datetime.now(UTC)

            logger.info(
                "Listing sync attempted: listing_id=%s, platform=%s",
                listing_id,
                effective_platform,
            )

            if effective_platform.lower() in _SUPPORTED_PLATFORM_APIS:
                # Platform API is integrated -- perform real sync here.
                # When a real adapter exists this is where it would be called,
                # e.g.: adapter = get_platform_adapter(effective_platform)
                #        adapter.sync(listing, account_credentials)
                listing.status = ListingStatusEnum.LIVE
                listing.last_synced = now
                sync_status = "synced"
                message = f"Successfully synced listing with {effective_platform}"
                logger.info(
                    "Listing %s synced with %s",
                    listing_id,
                    effective_platform,
                )
            else:
                # Platform API adapter is not yet available -- mark as pending
                # rather than falsely reporting success.
                listing.status = ListingStatusEnum.PENDING
                listing.last_synced = now
                sync_status = "sync_pending"
                message = (
                    f"Platform sync for {effective_platform} is coming in a future release. "
                    f"Your listing has been saved locally and will be synced automatically "
                    f"when the integration is available."
                )
                logger.info(
                    "Listing %s marked sync_pending -- no API adapter for %s",
                    listing_id,
                    effective_platform,
                )

            # Persist the sync metadata inside listing_data
            listing_data["last_sync_status"] = sync_status
            listing_data["last_sync_message"] = message
            listing.listing_data = listing_data

            await db.commit()

            return {
                "listing_id": listing_id,
                "platform": effective_platform,
                "status": sync_status,
                "synced_at": now.isoformat(),
                "message": message,
            }

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, _sync()).result()
        else:
            result = loop.run_until_complete(_sync())
    except RuntimeError:
        result = asyncio.run(_sync())
    except SoftTimeLimitExceeded:
        logger.warning("Task %s hit soft time limit, cleaning up", self.request.id)
        raise
    except Exception as exc:
        logger.error("Listing sync failed for listing_id=%s: %s", listing_id, exc, exc_info=True)
        raise self.retry(exc=exc) from exc

    return result
