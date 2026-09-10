"""Unit tests for the Publishing Operations Center service layer.

These tests mock the database (AsyncSession) to validate the pure
business logic of each service function: account management, export
orchestration, template CRUD, book metadata, and listing sync.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import populate_server_defaults

from app.modules.publishing_ops.schemas import (
    BookMetadata,
    BookMetadataUpdate,
    ChapterInput,
    ExportFormat,
    ExportRequest,
    ExportResponse,
    FormattingTemplate,
    FormattingTemplateCreate,
    ListingDetail,
    ListingSyncResponse,
    PlatformType,
    PricingInfo,
    PublishingAccount,
    PublishingAccountCreate,
    TemplateGenre,
    TemplateStyleSettings,
    TrimSize,
)
from app.modules.publishing_ops.service import (
    create_account,
    create_template,
    delete_account,
    generate_export,
    get_metadata,
    list_accounts,
    list_listings,
    list_templates,
    sync_listing,
    update_metadata,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)


def _make_db() -> AsyncMock:
    """Return an AsyncMock that behaves like an AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock(side_effect=populate_server_defaults)
    db.execute = AsyncMock()
    return db


def _make_account_row(
    *,
    account_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    platform: str = "kdp",
    credentials_encrypted: str = "My KDP",
    status: str = "active",
    deleted_at: datetime | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a PublishingAccountModel ORM row."""
    row = MagicMock()
    row.id = account_id or uuid.uuid4()
    row.org_id = org_id or uuid.uuid4()
    # platform and status are enums with a .value attribute
    row.platform = MagicMock()
    row.platform.value = platform
    row.credentials_encrypted = credentials_encrypted
    row.status = MagicMock()
    row.status.value = status
    row.health_score = None
    row.deleted_at = deleted_at
    row.created_at = _NOW
    row.updated_at = _NOW
    return row


def _make_scalars_result(rows: list) -> MagicMock:
    """Wrap a list of ORM-style mocks so db.execute().scalars().all() works."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    result_mock.scalar_one_or_none.return_value = rows[0] if rows else None
    return result_mock


def _make_listing_row(
    *,
    listing_id: uuid.UUID | None = None,
    book_id: uuid.UUID | None = None,
    publishing_account_id: uuid.UUID | None = None,
    platform_id: str | None = "B0EXAMPLE",
    status: str = "live",
    listing_data: dict | None = None,
    last_synced: datetime | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Listing ORM row."""
    row = MagicMock()
    row.id = listing_id or uuid.uuid4()
    row.book_id = book_id or uuid.uuid4()
    row.publishing_account_id = publishing_account_id or uuid.uuid4()
    row.platform_id = platform_id
    row.status = MagicMock()
    row.status.value = status
    row.listing_data = listing_data or {
        "platform": "kdp",
        "title": "Test Book",
        "listing_url": "https://amazon.com/dp/B0EXAMPLE",
        "current_price": 9.99,
        "current_rank": 1234,
        "reviews_count": 42,
        "rating": 4.5,
        "sync_errors": [],
    }
    row.last_synced = last_synced
    row.created_at = _NOW
    row.updated_at = _NOW
    row.deleted_at = None
    return row


def _make_template_row(
    *,
    template_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    name: str = "Custom Template",
    genre: str = "custom",
    description: str | None = "A custom template",
    trim_size: str = "6x9",
    style_settings: dict | None = None,
    is_builtin: bool = False,
) -> MagicMock:
    """Create a MagicMock that mimics a FormattingTemplateModel ORM row."""
    row = MagicMock()
    row.id = template_id or uuid.uuid4()
    row.org_id = org_id or uuid.uuid4()
    row.name = name
    row.genre = genre
    row.description = description
    row.trim_size = trim_size
    row.style_settings = style_settings
    row.is_builtin = is_builtin
    row.created_at = _NOW
    row.updated_at = _NOW
    row.deleted_at = None
    return row


def _make_book_row(
    *,
    book_id: uuid.UUID | None = None,
    title: str = "Test Book",
    subtitle: str | None = None,
    isbn: str | None = None,
    asin: str | None = None,
    metadata_: dict | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Book ORM row."""
    row = MagicMock()
    row.id = book_id or uuid.uuid4()
    row.title = title
    row.subtitle = subtitle
    row.isbn = isbn
    row.asin = asin
    row.metadata_ = metadata_
    row.deleted_at = None
    row.created_at = _NOW
    row.updated_at = _NOW
    return row


# ===========================================================================
# Publishing Accounts
# ===========================================================================


class TestListAccounts:
    """Tests for list_accounts(db, org_id)."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_accounts(self):
        db = _make_db()
        db.execute.return_value = _make_scalars_result([])

        result = await list_accounts(db, uuid.uuid4())

        assert result == []
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_accounts_for_org(self):
        org_id = uuid.uuid4()
        rows = [
            _make_account_row(org_id=org_id, platform="kdp", credentials_encrypted="KDP Acct"),
            _make_account_row(org_id=org_id, platform="kdp", credentials_encrypted="KDP Acct 2"),
        ]
        db = _make_db()
        db.execute.return_value = _make_scalars_result(rows)

        result = await list_accounts(db, org_id)

        assert len(result) == 2
        assert isinstance(result[0], PublishingAccount)
        assert result[0].account_name == "KDP Acct"
        assert result[1].account_name == "KDP Acct 2"

    @pytest.mark.asyncio
    async def test_active_account_maps_is_active_true(self):
        db = _make_db()
        row = _make_account_row(status="active")
        db.execute.return_value = _make_scalars_result([row])

        result = await list_accounts(db, uuid.uuid4())

        assert result[0].is_active is True

    @pytest.mark.asyncio
    async def test_inactive_account_maps_is_active_false(self):
        db = _make_db()
        row = _make_account_row(status="inactive")
        db.execute.return_value = _make_scalars_result([row])

        result = await list_accounts(db, uuid.uuid4())

        assert result[0].is_active is False


class TestCreateAccount:
    """Tests for create_account(db, org_id, data)."""

    @pytest.mark.asyncio
    async def test_creates_and_returns_account(self):
        db = _make_db()
        org_id = uuid.uuid4()
        data = PublishingAccountCreate(
            platform=PlatformType.KDP,
            account_name="My KDP",
            account_email="test@example.com",
        )

        # After db.refresh, the mock will have attributes set by the service
        # The service reads account.id, account.org_id, account.created_at, account.updated_at
        # from the refreshed model object. We wire up db.add to capture the object
        # and make db.refresh populate the expected attributes.
        captured = {}

        def capture_add(obj):
            captured["obj"] = obj
            # Simulate the DB assigning an id and timestamps
            obj.id = uuid.uuid4()
            obj.org_id = org_id
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.add = capture_add

        result = await create_account(db, org_id, data)

        assert isinstance(result, PublishingAccount)
        assert result.platform == PlatformType.KDP
        assert result.account_name == "My KDP"
        assert result.account_email == "test@example.com"
        assert result.is_active is True
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_persists_account_with_db_add(self):
        db = _make_db()
        org_id = uuid.uuid4()
        added_objects = []
        db.add = lambda obj: added_objects.append(obj)

        data = PublishingAccountCreate(
            platform=PlatformType.KDP,
            account_name="Test Account",
        )

        # Set attributes the service will read after refresh
        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.org_id = org_id
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.refresh = fake_refresh

        await create_account(db, org_id, data)

        assert len(added_objects) == 1
        assert added_objects[0].credentials_encrypted == "Test Account"

    @pytest.mark.asyncio
    async def test_unknown_platform_falls_back_to_kdp(self):
        """If the platform value can't be mapped to PublishingPlatform, fall back to KDP."""
        db = _make_db()
        org_id = uuid.uuid4()

        # Use a valid PlatformType that does NOT exist in DB's PublishingPlatform
        # e.g., "smashwords" is in PlatformType but not in PublishingPlatform
        data = PublishingAccountCreate(
            platform=PlatformType.SMASHWORDS,
            account_name="Smashwords Acct",
        )

        added_objects = []
        db.add = lambda obj: added_objects.append(obj)

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.org_id = org_id
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.refresh = fake_refresh

        result = await create_account(db, org_id, data)

        # The service should still succeed, falling back to KDP for DB storage
        assert isinstance(result, PublishingAccount)
        # But the returned schema should reflect the original platform from the input
        assert result.platform == PlatformType.SMASHWORDS
        # The DB model should have been added with KDP as fallback
        from app.models.publishing import PublishingPlatform

        assert added_objects[0].platform == PublishingPlatform.KDP


class TestDeleteAccount:
    """Tests for delete_account(db, account_id)."""

    @pytest.mark.asyncio
    async def test_soft_deletes_existing_account(self):
        db = _make_db()
        account_id = uuid.uuid4()
        row = _make_account_row(account_id=account_id)
        row.deleted_at = None  # not yet deleted
        db.execute.return_value = _make_scalars_result([row])

        result = await delete_account(db, account_id)

        assert result is True
        # The service should have set deleted_at on the row
        assert row.deleted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_account_not_found(self):
        db = _make_db()
        # scalar_one_or_none returns None
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        result = await delete_account(db, uuid.uuid4())

        assert result is False
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_already_deleted_returns_false(self):
        """If the account is already soft-deleted, the query won't find it."""
        db = _make_db()
        # The WHERE clause filters deleted_at IS NULL, so already-deleted accounts
        # result in scalar_one_or_none returning None.
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        result = await delete_account(db, uuid.uuid4())

        assert result is False


# ===========================================================================
# Export Orchestration
# ===========================================================================


class TestGenerateExport:
    """Tests for generate_export(db, org_id, request, ...).

    The service dispatches Celery tasks for export generation.  When the
    broker is unreachable (i.e. ``.delay()`` raises), it falls back to
    synchronous generation.  We mock the Celery tasks so they always
    raise, exercising the synchronous fallback path.
    """

    _CELERY_EPUB = "app.modules.publishing_ops.service.task_generate_epub"
    _CELERY_PDF = "app.modules.publishing_ops.service.task_generate_pdf"

    @pytest.mark.asyncio
    @patch("app.modules.publishing_ops.service.task_generate_epub")
    async def test_epub_export_returns_completed_response(self, mock_epub_task):
        mock_epub_task.delay.side_effect = RuntimeError("broker unavailable")

        db = _make_db()
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.EPUB,
            chapters=[
                ChapterInput(title="Chapter 1", content="Hello world", order=1),
            ],
        )

        # After db.add + refresh, the ExportJob will need id, created_at, etc.
        export_id = uuid.uuid4()

        def capture_add(obj):
            obj.id = export_id
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.add = capture_add

        result = await generate_export(db, org_id, request, title="Test Book")

        assert isinstance(result, ExportResponse)
        assert result.book_id == book_id
        assert result.format == ExportFormat.EPUB
        assert result.status == "completed"
        assert result.file_url is not None
        assert result.file_url.endswith(".epub")
        assert result.file_size_bytes is not None
        assert result.file_size_bytes > 0

    @pytest.mark.asyncio
    @patch("app.modules.publishing_ops.service.task_generate_pdf")
    async def test_pdf_export_returns_completed_response(self, mock_pdf_task):
        mock_pdf_task.delay.side_effect = RuntimeError("broker unavailable")

        db = _make_db()
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=[
                ChapterInput(title="Intro", content="Welcome to the book.", order=1),
            ],
            trim_size=TrimSize.SIZE_6x9,
        )

        def capture_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.add = capture_add

        result = await generate_export(db, org_id, request, title="PDF Book")

        assert isinstance(result, ExportResponse)
        assert result.format == ExportFormat.PDF
        assert result.status == "completed"
        assert result.file_size_bytes > 0

    @pytest.mark.asyncio
    @patch("app.modules.publishing_ops.service.task_generate_epub")
    async def test_export_with_empty_chapters(self, mock_epub_task):
        mock_epub_task.delay.side_effect = RuntimeError("broker unavailable")

        db = _make_db()
        org_id = uuid.uuid4()

        request = ExportRequest(
            book_id=uuid.uuid4(),
            format=ExportFormat.EPUB,
            chapters=[],
        )

        def capture_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.add = capture_add

        result = await generate_export(db, org_id, request)

        assert result.status == "completed"
        # Even with no chapters, the EPUB structure is created
        assert result.file_size_bytes > 0

    @pytest.mark.asyncio
    @patch("app.modules.publishing_ops.service.task_generate_epub")
    async def test_export_persists_job_record(self, mock_epub_task):
        mock_epub_task.delay.side_effect = RuntimeError("broker unavailable")

        db = _make_db()
        org_id = uuid.uuid4()
        book_id = uuid.uuid4()

        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.EPUB,
            chapters=[ChapterInput(title="Ch1", content="Text", order=1)],
        )

        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)
            obj.id = uuid.uuid4()
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.add = capture_add

        await generate_export(db, org_id, request)

        assert len(added_objects) == 1
        job = added_objects[0]
        assert job.org_id == org_id
        assert job.book_id == book_id
        assert job.format == "epub"
        assert job.status == "completed"
        # The fallback path calls flush/refresh twice (initial persist + post-generation update)
        assert db.flush.await_count == 2
        assert db.refresh.await_count == 2

    @pytest.mark.asyncio
    @patch("app.modules.publishing_ops.service.task_generate_pdf")
    async def test_export_message_includes_format(self, mock_pdf_task):
        mock_pdf_task.delay.side_effect = RuntimeError("broker unavailable")

        db = _make_db()

        request = ExportRequest(
            book_id=uuid.uuid4(),
            format=ExportFormat.PDF,
            chapters=[ChapterInput(title="Ch", content="Body", order=1)],
        )

        def capture_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.add = capture_add

        result = await generate_export(db, uuid.uuid4(), request)

        assert "PDF" in result.message.upper()


