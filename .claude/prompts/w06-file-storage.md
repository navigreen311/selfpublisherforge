# W06: File Storage Service (S3/R2)
**Branch:** `ai-feature/file-storage`
**Scope:** api

## Mission
Implement a file storage service for manuscripts, covers, exports, and media assets using S3-compatible storage (AWS S3 / Cloudflare R2).

## What to Build

### Backend
1. **backend/app/modules/storage/__init__.py**
2. **backend/app/modules/storage/router.py** — Endpoints:
   - POST /api/v1/storage/upload — Get presigned upload URL
   - POST /api/v1/storage/upload/complete — Confirm upload, create asset record
   - GET /api/v1/storage/assets — List org assets (paginated, filterable by type)
   - GET /api/v1/storage/assets/{id} — Get asset details + download URL
   - DELETE /api/v1/storage/assets/{id} — Soft-delete asset
   - POST /api/v1/storage/assets/{id}/process — Trigger processing (image resize, PDF parse, etc.)

3. **backend/app/modules/storage/schemas.py** — UploadRequest(file_name, content_type, size), UploadResponse(upload_url, asset_id), AssetResponse
4. **backend/app/modules/storage/service.py** — S3 client wrapper: presigned URLs, upload/download, file validation (size limits per plan, mime type whitelist), asset CRUD
5. **backend/app/modules/storage/validators.py** — File type validation, size limits, malware scan placeholder

### File Type Support
- Manuscripts: .docx, .epub, .pdf, .txt, .rtf (max 50MB)
- Images: .jpg, .png, .tiff, .svg (max 20MB)
- Covers: .jpg, .png, .tiff (min 300 DPI for print)
- Exports: .epub, .pdf, .mobi (generated)

### Tests
6. **backend/tests/unit/test_storage_service.py** — Test presigned URL generation, file validation, size limits
7. **backend/tests/integration/test_storage_api.py** — Test endpoints with mocked S3

## Database Tables Used (read-only, created by W02)
- content_assets (from W02)

## Dependencies
- Uses: backend/app/core/dependencies.py (get_current_user)
- Uses: backend/app/core/exceptions.py (AppException)
- Uses: backend/app/core/pagination.py (paginate)
- External: boto3 (S3-compatible client)

## Read-Only (do NOT modify)
- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- backend/app/core/security.py
- backend/app/core/dependencies.py
- backend/app/core/exceptions.py
- backend/app/core/pagination.py
- backend/app/schemas/common.py
- frontend/src/app/layout.tsx
- frontend/src/components/providers.tsx
- frontend/src/lib/utils.ts
- frontend/src/lib/api.ts
- frontend/src/types/index.ts
- docker-compose.yml, CLAUDE.md, README.md

## Commit Convention
`feat(storage): implement S3/R2 file storage with presigned uploads and asset management`
