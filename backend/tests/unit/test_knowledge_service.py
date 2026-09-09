"""Unit tests for the Knowledge Vault service layer."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.knowledge_vault.schemas import (
    CreateEntryRequest,
    UpdateEntryRequest,
)
from app.modules.knowledge_vault.service import KnowledgeService

# ── Fixtures ─────────────────────────────────────────────────────

def _make_entry(**overrides):
    """Create a mock KnowledgeEntry-like object."""
    defaults = {
        "id": uuid.uuid4(),
        "org_id": uuid.uuid4(),
        "title": "Test Entry",
        "content": "Some research content about self-publishing.",
        "source_url": None,
        "source_type": "manual",
        "tags": ["research", "publishing"],
        "credibility_score": 0.85,
        "metadata_": {},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "deleted_at": None,
    }
    defaults.update(overrides)

    entry = MagicMock()
    for k, v in defaults.items():
        setattr(entry, k, v)

    entry.to_dict.return_value = {
        "id": str(defaults["id"]),
        "org_id": str(defaults["org_id"]),
        "title": defaults["title"],
        "content": defaults["content"],
        "source_url": defaults["source_url"],
        "source_type": defaults["source_type"],
        "tags": defaults["tags"],
        "credibility_score": defaults["credibility_score"],
        "created_at": defaults["created_at"].isoformat() if defaults["created_at"] else None,
        "updated_at": defaults["updated_at"].isoformat() if defaults["updated_at"] else None,
    }
    return entry


@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def mock_db():
    """Return an AsyncMock simulating an AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_search():
    """Return an AsyncMock of KnowledgeSearchService."""
    search = AsyncMock()
    search.index_entry = AsyncMock()
    search.delete_entry = AsyncMock()
    search.search = AsyncMock(return_value={"hits": [], "total": 0})
    return search


@pytest.fixture
def service(mock_db, mock_search):
    return KnowledgeService(db=mock_db, search=mock_search)


# ── Tests: create_entry ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_entry_basic(service, mock_db, mock_search, org_id):
    """Creating an entry should add to DB, flush, and index in ES."""
    payload = CreateEntryRequest(
        title="Research on KDP",
        content="Detailed notes about Kindle Direct Publishing.",
        tags=["kdp", "amazon"],
    )

    # After flush, simulate refresh populating the entry
    mock_db.refresh = AsyncMock(side_effect=lambda e: setattr(e, "id", uuid.uuid4()))

    entry = await service.create_entry(org_id, payload)

    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()
    mock_search.index_entry.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_entry_es_failure_does_not_raise(service, mock_db, mock_search, org_id):
    """If Elasticsearch indexing fails, the create should still succeed."""
    mock_search.index_entry.side_effect = ConnectionError("ES down")
    mock_db.refresh = AsyncMock(side_effect=lambda e: setattr(e, "id", uuid.uuid4()))

    payload = CreateEntryRequest(title="Fallback Test", content="Content")

    # Should not raise
    entry = await service.create_entry(org_id, payload)
    mock_db.add.assert_called_once()


# ── Tests: get_entry ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_entry_found(service, mock_db, org_id):
    """get_entry returns the entry when it exists."""
    expected = _make_entry(org_id=org_id)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await service.get_entry(org_id, expected.id)
    assert result == expected


@pytest.mark.asyncio
async def test_get_entry_not_found(service, mock_db, org_id):
    """get_entry returns None when the entry does not exist."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await service.get_entry(org_id, uuid.uuid4())
    assert result is None


# ── Tests: delete_entry (soft delete) ────────────────────────────

@pytest.mark.asyncio
async def test_delete_entry_sets_deleted_at(service, mock_db, mock_search, org_id):
    """Deleting an entry should set deleted_at and remove from ES index."""
    existing = _make_entry(org_id=org_id, deleted_at=None)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    mock_db.execute = AsyncMock(return_value=mock_result)

    success = await service.delete_entry(org_id, existing.id)
    assert success is True
    assert existing.deleted_at is not None
    mock_search.delete_entry.assert_awaited_once_with(str(existing.id))


@pytest.mark.asyncio
async def test_delete_entry_not_found(service, mock_db, org_id):
    """Deleting a non-existent entry returns False."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    success = await service.delete_entry(org_id, uuid.uuid4())
    assert success is False


