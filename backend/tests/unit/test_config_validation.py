"""Unit tests for Settings config validation logic.

Covers the ``_validate_production_secrets`` and ``_warn_empty_optional_secrets``
model validators defined in ``app.config.Settings``.
"""

from __future__ import annotations

import warnings
from typing import Any

import pytest

from app.config import Settings


# ---------------------------------------------------------------------------
# All 8 placeholder secrets that must be caught by the validator
# ---------------------------------------------------------------------------

PLACEHOLDER_SECRETS: dict[str, str] = {
    "SECRET_KEY": "YOUR_SECRET_KEY_HERE",
    "AWS_ACCESS_KEY_ID": "YOUR_AWS_ACCESS_KEY_HERE",
    "AWS_SECRET_ACCESS_KEY": "YOUR_AWS_SECRET_KEY_HERE",
    "ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY_HERE",
    "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY_HERE",
    "STRIPE_SECRET_KEY": "YOUR_STRIPE_SECRET_KEY_HERE",
    "STRIPE_WEBHOOK_SECRET": "YOUR_STRIPE_WEBHOOK_SECRET_HERE",
    "SENDGRID_API_KEY": "YOUR_SENDGRID_API_KEY_HERE",
}


def _real_secret_overrides() -> dict[str, str]:
    """Return env overrides that replace ALL placeholder secrets with real-ish values."""
    return {
        "SECRET_KEY": "real-secret-key-abc123",
        "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
        "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "ANTHROPIC_API_KEY": "sk-ant-real-key",
        "OPENAI_API_KEY": "sk-real-openai-key",
        "STRIPE_SECRET_KEY": "sk_live_real_stripe_key",
        "STRIPE_WEBHOOK_SECRET": "whsec_real_webhook_secret",
        "SENDGRID_API_KEY": "SG.real_sendgrid_key",
    }


def _build_settings(monkeypatch, extra_env: dict[str, str] | None = None) -> Settings:
    """Construct a fresh Settings instance with monkeypatched env vars.

    Prevents pydantic-settings from reading a real ``.env`` file by
    pointing to a non-existent path, and sets all supplied env vars.
    """
    # Prevent loading real .env
    monkeypatch.setenv("ENV_FILE", "/dev/null")

    if extra_env:
        for key, value in extra_env.items():
            monkeypatch.setenv(key, value)

    # Clear lru_cache so Settings() reads fresh env
    from app.config import get_settings
    get_settings.cache_clear()

    return Settings()


# ---------------------------------------------------------------------------
# Development mode: placeholder secrets are ALLOWED
# ---------------------------------------------------------------------------


class TestDevelopmentMode:
    """In development mode the validator should NOT raise even if placeholders remain."""

    def test_placeholder_secrets_allowed_in_development(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        settings = _build_settings(monkeypatch)
        assert settings.ENVIRONMENT == "development"
        # No ValueError raised -- placeholders are tolerated
        assert settings.SECRET_KEY == "YOUR_SECRET_KEY_HERE"

    def test_all_placeholders_present_in_development(self, monkeypatch):
        """Every default placeholder value should be accepted in development."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        settings = _build_settings(monkeypatch)
        for field_name, placeholder in PLACEHOLDER_SECRETS.items():
            assert getattr(settings, field_name) == placeholder

    def test_no_warnings_in_development(self, monkeypatch):
        """No UserWarning about optional secrets should be issued outside production."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _build_settings(monkeypatch)
        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user_warnings) == 0


# ---------------------------------------------------------------------------
# Production mode: placeholder secrets MUST raise ValueError
# ---------------------------------------------------------------------------


class TestProductionModePlaceholderRejection:
    """In production, any remaining placeholder secret must cause a ValueError."""

    def test_all_placeholders_raises_in_production(self, monkeypatch):
        """If ALL secrets still have placeholders, Settings() must raise."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        with pytest.raises(ValueError, match="Production mode"):
            _build_settings(monkeypatch)

    @pytest.mark.parametrize(
        "secret_name,placeholder_value",
        list(PLACEHOLDER_SECRETS.items()),
        ids=list(PLACEHOLDER_SECRETS.keys()),
    )
    def test_single_placeholder_raises_in_production(
        self, monkeypatch, secret_name: str, placeholder_value: str
    ):
        """Each individual placeholder must be caught when all others are real."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        env = _real_secret_overrides()
        # Revert one secret back to its placeholder
        env[secret_name] = placeholder_value

        with pytest.raises(ValueError, match=secret_name):
            _build_settings(monkeypatch, extra_env=env)

    def test_all_real_secrets_pass_in_production(self, monkeypatch):
        """When every placeholder is replaced with a real value, no error is raised."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        env = _real_secret_overrides()

        # Need to also supply optional fields to avoid warnings interfering
        settings = _build_settings(monkeypatch, extra_env=env)
        assert settings.ENVIRONMENT == "production"

    def test_error_message_lists_all_missing_secrets(self, monkeypatch):
        """The error message should enumerate every secret that is still a placeholder."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        with pytest.raises(ValueError) as exc_info:
            _build_settings(monkeypatch)

        error_msg = str(exc_info.value)
        for secret_name in PLACEHOLDER_SECRETS:
            assert secret_name in error_msg, (
                f"Expected '{secret_name}' to appear in the error message"
            )


