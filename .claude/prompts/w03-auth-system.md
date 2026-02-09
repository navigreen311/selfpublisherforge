# W03: Authentication System
**Branch:** `ai-feature/auth-system`
**Scope:** api

## Mission
Implement the complete authentication system: registration, login, JWT tokens, refresh tokens, password reset, email verification, MFA (TOTP), session management, and RBAC.

## What to Build

### Backend Files
1. **backend/app/modules/auth/__init__.py**
2. **backend/app/modules/auth/router.py** — FastAPI router with endpoints:
   - POST /api/v1/auth/register — Create user + org, send verification email
   - POST /api/v1/auth/login — Validate credentials, return JWT access + refresh tokens
   - POST /api/v1/auth/refresh — Refresh access token using refresh token
   - POST /api/v1/auth/logout — Invalidate session
   - POST /api/v1/auth/forgot-password — Send password reset email
   - POST /api/v1/auth/reset-password — Reset password with token
   - POST /api/v1/auth/verify-email — Verify email with token
   - POST /api/v1/auth/mfa/setup — Generate TOTP secret + QR code
   - POST /api/v1/auth/mfa/verify — Verify TOTP code
   - POST /api/v1/auth/mfa/disable — Disable MFA

3. **backend/app/modules/auth/schemas.py** — Pydantic models:
   - RegisterRequest(email, password, name, org_name)
   - LoginRequest(email, password, mfa_code optional)
   - TokenResponse(access_token, refresh_token, token_type, expires_in)
   - RefreshRequest(refresh_token)
   - ForgotPasswordRequest(email)
   - ResetPasswordRequest(token, new_password)
   - VerifyEmailRequest(token)
   - MFASetupResponse(secret, qr_code_url, backup_codes)

4. **backend/app/modules/auth/service.py** — Business logic:
   - register_user() — Create org + user, hash password, generate verification token
   - authenticate() — Verify credentials, check MFA if enabled, create session
   - refresh_token() — Validate refresh token, issue new access token
   - logout() — Delete session
   - Session management: max 5 concurrent sessions, invalidate on password change
   - Password validation: min 8 chars, uppercase, lowercase, number, special char

5. **backend/app/modules/auth/utils.py** — Helper functions for token generation, email token creation

### Tests
6. **backend/tests/unit/test_auth_service.py** — Test registration, login, token refresh, password reset, MFA
7. **backend/tests/integration/test_auth_api.py** — Test all auth endpoints with test client

## Database Tables Used (read-only, created by W02)
- users, organizations, user_sessions, api_keys

## Dependencies
- Uses: backend/app/core/security.py (hash_password, verify_password, create_access_token, create_refresh_token)
- Uses: backend/app/core/dependencies.py (get_current_user)

## Read-Only (do NOT modify)
- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- backend/app/core/security.py
- backend/app/core/dependencies.py
- backend/app/core/exceptions.py
- backend/app/core/pagination.py
- backend/app/schemas/common.py
- frontend/src/app/layout.tsx
- frontend/src/components/providers.tsx
- frontend/src/lib/utils.ts
- frontend/src/lib/api.ts
- frontend/src/types/index.ts
- docker-compose.yml, CLAUDE.md, README.md

## Commit Convention
`feat(auth): implement complete authentication system with JWT, MFA, and session management`
