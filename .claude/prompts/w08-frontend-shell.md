# W08: Frontend Shell & Design System
**Branch:** `ai-feature/frontend-shell`
**Scope:** ui

## Mission
Build the complete frontend shell: responsive dashboard layout, shadcn/ui component library, navigation, theme support, onboarding flow, and reusable UI components.

## What to Build

### Core Layout
1. **frontend/src/components/layout/sidebar.tsx** — REPLACE placeholder with full sidebar: collapsible, icons (lucide-react), active state, mobile drawer, user menu at bottom
2. **frontend/src/components/layout/header.tsx** — REPLACE with: breadcrumbs, search bar, notification bell, user avatar dropdown, theme toggle
3. **frontend/src/components/layout/mobile-nav.tsx** — Mobile responsive navigation drawer

### shadcn/ui Components (create in frontend/src/components/ui/)
4. **button.tsx** — Variants: default, destructive, outline, secondary, ghost, link. Sizes: sm, default, lg, icon
5. **input.tsx** — Text input with label, error state, helper text
6. **card.tsx** — Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
7. **badge.tsx** — Variants: default, secondary, destructive, outline
8. **dialog.tsx** — Modal dialog using Radix
9. **dropdown-menu.tsx** — Dropdown menu using Radix
10. **select.tsx** — Select using Radix
11. **tabs.tsx** — Tabs using Radix
12. **table.tsx** — Table, TableHeader, TableBody, TableRow, TableHead, TableCell
13. **textarea.tsx** — Auto-growing textarea
14. **tooltip.tsx** — Tooltip using Radix
15. **skeleton.tsx** — Loading skeleton
16. **separator.tsx** — Separator using Radix
17. **switch.tsx** — Toggle switch using Radix
18. **avatar.tsx** — Avatar using Radix
19. **progress.tsx** — Progress bar
20. **alert.tsx** — Alert with variants: default, destructive

### Dashboard Pages
21. **frontend/src/app/(dashboard)/dashboard/page.tsx** — REPLACE with real dashboard: stat cards grid, recent activity list, quick actions, project list preview
22. **frontend/src/app/(dashboard)/projects/page.tsx** — Projects list with filters, search, create button
23. **frontend/src/app/(dashboard)/projects/new/page.tsx** — Create new project form (title, type, genre, pen name)

### Auth Pages
24. **frontend/src/app/(auth)/login/page.tsx** — REPLACE with real login form: email, password, MFA input, remember me, forgot password link
25. **frontend/src/app/(auth)/register/page.tsx** — REPLACE with registration form: name, email, password, org name, plan selection
26. **frontend/src/app/(auth)/layout.tsx** — Auth layout: centered card, branding

### Onboarding
27. **frontend/src/app/(dashboard)/onboarding/page.tsx** — Multi-step onboarding: welcome, first project, connect KDP, first AI generation
28. **frontend/src/components/shared/onboarding-wizard.tsx** — Reusable step wizard component

### Shared Components
29. **frontend/src/components/shared/data-table.tsx** — Generic sortable, filterable data table with pagination
30. **frontend/src/components/shared/stat-card.tsx** — Metric card (value, label, trend, icon)
31. **frontend/src/components/shared/empty-state.tsx** — Empty state with icon, message, action button
32. **frontend/src/components/shared/loading.tsx** — Full page + inline loading states
33. **frontend/src/components/shared/error-boundary.tsx** — Error boundary with fallback UI
34. **frontend/src/components/shared/confirm-dialog.tsx** — Confirmation dialog for destructive actions

### Hooks
35. **frontend/src/hooks/use-auth.ts** — Auth state management (login, logout, isAuthenticated, user)
36. **frontend/src/hooks/use-theme.ts** — Theme toggle (light/dark/system)
37. **frontend/src/hooks/use-sidebar.ts** — Sidebar collapsed state

### State Management
38. **frontend/src/lib/store.ts** — Zustand store: auth state, UI state (sidebar, theme, notifications)

## Tests
39. **frontend/src/components/ui/__tests__/button.test.tsx** — Component tests for button variants
40. **frontend/src/components/layout/__tests__/sidebar.test.tsx** — Sidebar navigation tests

## Read-Only (do NOT modify)
- frontend/src/app/layout.tsx
- frontend/src/components/providers.tsx
- frontend/src/lib/utils.ts
- frontend/src/lib/api.ts
- frontend/src/types/index.ts
- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- backend/app/core/security.py
- backend/app/core/dependencies.py
- backend/app/core/exceptions.py
- backend/app/core/pagination.py
- backend/app/schemas/common.py
- docker-compose.yml, CLAUDE.md, README.md

## Commit Convention
`feat(ui): implement frontend shell with design system, layouts, and core components`