# ---------------------------------------------------------------------------
# Production mode: warnings for empty optional credentials
# ---------------------------------------------------------------------------


class TestProductionOptionalWarnings:
    """In production, empty OAuth/Stripe/Ads credentials should emit warnings."""

    def _build_production_settings(self, monkeypatch, extra_env=None):
        """Helper that sets ENVIRONMENT=production with all required secrets real."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        env = _real_secret_overrides()
        if extra_env:
            env.update(extra_env)
        return _build_settings(monkeypatch, extra_env=env)

    def test_warns_for_empty_oauth_credentials(self, monkeypatch):
        """Empty Google/GitHub OAuth fields should trigger a UserWarning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self._build_production_settings(monkeypatch)

        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user_warnings) >= 1

        warning_text = str(user_warnings[0].message)
        assert "GOOGLE_CLIENT_ID" in warning_text or "OAuth" in warning_text

    def test_warns_for_empty_stripe_price_ids(self, monkeypatch):
        """Empty Stripe price ID fields should appear in the warning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self._build_production_settings(monkeypatch)

        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user_warnings) >= 1

        # Combine all warning messages
        all_warning_text = " ".join(str(w.message) for w in user_warnings)
        assert "STRIPE_PRICE_STARTER" in all_warning_text

    def test_warns_for_empty_amazon_ads_credentials(self, monkeypatch):
        """Empty Amazon Ads credentials should appear in the warning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self._build_production_settings(monkeypatch)

        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        all_warning_text = " ".join(str(w.message) for w in user_warnings)
        assert "AMAZON_ADS_CLIENT_ID" in all_warning_text

    def test_no_warning_when_optional_fields_populated(self, monkeypatch):
        """If all optional recommended fields are populated, no warning is emitted."""
        optional_env = {
            "GOOGLE_CLIENT_ID": "google-id",
            "GOOGLE_CLIENT_SECRET": "google-secret",
            "GITHUB_CLIENT_ID": "github-id",
            "GITHUB_CLIENT_SECRET": "github-secret",
            "STRIPE_PRICE_STARTER": "price_starter_123",
            "STRIPE_PRICE_PRO": "price_pro_123",
            "STRIPE_PRICE_BUSINESS": "price_business_123",
            "STRIPE_PRICE_ENTERPRISE": "price_enterprise_123",
            "AMAZON_ADS_CLIENT_ID": "amazon-ads-id",
            "AMAZON_ADS_CLIENT_SECRET": "amazon-ads-secret",
        }

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self._build_production_settings(monkeypatch, extra_env=optional_env)

        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user_warnings) == 0, (
            f"Expected no UserWarnings but got: "
            f"{[str(w.message) for w in user_warnings]}"
        )

    def test_warning_mentions_unavailable_features(self, monkeypatch):
        """The warning text should mention which features will be unavailable."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self._build_production_settings(monkeypatch)

        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user_warnings) >= 1

        all_warning_text = " ".join(str(w.message) for w in user_warnings)
        # The warning message should reference the affected features
        assert "OAuth" in all_warning_text or "Stripe" in all_warning_text


# ---------------------------------------------------------------------------
# CORS origin injection
# ---------------------------------------------------------------------------


class TestCORSOriginInjection:
    """The validator also appends FRONTEND_URL to CORS_ORIGINS."""

    def test_frontend_url_added_to_cors_origins(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")
        settings = _build_settings(monkeypatch)
        assert "https://app.example.com" in settings.CORS_ORIGINS

    def test_duplicate_frontend_url_not_added_twice(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
        settings = _build_settings(monkeypatch)
        # http://localhost:3000 is the default CORS origin, should not be duplicated
        count = settings.CORS_ORIGINS.count("http://localhost:3000")
        assert count == 1


# ---------------------------------------------------------------------------
# Staging mode: behaves like development (not production)
# ---------------------------------------------------------------------------


class TestStagingMode:
    """Staging mode should NOT raise for placeholders (only production does)."""

    def test_placeholders_allowed_in_staging(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "staging")
        settings = _build_settings(monkeypatch)
        assert settings.ENVIRONMENT == "staging"
        # No ValueError raised
        assert settings.SECRET_KEY == "YOUR_SECRET_KEY_HERE"

    def test_no_warnings_in_staging(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "staging")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _build_settings(monkeypatch)
        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user_warnings) == 0
