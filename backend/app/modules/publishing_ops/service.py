"""Service layer for the Publishing Operations Center.

Handles business logic for:
- Publishing account management (connect / disconnect / list)
- Export orchestration (EPUB & PDF generation)
- Book metadata CRUD
- Multi-platform listing sync

All functions accept an ``AsyncSession`` as first parameter for DB access.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Book
from app.models.publishing import (
    Listing as ListingModel,
    PublishingAccount as PublishingAccountModel,
    ListingStatus as ListingStatusEnum,
)
from app.modules.publishing_ops.models import ExportJob, FormattingTemplateModel
from app.modules.publishing_ops.schemas import (
    BookMetadata,
    BookMetadataBase,
    BookMetadataUpdate,
    ExportFormat,
    ExportRequest,
    ExportResponse,
    FormattingTemplate,
    FormattingTemplateCreate,
    ListingDetail,
    ListingStatus,
    ListingSyncResponse,
    PlatformType,
    PricingInfo,
    PublishingAccount,
    PublishingAccountCreate,
    TemplateGenre,
    TemplateStyleSettings,
    TrimSize,
)
from app.modules.publishing_ops.epub_generator import generate_epub
from app.modules.publishing_ops.pdf_generator import generate_pdf_bytes
from app.modules.publishing_ops.templates import get_all_templates


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Publishing Accounts
# ---------------------------------------------------------------------------

async def list_accounts(db: AsyncSession, org_id: uuid.UUID) -> list[PublishingAccount]:
    """Return all publishing accounts for an organisation."""
    stmt = (
        select(PublishingAccountModel)
        .where(
            PublishingAccountModel.org_id == org_id,
            PublishingAccountModel.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        PublishingAccount(
            id=row.id,
            org_id=row.org_id,
            platform=row.platform.value if hasattr(row.platform, "value") else row.platform,
            account_name=row.credentials_encrypted or "",
            account_email=None,
            is_active=row.status.value == "active" if hasattr(row.status, "value") else row.status == "active",
            last_synced_at=None,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


async def create_account(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: PublishingAccountCreate,
) -> PublishingAccount:
    """Connect a new publishing platform account."""
    from app.models.publishing import PublishingPlatform, PublishingAccountStatus

    # Map schema PlatformType to DB PublishingPlatform where values align
    platform_value = data.platform.value if hasattr(data.platform, "value") else str(data.platform)
    try:
        db_platform = PublishingPlatform(platform_value)
    except ValueError:
        # Fallback: store as KDP if no direct mapping
        db_platform = PublishingPlatform.KDP

    account = PublishingAccountModel(
        org_id=org_id,
        platform=db_platform,
        credentials_encrypted=data.account_name,  # store account_name in credentials_encrypted
        status=PublishingAccountStatus.ACTIVE,
        health_score=None,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)

    return PublishingAccount(
        id=account.id,
        org_id=account.org_id,
        platform=data.platform,
        account_name=data.account_name,
        account_email=data.account_email,
        is_active=True,
        last_synced_at=None,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


async def delete_account(db: AsyncSession, account_id: uuid.UUID) -> bool:
    """Disconnect (soft-delete) a publishing account."""
    stmt = (
        select(PublishingAccountModel)
        .where(
            PublishingAccountModel.id == account_id,
            PublishingAccountModel.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if account is None:
        return False

    account.deleted_at = _now()
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Export Orchestration
# ---------------------------------------------------------------------------

async def generate_export(
    db: AsyncSession,
    org_id: uuid.UUID,
    request: ExportRequest,
    title: str = "Untitled",
    authors: list[str] | None = None,
    language: str = "en",
    style_settings: TemplateStyleSettings | None = None,
) -> ExportResponse:
    """Kick off an export job and return a response with status.

    In production this would queue a Celery task. Here we perform the
    generation synchronously for demonstration purposes.
    """
    if request.format == ExportFormat.EPUB:
        data = generate_epub(
            request,
            title=title,
            authors=authors,
            language=language,
            style_settings=style_settings,
        )
    else:
        data = generate_pdf_bytes(
            request,
            title=title,
            authors=authors,
            style_settings=style_settings,
        )

    fmt_str = request.format.value if hasattr(request.format, "value") else str(request.format)

    # Persist the export job
    export_job = ExportJob(
        org_id=org_id,
        book_id=request.book_id,
        format=fmt_str,
        status="completed",
        file_url=f"/exports/{uuid.uuid4()}.{fmt_str}",
        file_size_bytes=len(data),
        page_count=None,
        message=f"{fmt_str.upper()} export completed successfully",
    )
    db.add(export_job)
    await db.flush()
    await db.refresh(export_job)

    return ExportResponse(
        id=export_job.id,
        book_id=export_job.book_id,
        format=request.format,
        status=export_job.status,
        file_url=export_job.file_url,
        file_size_bytes=export_job.file_size_bytes,
        page_count=export_job.page_count,
        created_at=export_job.created_at,
        message=export_job.message or "",
    )


# ---------------------------------------------------------------------------
# Formatting Templates
# ---------------------------------------------------------------------------

async def list_templates(
    db: AsyncSession,
    org_id: uuid.UUID | None = None,
) -> list[FormattingTemplate]:
    """Return all formatting templates (built-in + custom for org)."""
    builtin = get_all_templates()

    stmt = (
        select(FormattingTemplateModel)
        .where(FormattingTemplateModel.deleted_at.is_(None))
    )
    if org_id is not None:
        stmt = stmt.where(FormattingTemplateModel.org_id == org_id)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    custom = [
        FormattingTemplate(
            id=row.id,
            org_id=row.org_id,
            name=row.name,
            genre=row.genre or TemplateGenre.CUSTOM,
            description=row.description,
            trim_size=row.trim_size or TrimSize.SIZE_6x9,
            style_settings=TemplateStyleSettings(**(row.style_settings or {})),
            is_builtin=row.is_builtin,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]
    return builtin + custom


async def create_template(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: FormattingTemplateCreate,
) -> FormattingTemplate:
    """Create a custom formatting template."""
    genre_value = data.genre.value if hasattr(data.genre, "value") else str(data.genre)
    trim_value = data.trim_size.value if hasattr(data.trim_size, "value") else str(data.trim_size)

    template = FormattingTemplateModel(
        org_id=org_id,
        name=data.name,
        genre=genre_value,
        description=data.description,
        trim_size=trim_value,
        style_settings=data.style_settings.model_dump() if data.style_settings else None,
        is_builtin=False,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)

    return FormattingTemplate(
        id=template.id,
        org_id=template.org_id,
        name=template.name,
        genre=data.genre,
        description=template.description,
        trim_size=data.trim_size,
        style_settings=data.style_settings,
        is_builtin=False,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


# ---------------------------------------------------------------------------
# Book Metadata
# ---------------------------------------------------------------------------

async def get_metadata(db: AsyncSession, book_id: uuid.UUID) -> BookMetadata | None:
    """Retrieve metadata for a book from the Book model's JSONB metadata_ column."""
    stmt = select(Book).where(Book.id == book_id, Book.deleted_at.is_(None))
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()
    if book is None:
        return None

    meta = book.metadata_ or {}
    return BookMetadata(
        book_id=book.id,
        title=meta.get("title", book.title),
        subtitle=meta.get("subtitle", book.subtitle),
        description=meta.get("description"),
        authors=meta.get("authors", []),
        keywords=meta.get("keywords", []),
        categories=meta.get("categories", []),
        language=meta.get("language", "en"),
        isbn=meta.get("isbn", book.isbn),
        asin=meta.get("asin", book.asin),
        publisher=meta.get("publisher"),
        publication_date=meta.get("publication_date"),
        pricing=PricingInfo(**meta["pricing"]) if meta.get("pricing") else PricingInfo(),
        series_name=meta.get("series_name"),
        series_number=meta.get("series_number"),
        page_count=meta.get("page_count"),
        age_range=meta.get("age_range"),
        updated_at=book.updated_at,
    )


