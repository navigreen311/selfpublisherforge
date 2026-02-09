# W18: Production Pipeline Manager (Module #4)
**Branch:** `ai-feature/production-pipeline`
**Scope:** fullstack

## Mission
Build the Production Pipeline Manager: a workflow engine for managing the editorial pipeline (writing, editing, proofreading, formatting) with deadline tracking and status dashboard.

## API Endpoints
- POST /api/v1/pipelines — Create pipeline for a book
- GET /api/v1/pipelines — List pipelines (paginated, filterable)
- GET /api/v1/pipelines/{id} — Get pipeline detail with tasks
- PATCH /api/v1/pipelines/{id} — Update pipeline settings
- POST /api/v1/pipelines/{id}/tasks — Add task to pipeline
- PATCH /api/v1/pipelines/{id}/tasks/{task_id} — Update task status/assignee
- GET /api/v1/pipelines/{id}/timeline — Get Gantt-style timeline
- POST /api/v1/pipelines/templates — Save pipeline as template
- GET /api/v1/pipelines/templates — List pipeline templates

## What to Build

### Backend
1. **backend/app/modules/production_pipeline/__init__.py**
2. **backend/app/modules/production_pipeline/router.py** — All endpoints
3. **backend/app/modules/production_pipeline/schemas.py** — Pipeline, PipelineTask, PipelineTemplate, CreatePipeline, TimelineView
4. **backend/app/modules/production_pipeline/service.py** — Pipeline CRUD, task management, status transitions, deadline calculation
5. **backend/app/modules/production_pipeline/models.py** — pipelines: id, org_id, book_id, name, status, settings (JSONB), deadline. pipeline_tasks: id, pipeline_id, title, type (writing/editing/proofreading/formatting/review), status, assignee_id, due_date, depends_on (ARRAY), completed_at
6. **backend/app/modules/production_pipeline/workflow.py** — Workflow engine: task dependency resolution, status transitions, deadline alerts
7. **backend/app/tasks/production_pipeline.py** — Celery: deadline reminder notifications, overdue alerts

### Frontend
8. **frontend/src/app/(dashboard)/pipeline/page.tsx** — Pipeline dashboard: active pipelines, progress bars, overdue alerts
9. **frontend/src/app/(dashboard)/pipeline/[id]/page.tsx** — Pipeline detail: Kanban board or timeline view, task cards
10. **frontend/src/modules/pipeline/components/** — PipelineCard, TaskBoard, TimelineView, TaskForm
11. **frontend/src/modules/pipeline/hooks.ts** — React Query hooks

### Tests
12. **backend/tests/unit/test_pipeline_workflow.py** — Test dependency resolution, status transitions
13. **backend/tests/integration/test_pipeline_api.py**

## Commit Convention
`feat(pipeline): implement production pipeline manager with workflow engine`
