"""Integration tests for the Style Cloning API endpoints.

Tests cover the full CRUD lifecycle and analysis pipeline
through the FastAPI router, using in-memory SQLite and mocked auth.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.dependencies import get_current_user
from app.database import Base, get_db

# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them afterwards."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Auth fixtures
# ---------------------------------------------------------------------------

_ORG_A = uuid.uuid4()
_ORG_B = uuid.uuid4()
_USER_A = {"user_id": str(uuid.uuid4()), "org_id": _ORG_A, "role": "admin"}
_USER_B = {"user_id": str(uuid.uuid4()), "org_id": _ORG_B, "role": "admin"}

# Track which user is "current" so org isolation tests can switch
_current_user = dict(_USER_A)


def _set_current_user(user: dict):
    _current_user.clear()
    _current_user.update(user)


def _override_current_user():
    return dict(_current_user)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def fastapi_app():
    """Create a fresh app instance with overridden dependencies."""
    from app.main import create_app

    application = create_app()
    application.dependency_overrides[get_db] = _override_get_db
    application.dependency_overrides[get_current_user] = _override_current_user
    _set_current_user(_USER_A)
    yield application
    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(fastapi_app):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


SAMPLE_TEXT = (
    "The old house stood at the end of the lane. Its walls were weathered "
    "by decades of storms. Paint peeled from the wooden shutters. Ivy crept "
    "up the eastern wall. The garden had grown wild with neglect. Roses "
    "tangled with weeds along the fence. A broken gate hung from rusty "
    "hinges. Inside, dust covered every surface. The floorboards creaked "
    "underfoot. Memories lingered in every room. The kitchen still smelled "
    "faintly of cinnamon. Sunlight filtered through cracked windows. "
    "Shadows danced on the faded wallpaper. An old clock ticked on the "
    "mantle. Time had moved on but the house remained."
)


# ===================================================================
# Profile CRUD tests
# ===================================================================


class TestProfileCRUD:
    @pytest.mark.asyncio
    async def test_create_profile_without_samples(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Test Author", "description": "A test profile", "genre": "Fiction"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Author"
        assert data["status"] == "pending"
        assert data["word_count"] == 0

    @pytest.mark.asyncio
    async def test_create_profile_with_samples(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/style-profiles",
            json={
                "name": "Analyzed Author",
                "sample_texts": [SAMPLE_TEXT],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Analyzed Author"
        assert data["status"] == "ready"
        assert data["word_count"] > 0
        assert data["confidence"] > 0
        assert data["style_card"] is not None

    @pytest.mark.asyncio
    async def test_list_profiles(self, client: AsyncClient):
        # Create two profiles
        await client.post(
            "/api/v1/style-profiles",
            json={"name": "Profile A"},
        )
        await client.post(
            "/api/v1/style-profiles",
            json={"name": "Profile B"},
        )

        response = await client.get("/api/v1/style-profiles")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Get Me"},
        )
        profile_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/style-profiles/{profile_id}",
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Get Me"

    @pytest.mark.asyncio
    async def test_get_nonexistent_profile_returns_404(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/style-profiles/{fake_id}",
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_profile(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Delete Me"},
        )
        profile_id = create_resp.json()["id"]

        delete_resp = await client.delete(
            f"/api/v1/style-profiles/{profile_id}",
        )
        assert delete_resp.status_code == 204

        # Should no longer be found
        get_resp = await client.get(
            f"/api/v1/style-profiles/{profile_id}",
        )
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/v1/style-profiles/{fake_id}",
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_profile_excluded_from_list(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Will Delete"},
        )
        profile_id = create_resp.json()["id"]

        await client.delete(
            f"/api/v1/style-profiles/{profile_id}",
        )

        list_resp = await client.get("/api/v1/style-profiles")
        assert list_resp.json()["total"] == 0


# ===================================================================
# Analysis & fingerprint tests
# ===================================================================


class TestAnalysis:
    @pytest.mark.asyncio
    async def test_analyze_adds_samples(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Incremental"},
        )
        profile_id = create_resp.json()["id"]

        analyze_resp = await client.post(
            f"/api/v1/style-profiles/{profile_id}/analyze",
            json={"sample_texts": [SAMPLE_TEXT]},
        )
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert data["status"] == "ready"
        assert data["word_count"] > 0

    @pytest.mark.asyncio
    async def test_get_fingerprint(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Fingerprinted", "sample_texts": [SAMPLE_TEXT]},
        )
        profile_id = create_resp.json()["id"]

        fp_resp = await client.get(
            f"/api/v1/style-profiles/{profile_id}/fingerprint",
        )
        assert fp_resp.status_code == 200
        data = fp_resp.json()
        assert data["profile_id"] == profile_id
        fp = data["fingerprint"]
        assert "vocabulary" in fp
        assert "sentence" in fp
        assert "paragraph" in fp
        assert "rhetorical" in fp
        assert "dialogue" in fp
        assert "voice_vector" in fp
        assert len(fp["voice_vector"]) >= 200

    @pytest.mark.asyncio
    async def test_fingerprint_not_available_before_analysis(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "No Analysis"},
        )
        profile_id = create_resp.json()["id"]

        fp_resp = await client.get(
            f"/api/v1/style-profiles/{profile_id}/fingerprint",
        )
        assert fp_resp.status_code == 404


# ===================================================================
# Conformity check tests
# ===================================================================


class TestConformityCheckAPI:
    @pytest.mark.asyncio
    async def test_conformity_check_endpoint(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Conformity Test", "sample_texts": [SAMPLE_TEXT]},
        )
        profile_id = create_resp.json()["id"]

        check_resp = await client.post(
            f"/api/v1/style-profiles/{profile_id}/conformity-check",
            json={"text": SAMPLE_TEXT},
        )
        assert check_resp.status_code == 200
        data = check_resp.json()
        assert "overall_score" in data
        assert 0 <= data["overall_score"] <= 100
        assert "vocabulary_score" in data
        assert "sentence_score" in data
        assert "feedback" in data

    @pytest.mark.asyncio
    async def test_conformity_check_on_unanalyzed_profile(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Unanalyzed"},
        )
        profile_id = create_resp.json()["id"]

        check_resp = await client.post(
            f"/api/v1/style-profiles/{profile_id}/conformity-check",
            json={"text": "Some text to check."},
        )
        assert check_resp.status_code == 404


# ===================================================================
# Generate sample tests
# ===================================================================


class TestGenerateSample:
    @pytest.mark.asyncio
    async def test_generate_sample_endpoint(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Sample Gen", "sample_texts": [SAMPLE_TEXT]},
        )
        profile_id = create_resp.json()["id"]

        from app.modules.llm_orchestration.providers.base import LLMResponse

        mock_response = LLMResponse(
            model_id="claude-sonnet-4-5-20250929",
            content="The sunset painted the sky in hues of amber and rose.",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            latency_ms=200.0,
            finish_reason="end_turn",
        )

        with patch("app.modules.style_cloning.router.AnthropicProvider") as MockProvider:
            mock_instance = MockProvider.return_value
            mock_instance.generate = AsyncMock(return_value=mock_response)

            gen_resp = await client.post(
                f"/api/v1/style-profiles/{profile_id}/generate-sample",
                json={"prompt": "Write a paragraph about a sunset.", "max_words": 100},
            )

        assert gen_resp.status_code == 200
        data = gen_resp.json()
        assert "generated_text" in data
        assert data["profile_id"] == profile_id

    @pytest.mark.asyncio
    async def test_generate_sample_unanalyzed_returns_400(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "No Samples"},
        )
        profile_id = create_resp.json()["id"]

        gen_resp = await client.post(
            f"/api/v1/style-profiles/{profile_id}/generate-sample",
            json={"prompt": "Write something"},
        )
        assert gen_resp.status_code == 400


# ===================================================================
# Org isolation tests
# ===================================================================


class TestOrgIsolation:
    @pytest.mark.asyncio
    async def test_profiles_isolated_by_org(self, client: AsyncClient):
        # Create as user A
        _set_current_user(_USER_A)
        await client.post(
            "/api/v1/style-profiles",
            json={"name": "Org A Profile"},
        )

        # Switch to user B - should not see user A's profile
        _set_current_user(_USER_B)
        list_resp = await client.get("/api/v1/style-profiles")
        assert list_resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_cannot_access_other_org_profile(self, client: AsyncClient):
        # Create as user A
        _set_current_user(_USER_A)
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Secret"},
        )
        profile_id = create_resp.json()["id"]

        # Switch to user B
        _set_current_user(_USER_B)
        get_resp = await client.get(
            f"/api/v1/style-profiles/{profile_id}",
        )
        assert get_resp.status_code == 404


# ===================================================================
# Validation tests
# ===================================================================


class TestValidation:
    @pytest.mark.asyncio
    async def test_empty_name_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/style-profiles",
            json={"name": ""},
        )
        assert response.status_code == 422