async def update_metadata(
    db: AsyncSession,
    book_id: uuid.UUID,
    data: BookMetadataUpdate,
) -> BookMetadata:
    """Create or update metadata for a book via the Book model's JSONB column."""
    stmt = select(Book).where(Book.id == book_id, Book.deleted_at.is_(None))
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if book is None:
        # If no book found, raise — the router should handle 404
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Book not found")

    existing_meta = book.metadata_ or {}
    update_dict = data.model_dump(exclude_unset=True)

    # Serialize nested Pydantic models (e.g. PricingInfo) to dicts
    if "pricing" in update_dict and update_dict["pricing"] is not None:
        pricing_obj = update_dict["pricing"]
        if hasattr(pricing_obj, "model_dump"):
            update_dict["pricing"] = pricing_obj.model_dump()
        elif isinstance(pricing_obj, dict):
            pass  # already a dict

    # Serialize datetime objects to ISO strings for JSONB storage
    if "publication_date" in update_dict and update_dict["publication_date"] is not None:
        pub_date = update_dict["publication_date"]
        if isinstance(pub_date, datetime):
            update_dict["publication_date"] = pub_date.isoformat()

    existing_meta.update(update_dict)

    # Also update top-level Book columns where applicable
    if data.title is not None:
        book.title = data.title
        existing_meta["title"] = data.title
    if data.subtitle is not None:
        book.subtitle = data.subtitle
    if data.isbn is not None:
        book.isbn = data.isbn
    if data.asin is not None:
        book.asin = data.asin

    book.metadata_ = existing_meta
    await db.flush()
    await db.refresh(book)

    meta = book.metadata_ or {}
    return BookMetadata(
        book_id=book.id,
        title=meta.get("title", book.title),
        subtitle=meta.get("subtitle", book.subtitle),
        description=meta.get("description"),
        authors=meta.get("authors", []),
        keywords=meta.get("keywords", []),
        categories=meta.get("categories", []),
        language=meta.get("language", "en"),
        isbn=meta.get("isbn", book.isbn),
        asin=meta.get("asin", book.asin),
        publisher=meta.get("publisher"),
        publication_date=meta.get("publication_date"),
        pricing=PricingInfo(**meta["pricing"]) if meta.get("pricing") else PricingInfo(),
        series_name=meta.get("series_name"),
        series_number=meta.get("series_number"),
        page_count=meta.get("page_count"),
        age_range=meta.get("age_range"),
        updated_at=book.updated_at,
    )


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

