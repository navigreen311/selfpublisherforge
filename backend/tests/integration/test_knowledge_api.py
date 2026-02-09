"""Integration tests for the Knowledge Vault API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.database import get_db
from app.core.dependencies import get_current_user


# ── Fixtures ─────────────────────────────────────────────────────

TEST_ORG_ID = str(uuid.uuid4())
TEST_USER_ID = str(uuid.uuid4())
TEST_USER = {
    "user_id": uuid.UUID(TEST_USER_ID),
    "org_id": uuid.UUID(TEST_ORG_ID),
    "role": "admin",
}


def _make_mock_entry(**overrides):
    """Create a mock entry ORM object."""
    defaults = {
        "id": uuid.uuid4(),
        "org_id": uuid.UUID(TEST_ORG_ID),
        "title": "Integration Test Entry",
        "content": "Content for integration testing.",
        "source_url": None,
        "source_type": "manual",
        "tags": ["test"],
        "credibility_score": 0.9,
        "metadata_": {"key": "value"},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
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
    return entry, defaults


@pytest.fixture
def app():
    """Create a test FastAPI app with dependency overrides."""
    test_app = create_app()

    # Override auth dependency
    test_app.dependency_overrides[get_current_user] = lambda: TEST_USER

    # Override DB dependency
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def override_get_db():
        yield mock_db

    test_app.dependency_overrides[get_db] = override_get_db

    return test_app


@pytest_asyncio.fixture
async def client(app):
    """Create an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Tests: POST /api/v1/knowledge ────────────────────────────────

@pytest.mark.asyncio
async def test_create_entry_success(client):
    """POST /api/v1/knowledge should create an entry and return 201."""
    mock_entry, defaults = _make_mock_entry()

    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.create_entry",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.return_value = mock_entry

        resp = await client.post(
            "/api/v1/knowledge",
            json={
                "title": "New Research",
                "content": "Research content.",
                "tags": ["research"],
            },
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == defaults["title"]
        assert data["source_type"] == "manual"


@pytest.mark.asyncio
async def test_create_entry_validation_error(client):
    """POST /api/v1/knowledge with empty title should return 422."""
    resp = await client.post(
        "/api/v1/knowledge",
        json={"title": "", "content": "body"},
    )
    assert resp.status_code == 422


# ── Tests: GET /api/v1/knowledge ─────────────────────────────────

@pytest.mark.asyncio
async def test_list_entries_success(client):
    """GET /api/v1/knowledge should return paginated entries."""
    mock_entry, _ = _make_mock_entry()

    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.list_entries",
        new_callable=AsyncMock,
    ) as mock_list:
        mock_list.return_value = {
            "items": [mock_entry],
            "next_cursor": None,
            "has_more": False,
            "total_count": 1,
        }

        resp = await client.get("/api/v1/knowledge")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 1
        assert len(data["items"]) == 1


# ── Tests: GET /api/v1/knowledge/{id} ────────────────────────────

@pytest.mark.asyncio
async def test_get_entry_success(client):
    """GET /api/v1/knowledge/{id} should return the entry."""
    mock_entry, defaults = _make_mock_entry()

    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.get_entry",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = mock_entry

        resp = await client.get(f"/api/v1/knowledge/{defaults['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == defaults["title"]


@pytest.mark.asyncio
async def test_get_entry_not_found(client):
    """GET /api/v1/knowledge/{id} should return 404 for missing entries."""
    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.get_entry",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = None

        resp = await client.get(f"/api/v1/knowledge/{uuid.uuid4()}")
        assert resp.status_code == 404


# ── Tests: PUT /api/v1/knowledge/{id} ────────────────────────────

@pytest.mark.asyncio
async def test_update_entry_success(client):
    """PUT /api/v1/knowledge/{id} should update and return the entry."""
    mock_entry, defaults = _make_mock_entry(title="Updated Title")

    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.update_entry",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_update.return_value = mock_entry

        resp = await client.put(
            f"/api/v1/knowledge/{defaults['id']}",
            json={"title": "Updated Title"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_entry_not_found(client):
    """PUT /api/v1/knowledge/{id} should return 404 for missing entries."""
    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.update_entry",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_update.return_value = None

        resp = await client.put(
            f"/api/v1/knowledge/{uuid.uuid4()}",
            json={"title": "Does Not Matter"},
        )
        assert resp.status_code == 404


# ── Tests: DELETE /api/v1/knowledge/{id} ─────────────────────────

@pytest.mark.asyncio
async def test_delete_entry_success(client):
    """DELETE /api/v1/knowledge/{id} should return 204."""
    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.delete_entry",
        new_callable=AsyncMock,
    ) as mock_delete:
        mock_delete.return_value = True

        resp = await client.delete(f"/api/v1/knowledge/{uuid.uuid4()}")
        assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_entry_not_found(client):
    """DELETE /api/v1/knowledge/{id} should return 404 for missing entries."""
    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.delete_entry",
        new_callable=AsyncMock,
    ) as mock_delete:
        mock_delete.return_value = False

        resp = await client.delete(f"/api/v1/knowledge/{uuid.uuid4()}")
        assert resp.status_code == 404


# ── Tests: POST /api/v1/knowledge/search ─────────────────────────

@pytest.mark.asyncio
async def test_search_entries_success(client):
    """POST /api/v1/knowledge/search should return search results."""
    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.full_text_search",
        new_callable=AsyncMock,
    ) as mock_search:
        mock_search.return_value = {
            "hits": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Found It",
                    "content_snippet": "Snippet text",
                    "source_type": "url",
                    "tags": ["research"],
                    "score": 2.5,
                    "credibility_score": 0.8,
                    "created_at": None,
                }
            ],
            "total": 1,
        }

        resp = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "publishing"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["query"] == "publishing"
        assert len(data["hits"]) == 1


