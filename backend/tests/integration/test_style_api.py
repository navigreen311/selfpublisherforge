"""Integration tests for the Style Cloning API endpoints.

Tests cover the full CRUD lifecycle and analysis pipeline
through the FastAPI router.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.modules.style_cloning import service as style_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def fastapi_app():
    """Create a fresh app instance with the style-cloning router registered."""
    from app.modules.style_cloning.router import router
    from app.config import get_settings

    application = create_app()
    settings = get_settings()
    prefix = f"{settings.API_V1_PREFIX}/style-profiles"
    application.include_router(router, prefix=prefix, tags=["style-cloning"])

    # Reset the in-memory store before each test
    style_service._reset_store()

    yield application


@pytest_asyncio.fixture
async def client(fastapi_app):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def org_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def headers(org_id: str) -> dict[str, str]:
    return {"X-Org-Id": org_id}


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
    async def test_create_profile_without_samples(self, client: AsyncClient, headers: dict):
        response = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Test Author", "description": "A test profile", "genre": "Fiction"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Author"
        assert data["status"] == "pending"
        assert data["word_count"] == 0

    @pytest.mark.asyncio
    async def test_create_profile_with_samples(self, client: AsyncClient, headers: dict):
        response = await client.post(
            "/api/v1/style-profiles",
            json={
                "name": "Analyzed Author",
                "sample_texts": [SAMPLE_TEXT],
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Analyzed Author"
        assert data["status"] == "ready"
        assert data["word_count"] > 0
        assert data["confidence"] > 0
        assert data["style_card"] is not None

    @pytest.mark.asyncio
    async def test_list_profiles(self, client: AsyncClient, headers: dict):
        # Create two profiles
        await client.post(
            "/api/v1/style-profiles",
            json={"name": "Profile A"},
            headers=headers,
        )
        await client.post(
            "/api/v1/style-profiles",
            json={"name": "Profile B"},
            headers=headers,
        )

        response = await client.get("/api/v1/style-profiles", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient, headers: dict):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Get Me"},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/style-profiles/{profile_id}",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Get Me"

    @pytest.mark.asyncio
    async def test_get_nonexistent_profile_returns_404(self, client: AsyncClient, headers: dict):
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/style-profiles/{fake_id}",
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_profile(self, client: AsyncClient, headers: dict):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Delete Me"},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        delete_resp = await client.delete(
            f"/api/v1/style-profiles/{profile_id}",
            headers=headers,
        )
        assert delete_resp.status_code == 204

        # Should no longer be found
        get_resp = await client.get(
            f"/api/v1/style-profiles/{profile_id}",
            headers=headers,
        )
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, client: AsyncClient, headers: dict):
        fake_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/v1/style-profiles/{fake_id}",
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_profile_excluded_from_list(self, client: AsyncClient, headers: dict):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Will Delete"},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        await client.delete(
            f"/api/v1/style-profiles/{profile_id}",
            headers=headers,
        )

        list_resp = await client.get("/api/v1/style-profiles", headers=headers)
        assert list_resp.json()["total"] == 0


# ===================================================================
# Analysis & fingerprint tests
# ===================================================================

class TestAnalysis:

    @pytest.mark.asyncio
    async def test_analyze_adds_samples(self, client: AsyncClient, headers: dict):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Incremental"},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        analyze_resp = await client.post(
            f"/api/v1/style-profiles/{profile_id}/analyze",
            json={"sample_texts": [SAMPLE_TEXT]},
            headers=headers,
        )
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert data["status"] == "ready"
        assert data["word_count"] > 0

    @pytest.mark.asyncio
    async def test_get_fingerprint(self, client: AsyncClient, headers: dict):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Fingerprinted", "sample_texts": [SAMPLE_TEXT]},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        fp_resp = await client.get(
            f"/api/v1/style-profiles/{profile_id}/fingerprint",
            headers=headers,
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
    async def test_fingerprint_not_available_before_analysis(
        self, client: AsyncClient, headers: dict
    ):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "No Analysis"},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        fp_resp = await client.get(
            f"/api/v1/style-profiles/{profile_id}/fingerprint",
            headers=headers,
        )
        assert fp_resp.status_code == 404


# ===================================================================
# Conformity check tests
# ===================================================================

class TestConformityCheckAPI:

    @pytest.mark.asyncio
    async def test_conformity_check_endpoint(self, client: AsyncClient, headers: dict):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Conformity Test", "sample_texts": [SAMPLE_TEXT]},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        check_resp = await client.post(
            f"/api/v1/style-profiles/{profile_id}/conformity-check",
            json={"text": SAMPLE_TEXT},
            headers=headers,
        )
        assert check_resp.status_code == 200
        data = check_resp.json()
        assert "overall_score" in data
        assert 0 <= data["overall_score"] <= 100
        assert "vocabulary_score" in data
        assert "sentence_score" in data
        assert "feedback" in data

    @pytest.mark.asyncio
    async def test_conformity_check_on_unanalyzed_profile(
        self, client: AsyncClient, headers: dict
    ):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Unanalyzed"},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        check_resp = await client.post(
            f"/api/v1/style-profiles/{profile_id}/conformity-check",
            json={"text": "Some text to check."},
            headers=headers,
        )
        assert check_resp.status_code == 404


# ===================================================================
# Generate sample tests
# ===================================================================

class TestGenerateSample:

    @pytest.mark.asyncio
    async def test_generate_sample_endpoint(self, client: AsyncClient, headers: dict):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Sample Gen", "sample_texts": [SAMPLE_TEXT]},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        gen_resp = await client.post(
            f"/api/v1/style-profiles/{profile_id}/generate-sample",
            json={"prompt": "Write a paragraph about a sunset.", "max_words": 100},
            headers=headers,
        )
        assert gen_resp.status_code == 200
        data = gen_resp.json()
        assert "generated_text" in data
        assert data["profile_id"] == profile_id

    @pytest.mark.asyncio
    async def test_generate_sample_unanalyzed_returns_400(
        self, client: AsyncClient, headers: dict
    ):
        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "No Samples"},
            headers=headers,
        )
        profile_id = create_resp.json()["id"]

        gen_resp = await client.post(
            f"/api/v1/style-profiles/{profile_id}/generate-sample",
            json={"prompt": "Write something"},
            headers=headers,
        )
        assert gen_resp.status_code == 400


# ===================================================================
# Org isolation tests
# ===================================================================

class TestOrgIsolation:

    @pytest.mark.asyncio
    async def test_profiles_isolated_by_org(self, client: AsyncClient):
        org_a = str(uuid.uuid4())
        org_b = str(uuid.uuid4())

        await client.post(
            "/api/v1/style-profiles",
            json={"name": "Org A Profile"},
            headers={"X-Org-Id": org_a},
        )

        # Org B should not see Org A's profile
        list_resp = await client.get(
            "/api/v1/style-profiles",
            headers={"X-Org-Id": org_b},
        )
        assert list_resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_cannot_access_other_org_profile(self, client: AsyncClient):
        org_a = str(uuid.uuid4())
        org_b = str(uuid.uuid4())

        create_resp = await client.post(
            "/api/v1/style-profiles",
            json={"name": "Secret"},
            headers={"X-Org-Id": org_a},
        )
        profile_id = create_resp.json()["id"]

        get_resp = await client.get(
            f"/api/v1/style-profiles/{profile_id}",
            headers={"X-Org-Id": org_b},
        )
        assert get_resp.status_code == 404


# ===================================================================
# Validation tests
# ===================================================================

class TestValidation:

    @pytest.mark.asyncio
    async def test_missing_org_header_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/style-profiles",
            json={"name": "No Org"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_name_returns_422(self, client: AsyncClient, headers: dict):
        response = await client.post(
            "/api/v1/style-profiles",
            json={"name": ""},
            headers=headers,
        )
        assert response.status_code == 422
