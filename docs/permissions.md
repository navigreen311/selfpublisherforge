# Permissions & RBAC

This document describes the SelfPublisherForge permission system introduced in
Stream 1 of the Final Gaps release (migrations `021_add_pen_names` and
`022_add_roles_and_invitations`).

## Data model

- `roles` — one row per role per org. `is_system = true` for the six built-in
  roles seeded on org creation (see migration `022`):
  `Owner`, `Admin`, `Editor`, `Designer`, `Viewer`, `VA`.
- `roles.permissions` is a JSONB blob shaped as:

  ```json
  {
    "<module>": {
      "view": true,
      "create": false,
      "edit": false,
      "delete": false,
      "publish": false
    }
  }
  ```

- `users.role_id` — nullable FK into `roles`. Backfilled to the `Owner` row for
  every existing user in migration `022`.
- `users.role` (legacy enum) is still written by older code paths; the
  permission loader falls back to matching this enum against the system role
  name.
- `team_invitations` — pending invites, joined to `roles.id` via `role_id`.

## Modules

The module keys seeded by migration `022` line up with the Custom Role Builder
mockup in the spec and include — among others — `dashboard`, `projects`,
`market`, `competitors`, `reviews`, `writing`, `cover_design`, `audiobook`,
`childrens_books`, `coloring_books`, `puzzle_books`, `comic_books`,
`cookbooks`, `style_profiles`, `pipeline`, `marketing`, `publishing`,
`advertising`, `analytics`, `analytics_revenue`, `pricing`, `agents`,
`admin`, `settings`, `team`, `billing`, `pen_names`.

New modules can add themselves by inserting per-role permission entries at
runtime; missing entries default to deny.

## The `require_permission` dependency

`app.modules.team.permissions.require_permission(module, action)` returns a
FastAPI dependency that:

1. Loads the caller's effective permissions (via `users.role_id -> roles`, with
   legacy role fallback).
2. Returns the user dict if `permissions[module][action]` is truthy.
3. Raises `HTTPException(403)` otherwise.
4. Always allows the legacy `owner` role as a safety hatch so an org cannot
   lock itself out pre-backfill.

### Usage

```python
from fastapi import Depends
from app.modules.team.permissions import require_permission

@router.post(
    "/cookbooks",
    dependencies=[Depends(require_permission("cookbooks", "create"))],
)
async def create_cookbook(...):
    ...
```

Use it as a route-level `dependencies=[...]` entry so the checker runs *before*
the handler body but after authentication. Handlers that also need the user
dict can inject it separately via `Depends(get_current_user)`.

## Which endpoints are wired?

The Stream 1 PR ships permission enforcement on:

- **All team / role endpoints** (`POST/PATCH/DELETE /roles`, invites,
  `team/{user}/role`, `team/{user}`).
- **All pen-name mutations** (`POST`, `PATCH`, `DELETE /pen-names/...`).
- **A representative sample of high-impact endpoints** in other modules —
  publishing submission and billing — as integration examples.

We intentionally did *not* try to wire every endpoint in the monorepo in this
PR. Other streams and follow-up PRs should add `require_permission` to their
endpoints module-by-module, following the pattern above. A module without a
permission check continues to work (it's permissive), so the rollout can be
incremental.

## UI enforcement

Frontend hooks should call `GET /api/v1/roles` and look up the user's role to
decide which UI elements to disable. The permission map is already returned on
the role response so no further endpoint is needed. A helper
`useCanI(module, action)` can be added in a follow-up.
