# W17: Knowledge Vault & Research Library (Module #29)
**Branch:** `ai-feature/knowledge-vault`
**Scope:** fullstack

## Mission
Build the Knowledge Vault: a research repository where authors store, organize, search, and leverage research materials with AI assistance.

## API Endpoints
- POST /api/v1/knowledge — Create knowledge entry (manual, URL import, file import)
- GET /api/v1/knowledge — List entries (paginated, filterable by tag, type, source)
- GET /api/v1/knowledge/{id} — Get entry detail
- PUT /api/v1/knowledge/{id} — Update entry
- DELETE /api/v1/knowledge/{id} — Soft delete
- POST /api/v1/knowledge/search — Full-text search via Elasticsearch
- POST /api/v1/knowledge/import — Import from URL or file (extracts key info)
- GET /api/v1/knowledge/suggestions — AI-suggested research for current project
- POST /api/v1/knowledge/{id}/summarize — AI summarize a research entry
- GET /api/v1/knowledge/tags — List all tags

## What to Build

### Backend
1. **backend/app/modules/knowledge_vault/__init__.py**
2. **backend/app/modules/knowledge_vault/router.py** — All endpoints
3. **backend/app/modules/knowledge_vault/schemas.py** — KnowledgeEntry, CreateEntry, SearchRequest, SearchResult, ImportRequest
4. **backend/app/modules/knowledge_vault/service.py** — CRUD, search, import, AI summarization
5. **backend/app/modules/knowledge_vault/models.py** — knowledge_entries table: id, org_id, title, content (TEXT), source_url, source_type (manual/url/file/clip), tags (ARRAY), credibility_score (Float), metadata (JSONB), created_at, updated_at, deleted_at
6. **backend/app/modules/knowledge_vault/search.py** — Elasticsearch integration: index entries, full-text search with relevance scoring, faceted search by tags
7. **backend/app/modules/knowledge_vault/importer.py** — URL content extraction (web scraping), file content extraction (PDF/DOCX), AI-powered key fact extraction
8. **backend/app/tasks/knowledge_vault.py** — Celery tasks for async import and indexing

### Frontend
9. **frontend/src/app/(dashboard)/knowledge/page.tsx** — Knowledge vault: search bar, tag filter, entry list, create button
10. **frontend/src/app/(dashboard)/knowledge/[id]/page.tsx** — Entry detail view with AI summary
11. **frontend/src/modules/knowledge/hooks.ts** — React Query hooks
12. **frontend/src/modules/knowledge/components/** — EntryCard, SearchBar, TagFilter, ImportModal

### Tests
13. **backend/tests/unit/test_knowledge_service.py**
14. **backend/tests/integration/test_knowledge_api.py**

## Commit Convention
`feat(knowledge): implement knowledge vault with Elasticsearch search and AI import`
