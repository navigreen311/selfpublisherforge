# W11: Storage Service — Implement trigger_processing

## Files to modify
- `backend/app/modules/storage/service.py` — Implement trigger_processing and upload lifecycle

## Context
The storage service manages file uploads to S3. There's likely a `trigger_processing` TODO or placeholder method that should process uploaded files (e.g., generate thumbnails, extract metadata).

## Task

### 1. Read the current storage service

Read `backend/app/modules/storage/service.py` and identify any TODOs, placeholder methods, or incomplete functionality.

### 2. Implement trigger_processing

If a `trigger_processing` or similar placeholder exists, implement it:

```python
async def trigger_processing(
    db: AsyncSession,
    asset_id: uuid.UUID,
    org_id: uuid.UUID,
) -> dict:
    """Process an uploaded file: update status, extract metadata."""
    from app.models.content import ContentAsset

    result = await db.execute(
        select(ContentAsset).where(
            ContentAsset.id == asset_id,
            ContentAsset.org_id == org_id,
        )
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise AppException(status_code=404, code="ASSET_NOT_FOUND", message="Asset not found")

    # Update status to processing
    asset.status = "processing"
    await db.flush()

    # Extract metadata based on content type
    metadata = {}
    if asset.content_type and asset.content_type.startswith("image/"):
        metadata["type"] = "image"
    elif asset.content_type == "application/pdf":
        metadata["type"] = "document"
    elif asset.content_type in ("application/epub+zip",):
        metadata["type"] = "ebook"

    # Mark as completed
    asset.status = "completed"
    await db.flush()
    await db.refresh(asset)

    return {"asset_id": str(asset.id), "status": "completed", "metadata": metadata}
```

### 3. Add upload completion handler

If not already present, add a method that marks an upload as complete and triggers processing:

```python
async def complete_upload(db, asset_id, org_id):
    """Called after S3 upload finishes. Triggers post-processing."""
    # Update status from 'uploading' to 'uploaded'
    # Then trigger_processing
```

### 4. Ensure the router exposes any new endpoints

If you add new service methods, make sure corresponding router endpoints exist.
