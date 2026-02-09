# W19: Publishing Operations Center (Module #6)
**Branch:** `ai-feature/publishing-ops`
**Scope:** fullstack

## Mission
Build the Publishing Operations Center: KDP formatting templates, EPUB/PDF export, metadata editor, ISBN management, multi-platform listing management.

## API Endpoints
- GET /api/v1/publishing/accounts — List connected publishing accounts
- POST /api/v1/publishing/accounts — Connect a publishing account
- DELETE /api/v1/publishing/accounts/{id} — Disconnect account
- POST /api/v1/publishing/export/epub — Generate EPUB from manuscript
- POST /api/v1/publishing/export/pdf — Generate print-ready PDF
- GET /api/v1/publishing/templates — List formatting templates
- POST /api/v1/publishing/templates — Create custom template
- GET /api/v1/books/{id}/metadata — Get book metadata
- PATCH /api/v1/books/{id}/metadata — Update metadata (title, subtitle, description, keywords, categories, pricing)
- GET /api/v1/publishing/listings — List all listings across platforms
- POST /api/v1/publishing/listings/{id}/sync — Sync listing with platform

## What to Build

### Backend
1. **backend/app/modules/publishing_ops/__init__.py**
2. **backend/app/modules/publishing_ops/router.py** — All endpoints
3. **backend/app/modules/publishing_ops/schemas.py** — PublishingAccount, ExportRequest, ExportResponse, FormattingTemplate, BookMetadata, ListingDetail
4. **backend/app/modules/publishing_ops/service.py** — Account management, export orchestration, metadata CRUD, listing sync
5. **backend/app/modules/publishing_ops/epub_generator.py** — Generate EPUB from chapters: TOC, metadata injection, image embedding, style application
6. **backend/app/modules/publishing_ops/pdf_generator.py** — Generate print-ready PDF: trim sizes (6x9, 5.5x8.5, etc.), margins, headers/footers, ISBN barcode
7. **backend/app/modules/publishing_ops/templates.py** — Built-in formatting templates (romance, thriller, nonfiction, children's, etc.)
8. **backend/app/tasks/publishing_ops.py** — Celery: async export generation, listing sync

### Frontend
9. **frontend/src/app/(dashboard)/publishing/page.tsx** — Publishing dashboard: accounts, listings, recent exports
10. **frontend/src/app/(dashboard)/publishing/export/page.tsx** — Export wizard: format selection, template, preview, generate
11. **frontend/src/app/(dashboard)/publishing/metadata/[bookId]/page.tsx** — Metadata editor form
12. **frontend/src/modules/publishing/hooks.ts** — React Query hooks
13. **frontend/src/modules/publishing/components/** — AccountCard, ExportWizard, MetadataForm, ListingTable

### Tests
14. **backend/tests/unit/test_epub_generator.py** — Test EPUB generation
15. **backend/tests/integration/test_publishing_api.py**

## Database Tables (from W02, read-only)
publishing_accounts, listings

## Commit Convention
`feat(publishing): implement publishing operations with EPUB/PDF export and listing management`