# ===========================================================================
# Formatting Templates
# ===========================================================================


class TestListTemplates:
    """Tests for list_templates(db, org_id)."""

    @pytest.mark.asyncio
    async def test_returns_builtin_templates_when_no_custom(self):
        db = _make_db()
        db.execute.return_value = _make_scalars_result([])

        result = await list_templates(db, uuid.uuid4())

        # Should contain all built-in templates (8 genres)
        assert len(result) >= 8
        genres = {t.genre for t in result}
        assert TemplateGenre.ROMANCE in genres
        assert TemplateGenre.THRILLER in genres
        assert TemplateGenre.NONFICTION in genres
        assert all(t.is_builtin for t in result)

    @pytest.mark.asyncio
    async def test_includes_custom_templates_from_db(self):
        db = _make_db()
        org_id = uuid.uuid4()
        custom_row = _make_template_row(org_id=org_id, name="My Custom")
        db.execute.return_value = _make_scalars_result([custom_row])

        result = await list_templates(db, org_id)

        # Should include built-in + 1 custom
        names = [t.name for t in result]
        assert "My Custom" in names
        # Verify the custom one is not builtin
        custom = next(t for t in result if t.name == "My Custom")
        assert custom.is_builtin is False

    @pytest.mark.asyncio
    async def test_list_templates_without_org_id(self):
        """When org_id is None, should still return builtins + all custom."""
        db = _make_db()
        db.execute.return_value = _make_scalars_result([])

        result = await list_templates(db, org_id=None)

        assert len(result) >= 8


