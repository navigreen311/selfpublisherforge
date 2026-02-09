# W04: User & Organization Management
**Branch:** `ai-feature/user-org-management`
**Scope:** fullstack

## Mission
Implement user profiles, organization management, team invitations, role management, onboarding, and preferences.

## What to Build

### Backend
1. **backend/app/modules/users/__init__.py**
2. **backend/app/modules/users/router.py** — Endpoints:
   - GET /api/v1/users/me — Get current user profile
   - PATCH /api/v1/users/me — Update profile
   - PATCH /api/v1/users/me/preferences — Update preferences (JSONB)
   - GET /api/v1/users/me/sessions — List active sessions
   - DELETE /api/v1/users/me/sessions/{id} — Revoke session
   - GET /api/v1/orgs/{id} — Get org details
   - PATCH /api/v1/orgs/{id} — Update org (owner/admin only)
   - GET /api/v1/orgs/{id}/members — List members
   - POST /api/v1/orgs/{id}/invite — Invite user (admin+)
   - PATCH /api/v1/orgs/{id}/members/{user_id}/role — Change role (owner only)
   - DELETE /api/v1/orgs/{id}/members/{user_id} — Remove member (admin+)
   - POST /api/v1/orgs/{id}/api-keys — Create API key (admin+)
   - GET /api/v1/orgs/{id}/api-keys — List API keys
   - DELETE /api/v1/orgs/{id}/api-keys/{key_id} — Revoke API key

3. **backend/app/modules/users/schemas.py** — UserProfile, UpdateUserRequest, OrgDetails, InviteRequest, ApiKeyCreate, ApiKeyResponse
4. **backend/app/modules/users/service.py** — User CRUD, org management, invitation logic, role validation

### Frontend
5. **frontend/src/app/(dashboard)/settings/page.tsx** — Settings layout with tabs
6. **frontend/src/app/(dashboard)/settings/profile/page.tsx** — Profile edit form
7. **frontend/src/app/(dashboard)/settings/organization/page.tsx** — Org settings, member management
8. **frontend/src/app/(dashboard)/settings/api-keys/page.tsx** — API key management UI
9. **frontend/src/modules/users/hooks.ts** — React Query hooks for user/org API calls
10. **frontend/src/modules/users/components/** — ProfileForm, MemberList, InviteModal, ApiKeyTable
    - **frontend/src/modules/users/components/ProfileForm.tsx**
    - **frontend/src/modules/users/components/MemberList.tsx**
    - **frontend/src/modules/users/components/InviteModal.tsx**
    - **frontend/src/modules/users/components/ApiKeyTable.tsx**

### Tests
11. **backend/tests/unit/test_user_service.py**
12. **backend/tests/integration/test_user_api.py**

## Database Tables Used (read-only, created by W02)
- users, organizations, user_sessions, api_keys

## Dependencies
- Uses: backend/app/core/security.py (hash_password, verify_password)
- Uses: backend/app/core/dependencies.py (get_current_user, require_role)
- Uses: backend/app/core/pagination.py (paginate)

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
`feat(users): implement user & organization management with team invitations`