@pytest.mark.asyncio
async def test_search_entries_empty_query(client):
    """POST /api/v1/knowledge/search with empty query should return 422."""
    resp = await client.post(
        "/api/v1/knowledge/search",
        json={"query": ""},
    )
    assert resp.status_code == 422


# ── Tests: POST /api/v1/knowledge/import ─────────────────────────

@pytest.mark.asyncio
async def test_import_from_url_success(client):
    """POST /api/v1/knowledge/import with URL should return 201."""
    mock_entry, _ = _make_mock_entry(source_type="url", source_url="https://example.com")

    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.import_entry",
        new_callable=AsyncMock,
    ) as mock_import:
        mock_import.return_value = mock_entry

        resp = await client.post(
            "/api/v1/knowledge/import",
            json={"url": "https://example.com/article"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "url"


@pytest.mark.asyncio
async def test_import_no_source_returns_400(client):
    """POST /api/v1/knowledge/import with no URL or file returns 400."""
    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.import_entry",
        new_callable=AsyncMock,
    ) as mock_import:
        mock_import.side_effect = ValueError("Provide either a URL or file_name + file_content_base64")

        resp = await client.post(
            "/api/v1/knowledge/import",
            json={},
        )
        assert resp.status_code == 400


# ── Tests: POST /api/v1/knowledge/{id}/summarize ────────────────

@pytest.mark.asyncio
async def test_summarize_entry_success(client):
    """POST /api/v1/knowledge/{id}/summarize should return summary."""
    entry_id = uuid.uuid4()

    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.summarize_entry",
        new_callable=AsyncMock,
    ) as mock_summ:
        mock_summ.return_value = {
            "entry_id": str(entry_id),
            "summary": "A concise summary.",
            "key_points": ["Point 1"],
            "suggested_tags": ["tag1"],
        }

        resp = await client.post(f"/api/v1/knowledge/{entry_id}/summarize")
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"] == "A concise summary."


@pytest.mark.asyncio
async def test_summarize_entry_not_found(client):
    """POST /api/v1/knowledge/{id}/summarize should return 404 for missing entry."""
    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.summarize_entry",
        new_callable=AsyncMock,
    ) as mock_summ:
        mock_summ.return_value = None

        resp = await client.post(f"/api/v1/knowledge/{uuid.uuid4()}/summarize")
        assert resp.status_code == 404


# ── Tests: GET /api/v1/knowledge/tags ────────────────────────────

@pytest.mark.asyncio
async def test_list_tags_success(client):
    """GET /api/v1/knowledge/tags should return tags and counts."""
    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.get_all_tags",
        new_callable=AsyncMock,
    ) as mock_tags:
        mock_tags.return_value = {
            "tags": ["research", "writing"],
            "counts": {"research": 5, "writing": 3},
        }

        resp = await client.get("/api/v1/knowledge/tags")
        assert resp.status_code == 200
        data = resp.json()
        assert "research" in data["tags"]
        assert data["counts"]["research"] == 5


# ── Tests: GET /api/v1/knowledge/suggestions ─────────────────────

@pytest.mark.asyncio
async def test_suggestions_success(client):
    """GET /api/v1/knowledge/suggestions should return AI suggestions."""
    with patch(
        "app.modules.knowledge_vault.service.KnowledgeService.get_suggestions",
        new_callable=AsyncMock,
    ) as mock_sugg:
        mock_sugg.return_value = [
            {
                "topic": "Email Marketing",
                "reason": "Complements existing marketing research",
                "search_query": "email marketing for self-published authors",
            }
        ]

        resp = await client.get("/api/v1/knowledge/suggestions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["topic"] == "Email Marketing"
