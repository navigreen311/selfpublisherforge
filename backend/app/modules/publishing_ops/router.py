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

Book metadata endpoints are on a separate router registered at "/api/v1":
GET    /books/{id}/metadata   Get book metadata
PATCH  /books/{id}/metadata   Update metadata
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.modules.publishing_ops import service
from app.modules.publishing_ops.schemas import (
    BookMetadata,
    BookMetadataUpdate,
    ExportRequest,
    ExportResponse,
    FormattingTemplate,
    FormattingTemplateCreate,
    ListingDetail,
    ListingSyncResponse,
    PublishingAccount,
    PublishingAccountCreate,
)

router = APIRouter(tags=["publishing"])

# Separate router for book-level endpoints that live outside /publishing.
metadata_router = APIRouter(tags=["publishing"])

# A placeholder org_id; in production this comes from auth/session.
_DEFAULT_ORG = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ---------- Publishing Accounts ----------

@router.get("/accounts", response_model=list[PublishingAccount])
async def list_accounts(
    org_id: uuid.UUID = Query(default=_DEFAULT_ORG),
):
    """List all connected publishing platform accounts."""
    return await service.list_accounts(org_id)


@router.post("/accounts", response_model=PublishingAccount, status_code=201)
async def create_account(
    data: PublishingAccountCreate,
    org_id: uuid.UUID = Query(default=_DEFAULT_ORG),
):
    """Connect a new publishing platform account."""
    return await service.create_account(org_id, data)


@router.delete("/accounts/{account_id}", status_code=204)
async def delete_account(account_id: uuid.UUID):
    """Disconnect (remove) a publishing account."""
    deleted = await service.delete_account(account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
    return None


# ---------- Export ----------

@router.post("/export/epub", response_model=ExportResponse, status_code=201)
async def export_epub(
    request: ExportRequest,
    org_id: uuid.UUID = Query(default=_DEFAULT_ORG),
):
    """Generate an EPUB file from manuscript chapters."""
    request.format = "epub"  # type: ignore[assignment]
    return await service.generate_export(org_id, request)


@router.post("/export/pdf", response_model=ExportResponse, status_code=201)
async def export_pdf(
    request: ExportRequest,
    org_id: uuid.UUID = Query(default=_DEFAULT_ORG),
):
    """Generate a print-ready PDF from manuscript chapters."""
    request.format = "pdf"  # type: ignore[assignment]
    return await service.generate_export(org_id, request)


# ---------- Formatting Templates ----------

@router.get("/templates", response_model=list[FormattingTemplate])
async def list_templates(
    org_id: uuid.UUID = Query(default=_DEFAULT_ORG),
):
    """List all available formatting templates (built-in + custom)."""
    return await service.list_templates(org_id)


@router.post("/templates", response_model=FormattingTemplate, status_code=201)
async def create_template(
    data: FormattingTemplateCreate,
    org_id: uuid.UUID = Query(default=_DEFAULT_ORG),
):
    """Create a new custom formatting template."""
    return await service.create_template(org_id, data)


# ---------- Book Metadata (on separate router) ----------

@metadata_router.get("/books/{book_id}/metadata", response_model=BookMetadata)
async def get_metadata(book_id: uuid.UUID):
    """Retrieve metadata for a specific book."""
    meta = await service.get_metadata(book_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Metadata not found for this book")
    return meta


@metadata_router.patch("/books/{book_id}/metadata", response_model=BookMetadata)
async def update_metadata(book_id: uuid.UUID, data: BookMetadataUpdate):
    """Create or update metadata for a specific book."""
    return await service.update_metadata(book_id, data)


# ---------- Listings ----------

@router.get("/listings", response_model=list[ListingDetail])
async def list_listings(
    org_id: uuid.UUID = Query(default=_DEFAULT_ORG),
):
    """List all book listings across connected platforms."""
    return await service.list_listings(org_id)


@router.post("/listings/{listing_id}/sync", response_model=ListingSyncResponse)
async def sync_listing(listing_id: uuid.UUID):
    """Trigger a sync for a specific listing with its platform."""
    return await service.sync_listing(listing_id)