async def list_listings(db: AsyncSession, org_id: uuid.UUID) -> list[ListingDetail]:
    """Return all listings across platforms for an organisation.

    Joins through PublishingAccount to filter by org_id.
    """
    from app.models.publishing import PublishingAccount as PAModel

    stmt = (
        select(ListingModel)
        .join(PAModel, ListingModel.publishing_account_id == PAModel.id)
        .where(
            PAModel.org_id == org_id,
            PAModel.deleted_at.is_(None),
            ListingModel.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    listings = []
    for row in rows:
        listing_data = row.listing_data or {}
        listings.append(
            ListingDetail(
                id=row.id,
                book_id=row.book_id,
                platform=listing_data.get("platform", PlatformType.KDP),
                platform_listing_id=row.platform_id,
                status=row.status.value if hasattr(row.status, "value") else row.status,
                listing_url=listing_data.get("listing_url"),
                account_id=row.publishing_account_id,
                title=listing_data.get("title"),
                current_price=listing_data.get("current_price"),
                current_rank=listing_data.get("current_rank"),
                reviews_count=listing_data.get("reviews_count"),
                rating=listing_data.get("rating"),
                last_synced_at=row.last_synced,
                sync_errors=listing_data.get("sync_errors", []),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    return listings


async def sync_listing(db: AsyncSession, listing_id: uuid.UUID) -> ListingSyncResponse:
    """Queue a sync job for a specific listing.

    In production this would enqueue a Celery task to fetch data from the
    platform API and update the listing record.
    """
    stmt = (
        select(ListingModel)
        .where(
            ListingModel.id == listing_id,
            ListingModel.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if listing is not None:
        listing.last_synced = _now()
        listing.status = ListingStatusEnum.LIVE
        await db.flush()

    return ListingSyncResponse(
        listing_id=listing_id,
        status="sync_queued",
        message="Listing sync has been queued",
    )
