# W02: Publishing Ops — Full DB Persistence

## Files to modify
- `backend/app/modules/publishing_ops/service.py` — Rewrite for DB
- `backend/app/modules/publishing_ops/router.py` — Add auth + db deps
- `backend/app/modules/publishing_ops/models.py` — NEW: export/template models

## Task

### 1. Create models.py for publishing ops module

The existing DB models in `app/models/publishing.py` already have `PublishingAccount` and `Listing`. For exports and templates, create new models:

```python
# backend/app/modules/publishing_ops/models.py
from app.database import BaseModel, TenantModel
# ... imports

class ExportJob(TenantModel):
    __tablename__ = "export_jobs"
    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # epub, pdf
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    file_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

class FormattingTemplateModel(TenantModel):
    __tablename__ = "formatting_templates"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trim_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    style_settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 2. Rewrite service.py

Remove ALL 5 in-memory dicts (`_accounts`, `_metadata`, `_listings`, `_custom_templates`, `_exports`) and `_reset_stores()`.

Add `db: AsyncSession` as first param to every function.

Use the existing `PublishingAccount` model from `app.models.publishing` for accounts. Use `Listing` model from same file for listings. Use new `ExportJob` and `FormattingTemplateModel` for exports and templates.

For book metadata — use the Book model's existing JSONB fields or the book table directly. The `update_metadata` function should update the Book model's metadata columns.

Convert between Pydantic schemas and ORM objects using model_dump/from_attributes.

### 3. Update router.py

Replace `_DEFAULT_ORG` with proper auth. Add `db: AsyncSession = Depends(get_db)` and `current_user: dict = Depends(get_current_user)` to every endpoint. Extract `org_id = current_user["org_id"]`. Pass `db` to all service calls.

Import from app.database and app.core.dependencies.
