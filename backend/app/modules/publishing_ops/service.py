"""Service layer for the Publishing Operations Center.

Handles business logic for:
- Publishing account management (connect / disconnect / list)
- Export orchestration (EPUB & PDF generation)
- Book metadata CRUD
- Multi-platform listing sync
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

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
# In-memory stores (replace with DB queries in production)
# ---------------------------------------------------------------------------

_accounts: dict[uuid.UUID, PublishingAccount] = {}
_metadata: dict[uuid.UUID, BookMetadata] = {}
_listings: dict[uuid.UUID, ListingDetail] = {}
_custom_templates: dict[uuid.UUID, FormattingTemplate] = {}
_exports: dict[uuid.UUID, ExportResponse] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Publishing Accounts
# ---------------------------------------------------------------------------

async def list_accounts(org_id: uuid.UUID) -> list[PublishingAccount]:
    """Return all publishing accounts for an organisation."""
    return [a for a in _accounts.values() if a.org_id == org_id]


async def create_account(
    org_id: uuid.UUID,
    data: PublishingAccountCreate,
) -> PublishingAccount:
    """Connect a new publishing platform account."""
    account = PublishingAccount(
        id=uuid.uuid4(),
        org_id=org_id,
        platform=data.platform,
        account_name=data.account_name,
        account_email=data.account_email,
        is_active=True,
        last_synced_at=None,
        created_at=_now(),
        updated_at=_now(),
    )
    _accounts[account.id] = account
    return account


async def delete_account(account_id: uuid.UUID) -> bool:
    """Disconnect (soft-delete) a publishing account."""
    if account_id in _accounts:
        del _accounts[account_id]
        return True
    return False


# ---------------------------------------------------------------------------
# Export Orchestration
# ---------------------------------------------------------------------------

async def generate_export(
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
    export_id = uuid.uuid4()

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

    response = ExportResponse(
        id=export_id,
        book_id=request.book_id,
        format=request.format,
        status="completed",
        file_url=f"/exports/{export_id}.{fmt_str}",
        file_size_bytes=len(data),
        page_count=None,
        created_at=_now(),
        message=f"{fmt_str.upper()} export completed successfully",
    )
    _exports[export_id] = response
    return response


# ---------------------------------------------------------------------------
# Formatting Templates
# ---------------------------------------------------------------------------

async def list_templates(org_id: uuid.UUID | None = None) -> list[FormattingTemplate]:
    """Return all formatting templates (built-in + custom for org)."""
    builtin = get_all_templates()
    custom = [
        t for t in _custom_templates.values()
        if t.org_id is None or t.org_id == org_id
    ]
    return builtin + custom


async def create_template(
    org_id: uuid.UUID,
    data: FormattingTemplateCreate,
) -> FormattingTemplate:
    """Create a custom formatting template."""
    template = FormattingTemplate(
        id=uuid.uuid4(),
        org_id=org_id,
        name=data.name,
        genre=data.genre,
        description=data.description,
        trim_size=data.trim_size,
        style_settings=data.style_settings,
        is_builtin=False,
        created_at=_now(),
        updated_at=_now(),
    )
    _custom_templates[template.id] = template
    return template


# ---------------------------------------------------------------------------
# Book Metadata
# ---------------------------------------------------------------------------

async def get_metadata(book_id: uuid.UUID) -> BookMetadata | None:
    """Retrieve metadata for a book."""
    return _metadata.get(book_id)


async def update_metadata(
    book_id: uuid.UUID,
    data: BookMetadataUpdate,
) -> BookMetadata:
    """Create or update metadata for a book."""
    existing = _metadata.get(book_id)
    if existing:
        update_dict = data.model_dump(exclude_unset=True)
        merged = existing.model_dump()
        merged.update(update_dict)
        merged["updated_at"] = _now()
        updated = BookMetadata(**merged)
        _metadata[book_id] = updated
        return updated
    else:
        new_meta = BookMetadata(
            book_id=book_id,
            title=data.title or "Untitled",
            subtitle=data.subtitle,
            description=data.description,
            authors=data.authors or [],
            keywords=data.keywords or [],
            categories=data.categories or [],
            language=data.language or "en",
            isbn=data.isbn,
            asin=data.asin,
            publisher=data.publisher,
            publication_date=data.publication_date,
            pricing=data.pricing or PricingInfo(),
            series_name=data.series_name,
            series_number=data.series_number,
            page_count=data.page_count,
            age_range=data.age_range,
            updated_at=_now(),
        )
        _metadata[book_id] = new_meta
        return new_meta


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

async def list_listings(org_id: uuid.UUID) -> list[ListingDetail]:
    """Return all listings across platforms for an organisation."""
    # In production, filter by org_id via DB join
    return list(_listings.values())


async def sync_listing(listing_id: uuid.UUID) -> ListingSyncResponse:
    """Queue a sync job for a specific listing.

    In production this would enqueue a Celery task to fetch data from the
    platform API and update the listing record.
    """
    listing = _listings.get(listing_id)
    if listing:
        listing.last_synced_at = _now()
        listing.status = ListingStatus.LIVE
    return ListingSyncResponse(
        listing_id=listing_id,
        status="sync_queued",
        message="Listing sync has been queued",
    )


# ---------------------------------------------------------------------------
# Internal helpers used by tests
# ---------------------------------------------------------------------------

def _reset_stores() -> None:
    """Clear all in-memory stores. Used by tests."""
    _accounts.clear()
    _metadata.clear()
    _listings.clear()
    _custom_templates.clear()
    _exports.clear()
