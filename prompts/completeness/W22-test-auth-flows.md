# W22: Integration Tests for Auth Forgot-Password + MFA Flows

## Files to create
- `backend/tests/integration/test_auth_mfa.py` — NEW

## Context
Auth endpoints exist:
- POST `/api/v1/auth/forgot-password`
- POST `/api/v1/auth/reset-password`
- POST `/api/v1/auth/mfa/setup`
- POST `/api/v1/auth/mfa/verify`
- POST `/api/v1/auth/mfa/disable`

## Task

### 1. Read auth router and service

Read `backend/app/modules/auth/router.py` and `backend/app/modules/auth/service.py` to understand the exact request/response formats.

### 2. Write integration tests

Follow the pattern from `backend/tests/integration/test_user_api.py` — create a test app with overridden dependencies:

```python
"""Integration tests for auth password-reset and MFA flows."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.auth.router import router
from app.database import get_db

class TestForgotPassword:
    def test_forgot_password_returns_200_always(self):
        """POST /forgot-password should return 200 for any email (no enumeration)."""
        ...

    def test_forgot_password_invalid_email_returns_422(self):
        """Invalid email format should return 422."""
        ...

class TestResetPassword:
    def test_reset_password_with_valid_token(self):
        """POST /reset-password with valid token should reset password."""
        ...

    def test_reset_password_with_invalid_token(self):
        """POST /reset-password with invalid token should return 400."""
        ...

    def test_reset_password_weak_password(self):
        """Weak password should be rejected."""
        ...

class TestMFASetup:
    def test_mfa_setup_returns_secret_and_qr(self):
        """POST /mfa/setup should return secret, qr_code_url, backup_codes."""
        ...

    def test_mfa_verify_activates(self):
        """POST /mfa/verify with correct code should activate MFA."""
        ...

    def test_mfa_verify_wrong_code(self):
        """POST /mfa/verify with wrong code should return 400."""
        ...

    def test_mfa_disable_requires_password(self):
        """POST /mfa/disable should require password confirmation."""
        ...

    def test_mfa_disable_wrong_password(self):
        """POST /mfa/disable with wrong password should return 403."""
        ...
```

Write at least 10 tests. Mock the database and any email sending.