class TestCreateTemplate:
    """Tests for create_template(db, org_id, data)."""

    @pytest.mark.asyncio
    async def test_creates_custom_template(self):
        db = _make_db()
        org_id = uuid.uuid4()

        data = FormattingTemplateCreate(
            name="Sci-Fi Custom",
            genre=TemplateGenre.SCIFI,
            description="A custom sci-fi template",
            trim_size=TrimSize.SIZE_6x9,
            style_settings=TemplateStyleSettings(font_family="Courier"),
        )

        template_id = uuid.uuid4()

        def capture_add(obj):
            obj.id = template_id
            obj.org_id = org_id
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.add = capture_add

        result = await create_template(db, org_id, data)

        assert isinstance(result, FormattingTemplate)
        assert result.name == "Sci-Fi Custom"
        assert result.genre == TemplateGenre.SCIFI
        assert result.is_builtin is False
        assert result.style_settings.font_family == "Courier"
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_template_persists_with_db_add(self):
        db = _make_db()
        org_id = uuid.uuid4()
        added = []
        db.add = lambda obj: added.append(obj)

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.org_id = org_id
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.refresh = fake_refresh

        data = FormattingTemplateCreate(
            name="Test Template",
            genre=TemplateGenre.CUSTOM,
        )

        await create_template(db, org_id, data)

        assert len(added) == 1
        assert added[0].name == "Test Template"
        assert added[0].is_builtin is False

    @pytest.mark.asyncio
    async def test_style_settings_serialized_to_dict(self):
        """Verify that style_settings is stored as a dict (for JSONB)."""
        db = _make_db()
        org_id = uuid.uuid4()
        added = []
        db.add = lambda obj: added.append(obj)

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.org_id = org_id
            obj.created_at = _NOW
            obj.updated_at = _NOW

        db.refresh = fake_refresh

        data = FormattingTemplateCreate(
            name="With Style",
            genre=TemplateGenre.ROMANCE,
            style_settings=TemplateStyleSettings(
                font_family="Garamond",
                drop_cap=True,
            ),
        )

        await create_template(db, org_id, data)

        stored_settings = added[0].style_settings
        assert isinstance(stored_settings, dict)
        assert stored_settings["font_family"] == "Garamond"
        assert stored_settings["drop_cap"] is True


