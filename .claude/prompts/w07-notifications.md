# W07: Notification Service
**Branch:** `ai-feature/notifications`
**Scope:** api

## Mission
Implement a notification service for transactional emails (SendGrid), in-app notifications, and notification preferences.

## What to Build

### Backend
1. **backend/app/modules/notifications/__init__.py**
2. **backend/app/modules/notifications/router.py** — Endpoints:
   - GET /api/v1/notifications — List user notifications (paginated)
   - PATCH /api/v1/notifications/{id}/read — Mark as read
   - POST /api/v1/notifications/read-all — Mark all as read
   - GET /api/v1/notifications/preferences — Get notification preferences
   - PATCH /api/v1/notifications/preferences — Update preferences
   - GET /api/v1/notifications/unread-count — Get unread count

3. **backend/app/modules/notifications/schemas.py** — Notification, NotificationPreferences, CreateNotification
4. **backend/app/modules/notifications/service.py** — Create notifications, send emails, preference management
5. **backend/app/modules/notifications/email.py** — SendGrid integration: send_transactional_email, email templates (welcome, verification, password reset, team invite, AI task complete, publishing status)
6. **backend/app/modules/notifications/models.py** — Notification model:
   - notifications: id, org_id, user_id, type (enum), title, message, data (JSONB), read_at, created_at
   - notification_preferences: id, user_id, channel (email/in_app/push), category, enabled

7. **backend/app/tasks/notifications.py** — Celery tasks for async email sending, batch notification delivery

### Tests
8. **backend/tests/unit/test_notification_service.py**
9. **backend/tests/integration/test_notification_api.py**

## Database Tables Owned
- notifications: id (UUID PK), org_id (FK), user_id (FK), type (enum: info/success/warning/error/ai_complete/publish_status/team_invite), title (VARCHAR 255), message (TEXT), data (JSONB), read_at (TIMESTAMP nullable), created_at (TIMESTAMP)
- notification_preferences: id (UUID PK), user_id (FK), channel (enum: email/in_app/push), category (VARCHAR 100), enabled (BOOLEAN default true)

### Indexes
- B-tree on notifications(user_id, created_at DESC)
- B-tree on notifications(org_id)
- Partial index on notifications WHERE read_at IS NULL
- Unique index on notification_preferences(user_id, channel, category)

## Dependencies
- Uses: backend/app/core/dependencies.py (get_current_user)
- Uses: backend/app/core/exceptions.py (AppException)
- Uses: backend/app/core/pagination.py (paginate)
- External: sendgrid Python SDK

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
`feat(notifications): implement notification service with email and in-app support`