# ── Tests: update_entry ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_entry_applies_changes(service, mock_db, mock_search, org_id):
    """Updating an entry should modify fields and re-index."""
    existing = _make_entry(org_id=org_id, title="Old Title")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    mock_db.execute = AsyncMock(return_value=mock_result)

    payload = UpdateEntryRequest(title="New Title")
    result = await service.update_entry(org_id, existing.id, payload)

    assert existing.title == "New Title"
    mock_db.flush.assert_awaited()
    mock_search.index_entry.assert_awaited()


@pytest.mark.asyncio
async def test_update_entry_not_found(service, mock_db, org_id):
    """Updating a non-existent entry returns None."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    payload = UpdateEntryRequest(title="Does Not Matter")
    result = await service.update_entry(org_id, uuid.uuid4(), payload)
    assert result is None


# ── Tests: full_text_search ──────────────────────────────────────

@pytest.mark.asyncio
async def test_full_text_search_delegates_to_es(service, mock_search, org_id):
    """full_text_search should delegate to the search service."""
    mock_search.search.return_value = {
        "hits": [
            {
                "id": str(uuid.uuid4()),
                "title": "Found Entry",
                "content_snippet": "Some snippet",
                "source_type": "manual",
                "tags": ["test"],
                "score": 1.5,
                "credibility_score": 0.9,
                "created_at": None,
            }
        ],
        "total": 1,
    }

    result = await service.full_text_search(org_id, query="publishing", tags=["test"])

    mock_search.search.assert_awaited_once_with(
        org_id=str(org_id),
        query="publishing",
        tags=["test"],
        source_type=None,
        limit=20,
        offset=0,
    )
    assert result["total"] == 1
    assert len(result["hits"]) == 1


# ── Tests: import_entry ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_from_url(service, mock_db, mock_search, org_id):
    """Importing from a URL should extract content and create an entry."""
    mock_db.refresh = AsyncMock(side_effect=lambda e: setattr(e, "id", uuid.uuid4()))

    with patch("app.modules.knowledge_vault.importer.extract_from_url", new_callable=AsyncMock) as mock_extract, \
         patch("app.modules.knowledge_vault.importer.extract_key_facts", new_callable=AsyncMock) as mock_facts:
        mock_extract.return_value = {
            "title": "Great Article",
            "content": "Article body text.",
            "source_url": "https://example.com/article",
            "source_type": "url",
        }
        mock_facts.return_value = {
            "key_facts": "- Fact 1\n- Fact 2",
            "tags": ["writing", "tips"],
            "credibility_score": 0.75,
        }

        entry = await service.import_entry(
            org_id=org_id,
            url="https://example.com/article",
            extract_facts=True,
        )

        mock_extract.assert_awaited_once_with("https://example.com/article")
        mock_facts.assert_awaited_once()
        mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_import_without_source_raises(service, org_id):
    """Importing without URL or file should raise ValueError."""
    with pytest.raises(ValueError, match="Provide either a URL"):
        await service.import_entry(org_id=org_id)


# ── Tests: summarize_entry ───────────────────────────────────────

@pytest.mark.asyncio
async def test_summarize_entry_returns_summary(service, mock_db, org_id):
    """Summarizing an entry should call the AI summarizer."""
    existing = _make_entry(org_id=org_id, content="Long research content about marketing.")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.modules.knowledge_vault.importer.summarize_content", new_callable=AsyncMock) as mock_summ:
        mock_summ.return_value = {
            "summary": "This is about marketing.",
            "key_points": ["Point 1", "Point 2"],
            "suggested_tags": ["marketing"],
        }

        result = await service.summarize_entry(org_id, existing.id)

        assert result is not None
        assert result["summary"] == "This is about marketing."
        assert len(result["key_points"]) == 2


@pytest.mark.asyncio
async def test_summarize_entry_not_found(service, mock_db, org_id):
    """Summarizing a non-existent entry returns None."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await service.summarize_entry(org_id, uuid.uuid4())
    assert result is None


# ── Tests: schemas validation ────────────────────────────────────

def test_create_entry_schema_validates_source_type():
    """CreateEntryRequest should reject invalid source_type."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateEntryRequest(title="Test", source_type="invalid")


def test_create_entry_schema_validates_credibility_range():
    """CreateEntryRequest should reject credibility_score outside 0-1."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateEntryRequest(title="Test", credibility_score=1.5)


def test_create_entry_schema_defaults():
    """CreateEntryRequest should have sensible defaults."""
    req = CreateEntryRequest(title="Test")
    assert req.source_type == "manual"
    assert req.tags == []
    assert req.content == ""
    assert req.credibility_score is None