# ===========================================================================
# Book Metadata
# ===========================================================================


class TestGetMetadata:
    """Tests for get_metadata(db, book_id)."""

    @pytest.mark.asyncio
    async def test_returns_none_when_book_not_found(self):
        db = _make_db()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        result = await get_metadata(db, uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_metadata_from_book(self):
        db = _make_db()
        book_id = uuid.uuid4()
        book = _make_book_row(
            book_id=book_id,
            title="Great Novel",
            subtitle="A Subtitle",
            isbn="978-0-123456-47-2",
            metadata_={
                "title": "Great Novel",
                "subtitle": "A Subtitle",
                "authors": ["Author One"],
                "keywords": ["fiction", "drama"],
                "categories": ["Fiction > Literary"],
                "language": "en",
                "description": "A great story",
            },
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = book
        db.execute.return_value = result_mock

        result = await get_metadata(db, book_id)

        assert isinstance(result, BookMetadata)
        assert result.book_id == book_id
        assert result.title == "Great Novel"
        assert result.authors == ["Author One"]
        assert result.keywords == ["fiction", "drama"]
        assert result.isbn == "978-0-123456-47-2"

    @pytest.mark.asyncio
    async def test_returns_defaults_when_metadata_is_none(self):
        """When book.metadata_ is None, should still return BookMetadata with defaults."""
        db = _make_db()
        book_id = uuid.uuid4()
        book = _make_book_row(book_id=book_id, title="Bare Book", metadata_=None)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = book
        db.execute.return_value = result_mock

        result = await get_metadata(db, book_id)

        assert result is not None
        assert result.title == "Bare Book"
        assert result.authors == []
        assert result.language == "en"
        assert result.pricing.currency == "USD"
        assert result.pricing.list_price == 0.0

    @pytest.mark.asyncio
    async def test_returns_pricing_from_metadata(self):
        db = _make_db()
        book_id = uuid.uuid4()
        book = _make_book_row(
            book_id=book_id,
            title="Priced Book",
            metadata_={
                "title": "Priced Book",
                "pricing": {"currency": "GBP", "list_price": 12.99, "sale_price": 6.99},
            },
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = book
        db.execute.return_value = result_mock

        result = await get_metadata(db, book_id)

        assert result.pricing.currency == "GBP"
        assert result.pricing.list_price == 12.99
        assert result.pricing.sale_price == 6.99


class TestUpdateMetadata:
    """Tests for update_metadata(db, book_id, data)."""

    @pytest.mark.asyncio
    async def test_raises_404_when_book_not_found(self):
        from fastapi import HTTPException

        db = _make_db()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        data = BookMetadataUpdate(title="Updated Title")

        with pytest.raises(HTTPException) as exc_info:
            await update_metadata(db, uuid.uuid4(), data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_updates_existing_metadata(self):
        db = _make_db()
        book_id = uuid.uuid4()
        book = _make_book_row(
            book_id=book_id,
            title="Original Title",
            metadata_={"title": "Original Title", "description": "Old desc"},
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = book
        db.execute.return_value = result_mock

        data = BookMetadataUpdate(description="New description")

        result = await update_metadata(db, book_id, data)

        assert isinstance(result, BookMetadata)
        # Original title should be preserved
        assert result.title == "Original Title"
        # Description should be updated
        assert book.metadata_["description"] == "New description"
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_updates_top_level_book_columns(self):
        """When title, subtitle, isbn, asin are updated, they should also
        be written to the top-level Book model columns."""
        db = _make_db()
        book_id = uuid.uuid4()
        book = _make_book_row(
            book_id=book_id,
            title="Old Title",
            metadata_={"title": "Old Title"},
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = book
        db.execute.return_value = result_mock

        data = BookMetadataUpdate(
            title="New Title",
            isbn="978-1-234567-89-0",
            asin="B0NEWASIN",
        )

        await update_metadata(db, book_id, data)

        assert book.title == "New Title"
        assert book.isbn == "978-1-234567-89-0"
        assert book.asin == "B0NEWASIN"

    @pytest.mark.asyncio
    async def test_creates_metadata_when_none_exists(self):
        """When book.metadata_ is None, update should create it from scratch."""
        db = _make_db()
        book_id = uuid.uuid4()
        book = _make_book_row(book_id=book_id, title="No Meta", metadata_=None)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = book
        db.execute.return_value = result_mock

        data = BookMetadataUpdate(
            title="New Title",
            authors=["Author A"],
        )

        result = await update_metadata(db, book_id, data)

        assert result.title == "New Title"
        assert book.metadata_ is not None
        assert "authors" in book.metadata_

    @pytest.mark.asyncio
    async def test_pricing_update_serialized_correctly(self):
        db = _make_db()
        book_id = uuid.uuid4()
        book = _make_book_row(
            book_id=book_id,
            title="Priced",
            metadata_={"title": "Priced"},
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = book
        db.execute.return_value = result_mock

        data = BookMetadataUpdate(
            pricing=PricingInfo(currency="EUR", list_price=14.99, sale_price=9.99),
        )

        result = await update_metadata(db, book_id, data)

        # The pricing should be stored as a dict in metadata_
        stored_pricing = book.metadata_["pricing"]
        assert isinstance(stored_pricing, dict)
        assert stored_pricing["currency"] == "EUR"
        assert stored_pricing["list_price"] == 14.99


# ===========================================================================
# Listings
# ===========================================================================


class TestListListings:
    """Tests for list_listings(db, org_id)."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_listings(self):
        db = _make_db()
        db.execute.return_value = _make_scalars_result([])

        result = await list_listings(db, uuid.uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_listings_with_details(self):
        db = _make_db()
        org_id = uuid.uuid4()
        row = _make_listing_row()
        db.execute.return_value = _make_scalars_result([row])

        result = await list_listings(db, org_id)

        assert len(result) == 1
        listing = result[0]
        assert isinstance(listing, ListingDetail)
        assert listing.title == "Test Book"
        assert listing.current_price == 9.99
        assert listing.current_rank == 1234
        assert listing.reviews_count == 42
        assert listing.rating == 4.5

    @pytest.mark.asyncio
    async def test_listing_with_minimal_listing_data(self):
        """When listing_data has only a platform and no extra fields, defaults apply."""
        db = _make_db()
        row = _make_listing_row(listing_data={"platform": "kdp"})
        db.execute.return_value = _make_scalars_result([row])

        result = await list_listings(db, uuid.uuid4())

        listing = result[0]
        assert listing.title is None
        assert listing.current_price is None
        assert listing.sync_errors == []

    @pytest.mark.asyncio
    async def test_multiple_listings_returned(self):
        db = _make_db()
        rows = [
            _make_listing_row(listing_data={"platform": "kdp", "title": "Book A"}),
            _make_listing_row(listing_data={"platform": "kobo", "title": "Book B"}),
        ]
        db.execute.return_value = _make_scalars_result(rows)

        result = await list_listings(db, uuid.uuid4())

        assert len(result) == 2
        titles = [l.title for l in result]
        assert "Book A" in titles
        assert "Book B" in titles


class TestSyncListing:
    """Tests for sync_listing(db, listing_id).

    The service dispatches a Celery task for listing sync.  When the
    broker is unreachable, it falls back to inline sync.  We mock the
    Celery task so it raises, exercising the inline fallback path.
    """

    @pytest.mark.asyncio
    @patch("app.modules.publishing_ops.service.celery_sync_listing")
    async def test_returns_sync_queued_response(self, mock_sync_task):
        mock_sync_task.delay.side_effect = RuntimeError("broker unavailable")

        db = _make_db()
        listing_id = uuid.uuid4()
        row = _make_listing_row(listing_id=listing_id)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = row
        db.execute.return_value = result_mock

        result = await sync_listing(db, listing_id)

        assert isinstance(result, ListingSyncResponse)
        assert result.listing_id == listing_id
        assert result.status == "sync_queued"

    @pytest.mark.asyncio
    @patch("app.modules.publishing_ops.service.celery_sync_listing")
    async def test_updates_last_synced_and_status(self, mock_sync_task):
        mock_sync_task.delay.side_effect = RuntimeError("broker unavailable")

        db = _make_db()
        listing_id = uuid.uuid4()
        row = _make_listing_row(listing_id=listing_id, status="draft")
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = row
        db.execute.return_value = result_mock

        await sync_listing(db, listing_id)

        # The fallback path should update last_synced and status
        assert row.last_synced is not None
        from app.models.publishing import ListingStatus as ListingStatusEnum

        assert row.status == ListingStatusEnum.LIVE
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sync_nonexistent_listing_still_returns_response(self):
        """When the listing is not found, the service returns a not_found
        response without dispatching any task or flushing."""
        db = _make_db()
        listing_id = uuid.uuid4()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        result = await sync_listing(db, listing_id)

        assert isinstance(result, ListingSyncResponse)
        assert result.listing_id == listing_id
        assert result.status == "not_found"
        # No flush should happen since there was nothing to update
        db.flush.assert_not_awaited()
