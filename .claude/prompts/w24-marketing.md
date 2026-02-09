# W24: Marketing & Launch Command (Module #7)
**Branch:** `ai-feature/marketing-launch`
**Scope:** fullstack

## Mission
Build the Marketing & Launch Command center: launch plan generator, email sequence builder, social media content calendar, ARC (Advance Review Copy) management.

## API Endpoints
- POST /api/v1/marketing/launch-plan/generate — AI-generate a launch plan
- GET /api/v1/marketing/launch-plans — List launch plans
- GET /api/v1/marketing/launch-plans/{id} — Get launch plan detail
- PATCH /api/v1/marketing/launch-plans/{id} — Update plan
- POST /api/v1/marketing/email-sequences — Create email sequence
- GET /api/v1/marketing/email-sequences — List sequences
- PATCH /api/v1/marketing/email-sequences/{id} — Update sequence
- POST /api/v1/marketing/email-sequences/{id}/send — Trigger send
- POST /api/v1/marketing/social/generate — Generate social media content
- GET /api/v1/marketing/social/calendar — Get social media calendar
- POST /api/v1/marketing/arc — Create ARC campaign
- GET /api/v1/marketing/arc — List ARC campaigns
- POST /api/v1/marketing/arc/{id}/send — Send ARC copies

## What to Build

### Backend
1. **backend/app/modules/marketing/__init__.py**
2. **backend/app/modules/marketing/router.py** — All endpoints
3. **backend/app/modules/marketing/schemas.py** — LaunchPlan, LaunchPhase, EmailSequence, EmailTemplate, SocialPost, ARCCampaign
4. **backend/app/modules/marketing/service.py** — Launch plan management, email sequence orchestration, social content management
5. **backend/app/modules/marketing/launch_planner.py** — AI launch plan generation: pre-launch (4 weeks), launch week, post-launch phases with specific tasks and dates
6. **backend/app/modules/marketing/email_builder.py** — Email sequence builder: templates (welcome, launch, follow-up, review request), scheduling, personalization
7. **backend/app/modules/marketing/social_generator.py** — AI: generate social media posts (Twitter, Facebook, Instagram) from book data
8. **backend/app/modules/marketing/arc_manager.py** — ARC campaign: recipient management, delivery tracking, review follow-up
9. **backend/app/tasks/marketing.py** — Celery: scheduled email sends, social post reminders, ARC follow-ups

### Frontend
10. **frontend/src/app/(dashboard)/marketing/page.tsx** — Marketing dashboard: active campaigns, launch plans, email stats
11. **frontend/src/app/(dashboard)/marketing/launch/[id]/page.tsx** — Launch plan detail with timeline view and checklist
12. **frontend/src/app/(dashboard)/marketing/email/page.tsx** — Email sequence builder with drag-drop
13. **frontend/src/modules/marketing/hooks.ts** — React Query hooks
14. **frontend/src/modules/marketing/components/** — LaunchTimeline, EmailSequenceBuilder, SocialCalendar, ARCTable

### Tests
15. **backend/tests/unit/test_launch_planner.py**
16. **backend/tests/integration/test_marketing_api.py**

## Database Tables (from W02, read-only)
launch_plans, email_sequences, campaigns

## Commit Convention
`feat(marketing): implement marketing & launch command with email sequences and ARC management`
