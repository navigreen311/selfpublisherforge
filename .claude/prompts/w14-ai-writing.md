# W14: AI Writing Studio (Module #2)
**Branch:** `ai-feature/ai-writing-studio`
**Scope:** fullstack

## Mission
Build the AI Writing Studio: book outline generator, chapter writing with AI assistance, editing tools, readability scoring, and a rich manuscript editor.

## API Endpoints
- POST /api/v1/generate — Unified AI generation endpoint (generation_type: chapter, blurb, outline, title_suggestions, etc.)
- GET /api/v1/books/{id}/manuscript — Get full manuscript
- GET /api/v1/books/{id}/manuscript/chapters — List chapters
- GET /api/v1/books/{id}/manuscript/chapters/{chapter_id} — Get chapter
- PUT /api/v1/books/{id}/manuscript/chapters/{chapter_id} — Update chapter content
- POST /api/v1/books/{id}/manuscript/chapters — Create new chapter
- PATCH /api/v1/books/{id}/manuscript/chapters/reorder — Reorder chapters
- POST /api/v1/books/{id}/manuscript/analyze — Analyze manuscript (readability, pacing, word count)
- GET /api/v1/books/{id}/manuscript/readability-score — Get readability metrics
- POST /api/v1/books/{id}/outline/generate — AI-generate book outline
- POST /api/v1/writing-sessions — Record writing session

## Unified Generation Endpoint (POST /api/v1/generate)
Request: generation_type (enum), project_id, style_profile_id (optional), instructions, context (JSONB), model_preference (auto|claude|gpt4|gemini), stream (bool, default true), quality_checks (string[])
Response (streaming): SSE events — event:token (chunks), event:quality (check results), event:complete (final metadata)

## What to Build

### Backend
1. **backend/app/modules/ai_writing/__init__.py**
2. **backend/app/modules/ai_writing/router.py** — All endpoints above
3. **backend/app/modules/ai_writing/schemas.py** — GenerateRequest, GenerateResponse, ChapterContent, ManuscriptAnalysis, ReadabilityScore, OutlineRequest/Response, WritingSessionRecord
4. **backend/app/modules/ai_writing/service.py** — Chapter CRUD, manuscript management, outline generation, readability analysis (Flesch-Kincaid, Gunning Fog, SMOG)
5. **backend/app/modules/ai_writing/generator.py** — AI content generation: prompt construction, streaming handler, quality post-checks
6. **backend/app/modules/ai_writing/prompts.py** — Prompt templates for each generation type (outline, chapter, blurb, etc.)
7. **backend/app/modules/ai_writing/readability.py** — Readability scoring algorithms (Flesch-Kincaid, Gunning Fog, SMOG, reading level)

### Frontend
8. **frontend/src/app/(dashboard)/writing/page.tsx** — Writing studio: project selector, book list, recent sessions
9. **frontend/src/app/(dashboard)/writing/[bookId]/page.tsx** — Manuscript editor: chapter sidebar, rich text editor, AI panel, word count, readability
10. **frontend/src/modules/writing/components/editor.tsx** — Rich text manuscript editor with AI inline suggestions
11. **frontend/src/modules/writing/components/chapter-sidebar.tsx** — Chapter list with drag-reorder
12. **frontend/src/modules/writing/components/ai-panel.tsx** — AI assistant panel: generate, continue, edit selection, tone adjustment
13. **frontend/src/modules/writing/hooks.ts** — React Query hooks + SSE streaming hook for AI generation

### Tests
14. **backend/tests/unit/test_readability.py** — Test readability scoring
15. **backend/tests/unit/test_ai_generator.py** — Test prompt construction, streaming
16. **backend/tests/integration/test_writing_api.py** — Test manuscript and generation endpoints

## Database Tables (from W02, read-only)
manuscripts, chapters, writing_sessions, content_assets

## Commit Convention
`feat(writing): implement AI writing studio with manuscript editor, generation, and readability`
