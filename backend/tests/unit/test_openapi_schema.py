"""Unit tests for custom OpenAPI schema generation.

Validates:
- custom_openapi_schema returns a valid OpenAPI dict
- Schema includes the BearerAuth security scheme
- Schema includes all expected tag metadata
- Schema includes correct API info (title, version, description)
- Schema caching behaviour
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from app.core.openapi import (
    _SECURITY_SCHEMES,
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    TAGS_METADATA,
    custom_openapi_schema,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app() -> FastAPI:
    """Create a minimal FastAPI app for schema generation."""
    app = FastAPI()

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok"}

    @app.get("/api/v1/example", tags=["auth"])
    async def example():
        return {"data": "test"}

    return app


# =========================================================================
# API metadata constants
# =========================================================================

class TestAPIMetadataConstants:

    def test_api_title(self):
        assert API_TITLE == "SelfPublisherForge API"

    def test_api_version(self):
        assert API_VERSION == "1.0.0"

    def test_api_description_non_empty(self):
        assert len(API_DESCRIPTION) > 100  # substantial description

    def test_api_description_mentions_selfpublisherforge(self):
        assert "SelfPublisherForge" in API_DESCRIPTION

    def test_api_description_mentions_authentication(self):
        assert "Authentication" in API_DESCRIPTION or "Bearer" in API_DESCRIPTION


# =========================================================================
# Tags metadata
# =========================================================================

class TestTagsMetadata:

    EXPECTED_TAGS = [
        "health",
        "auth",
        "users",
        "billing",
        "storage",
        "notifications",
        "realtime",
        "llm",
        "market",
        "knowledge",
        "writing",
        "style",
        "pipelines",
        "publishing",
        "kdp-validation",
        "product-page",
        "pricing",
        "competitors",
        "marketing",
        "advertising",
        "reviews",
        "analytics",
        "agents",
        "portfolio",
        "audience",
        "seasonal",
        "covers",
        "chrome-extension",
    ]

    def test_tags_metadata_is_list(self):
        assert isinstance(TAGS_METADATA, list)

    def test_tags_metadata_non_empty(self):
        assert len(TAGS_METADATA) > 0

    def test_all_entries_have_name(self):
        for tag in TAGS_METADATA:
            assert "name" in tag, f"Tag entry missing 'name': {tag}"

    def test_all_entries_have_description(self):
        for tag in TAGS_METADATA:
            assert "description" in tag, f"Tag {tag.get('name', '?')} missing 'description'"
            assert len(tag["description"]) > 0

    @pytest.mark.parametrize("tag_name", EXPECTED_TAGS)
    def test_expected_tag_present(self, tag_name: str):
        tag_names = [t["name"] for t in TAGS_METADATA]
        assert tag_name in tag_names, f"Expected tag '{tag_name}' not found in TAGS_METADATA"

    def test_no_duplicate_tag_names(self):
        names = [t["name"] for t in TAGS_METADATA]
        assert len(names) == len(set(names)), "Duplicate tag names found"


# =========================================================================
# Security schemes
# =========================================================================

class TestSecuritySchemes:

    def test_bearer_auth_exists(self):
        assert "BearerAuth" in _SECURITY_SCHEMES

    def test_bearer_auth_type(self):
        assert _SECURITY_SCHEMES["BearerAuth"]["type"] == "http"

    def test_bearer_auth_scheme(self):
        assert _SECURITY_SCHEMES["BearerAuth"]["scheme"] == "bearer"

    def test_bearer_auth_format(self):
        assert _SECURITY_SCHEMES["BearerAuth"]["bearerFormat"] == "JWT"

    def test_bearer_auth_has_description(self):
        assert "description" in _SECURITY_SCHEMES["BearerAuth"]
        assert len(_SECURITY_SCHEMES["BearerAuth"]["description"]) > 0


# =========================================================================
# custom_openapi_schema() factory
# =========================================================================

class TestCustomOpenApiSchema:

    def test_returns_callable(self):
        app = _make_app()
        result = custom_openapi_schema(app)
        assert callable(result)

    def test_callable_returns_dict(self):
        app = _make_app()
        openapi_fn = custom_openapi_schema(app)
        schema = openapi_fn()
        assert isinstance(schema, dict)

    def test_schema_has_openapi_version(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        assert "openapi" in schema
        assert schema["openapi"].startswith("3.")

    def test_schema_has_info(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        assert "info" in schema

    def test_schema_info_title(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        assert schema["info"]["title"] == API_TITLE

    def test_schema_info_version(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        assert schema["info"]["version"] == API_VERSION

    def test_schema_info_description(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        assert schema["info"]["description"] == API_DESCRIPTION

    def test_schema_has_paths(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        assert "paths" in schema
        assert len(schema["paths"]) > 0

    def test_schema_includes_security_schemes(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        assert "components" in schema
        assert "securitySchemes" in schema["components"]
        assert "BearerAuth" in schema["components"]["securitySchemes"]

    def test_schema_bearer_auth_details(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        bearer = schema["components"]["securitySchemes"]["BearerAuth"]
        assert bearer["type"] == "http"
        assert bearer["scheme"] == "bearer"
        assert bearer["bearerFormat"] == "JWT"

    def test_schema_has_global_security(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        assert "security" in schema
        assert {"BearerAuth": []} in schema["security"]

    def test_schema_includes_tags(self):
        app = _make_app()
        schema = custom_openapi_schema(app)()
        assert "tags" in schema
        tag_names = [t["name"] for t in schema["tags"]]
        # At least the tags used in our minimal app
        assert "health" in tag_names
        assert "auth" in tag_names

    def test_schema_is_cached_on_second_call(self):
        """The schema should be computed once and cached on ``app.openapi_schema``."""
        app = _make_app()
        openapi_fn = custom_openapi_schema(app)

        schema1 = openapi_fn()
        schema2 = openapi_fn()

        # Should be the exact same object (cached)
        assert schema1 is schema2
        assert app.openapi_schema is schema1

    def test_schema_respects_pre_existing_cache(self):
        """If app.openapi_schema is already set, the factory returns it as-is."""
        app = _make_app()
        fake_schema = {"openapi": "3.0.0", "info": {"title": "cached"}}
        app.openapi_schema = fake_schema

        openapi_fn = custom_openapi_schema(app)
        result = openapi_fn()

        assert result is fake_schema
