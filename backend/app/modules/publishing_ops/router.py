"""FastAPI router for the Publishing Operations Center.

Endpoints (after prefix="/api/v1/publishing" applied by main.py)
---------
GET    /accounts              List connected publishing accounts
POST   /accounts              Connect a publishing account
DELETE /accounts/{id}          Disconnect account
POST   /export/epub           Generate EPUB from manuscript
POST   /export/pdf            Generate print-ready PDF
GET    /templates             List formatting templates
POST   /templates             Create custom template
GET    /listings              List all listings across platforms
POST   /listings/{id}/sync    Sync listing with platform
GET    /isbns                 List all ISBNs
POST   /isbns                 Register a new ISBN
PATCH  /isbns/{id}            Update an ISBN record
DELETE /isbns/{id}            Delete an ISBN record
POST   /isbns/{id}/generate-barcode  Generate barcode for ISBN

Book metadata endpoints are on a separate router registered at "/api/v1":
GET    /books/{id}/metadata   Get book metadata
PATCH  /books/{id}/metadata   Update metadata
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.publishing_ops import service
from app.modules.publishing_ops.schemas import (
    BookMetadata,
    BookMetadataUpdate,
    CreateISBNRequest,
    ExportRequest,
    ExportResponse,
    FormattingTemplate,
    FormattingTemplateCreate,
    GenerateBarcodeRequest,
    ISBNResponse,
    ListingDetail,
    ListingSyncResponse,
    PublishingAccount,
    PublishingAccountCreate,
    UpdateISBNRequest,
)

router = APIRouter(tags=["publishing"])

# Separate router for book-level endpoints that live outside /publishing.
metadata_router = APIRouter(tags=["publishing"])


# ---------- Publishing Accounts ----------

@router.get(
    "/accounts",
    response_model=list[PublishingAccount],
    summary="List publishing accounts",
    description="List all connected publishing platform accounts for the organization.",
)
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all connected publishing platform accounts."""
    org_id = current_user["org_id"]
    return await service.list_accounts(db, org_id)


@router.post(
    "/accounts",
    response_model=PublishingAccount,
    status_code=201,
    summary="Connect publishing account",
    description="Connect a new publishing platform account (KDP, IngramSpark, etc.).",
)
async def create_account(
    data: PublishingAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Connect a new publishing platform account."""
    org_id = current_user["org_id"]
    return await service.create_account(db, org_id, data)


@router.delete(
    "/accounts/{account_id}",
    status_code=204,
    summary="Disconnect publishing account",
    description="Disconnect and remove a publishing platform account.",
)
async def delete_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Disconnect (remove) a publishing account."""
    deleted = await service.delete_account(db, account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
    return


# ---------- Export ----------

@router.post(
    "/export/epub",
    response_model=ExportResponse,
    status_code=201,
    summary="Export EPUB",
    description="Generate an EPUB file from manuscript chapters.",
)
async def export_epub(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate an EPUB file from manuscript chapters."""
    org_id = current_user["org_id"]
    request.format = "epub"  # type: ignore[assignment]
    return await service.generate_export(db, org_id, request)


@router.post(
    "/export/pdf",
    response_model=ExportResponse,
    status_code=201,
    summary="Export print-ready PDF",
    description="Generate a print-ready PDF from manuscript chapters with formatting template.",
)
async def export_pdf(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a print-ready PDF from manuscript chapters."""
    org_id = current_user["org_id"]
    request.format = "pdf"  # type: ignore[assignment]
    return await service.generate_export(db, org_id, request)


# ---------- Formatting Templates ----------

@router.get(
    "/templates",
    response_model=list[FormattingTemplate],
    summary="List formatting templates",
    description="List all available formatting templates (built-in and custom).",
)
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all available formatting templates (built-in + custom)."""
    org_id = current_user["org_id"]
    return await service.list_templates(db, org_id)


@router.post(
    "/templates",
    response_model=FormattingTemplate,
    status_code=201,
    summary="Create formatting template",
    description="Create a new custom formatting template with fonts, margins, and styles.",
)
async def create_template(
    data: FormattingTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new custom formatting template."""
    org_id = current_user["org_id"]
    return await service.create_template(db, org_id, data)


# ---------- Book Metadata (on separate router) ----------

@metadata_router.get(
    "/books/{book_id}/metadata",
    response_model=BookMetadata,
    summary="Get book metadata",
    description="Retrieve metadata (title, description, keywords, categories) for a book.",
)
async def get_metadata(
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve metadata for a specific book."""
    meta = await service.get_metadata(db, book_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Metadata not found for this book")
    return meta


@metadata_router.patch(
    "/books/{book_id}/metadata",
    response_model=BookMetadata,
    summary="Update book metadata",
    description="Create or update metadata for a specific book.",
)
async def update_metadata(
    book_id: uuid.UUID,
    data: BookMetadataUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create or update metadata for a specific book."""
    return await service.update_metadata(db, book_id, data)


# ---------- Listings ----------

@router.get(
    "/listings",
    response_model=list[ListingDetail],
    summary="List book listings",
    description="List all book listings across connected publishing platforms.",
)
async def list_listings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all book listings across connected platforms."""
    org_id = current_user["org_id"]
    return await service.list_listings(db, org_id)


@router.post(
    "/listings/{listing_id}/sync",
    response_model=ListingSyncResponse,
    summary="Sync listing with platform",
    description="Trigger a sync for a specific listing with its publishing platform.",
)
async def sync_listing(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Trigger a sync for a specific listing with its platform."""
    return await service.sync_listing(db, listing_id)


# ---------- ISBNs ----------

@router.get(
    "/isbns",
    response_model=list[ISBNResponse],
    summary="List ISBNs",
    description="List all ISBNs for the organisation.",
)
async def list_isbns(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all ISBNs for the organisation."""
    org_id = current_user["org_id"]
    return await service.list_isbns(db, org_id)


@router.post(
    "/isbns",
    response_model=ISBNResponse,
    status_code=201,
    summary="Create ISBN",
    description="Register a new ISBN for the organisation.",
)
async def create_isbn(
    body: CreateISBNRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Register a new ISBN."""
    org_id = current_user["org_id"]
    return await service.create_isbn(db, org_id, body)


@router.patch(
    "/isbns/{isbn_id}",
    response_model=ISBNResponse,
    summary="Update ISBN",
    description="Update an existing ISBN record.",
)
async def update_isbn(
    isbn_id: uuid.UUID,
    body: UpdateISBNRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update an existing ISBN record."""
    result = await service.update_isbn(db, isbn_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="ISBN not found")
    return result


@router.delete(
    "/isbns/{isbn_id}",
    status_code=204,
    summary="Delete ISBN",
    description="Remove an ISBN record.",
)
async def delete_isbn(
    isbn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete (soft-delete) an ISBN record."""
    deleted = await service.delete_isbn(db, isbn_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="ISBN not found")
    return


@router.post(
    "/isbns/{isbn_id}/generate-barcode",
    summary="Generate ISBN barcode",
    description="Generate a barcode image for a registered ISBN.",
)
async def generate_barcode(
    isbn_id: uuid.UUID,
    body: GenerateBarcodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a barcode image for a registered ISBN."""
    # Return placeholder URL for now
    return {"barcode_url": f"/api/v1/publishing/isbns/{isbn_id}/barcode.png"}
