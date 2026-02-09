# W15: Style Cloning Engine (Module #3)
**Branch:** `ai-feature/style-cloning`
**Scope:** api

## Mission
Build the Style Cloning Engine — SelfPublisherForge's primary technical differentiator. Multi-stage NLP pipeline that analyzes author manuscripts to create persistent voice profiles used for AI generation.

## Pipeline Stages (from blueprint)
1. **Text Ingestion & Preprocessing** — Accept DOCX/EPUB/PDF/TXT, extract text, segment into sentences/paragraphs/chapters. Min 10K words, 50K+ for high confidence.
2. **Linguistic Feature Extraction** — Vocabulary analysis (unique words, density, rare word freq, reading level), sentence structure (avg length, variance, simple/compound/complex ratio), paragraph patterns (avg length, transition words), rhetorical devices (metaphor density, humor markers, emotional intensity), dialogue patterns (fiction: tag freq, action beat ratio, dialogue-to-narrative ratio)
3. **Voice Profile Generation** — 200+ dimension voice vector, natural language style guide, example prompts, style card with key metrics
4. **Generation-Time Application** — Inject voice profile as system context, post-generation conformity check, drift detection, continuous refinement

## API Endpoints
- POST /api/v1/style-profiles — Create new profile (upload sample manuscripts)
- GET /api/v1/style-profiles — List org profiles
- GET /api/v1/style-profiles/{id} — Get profile details
- GET /api/v1/style-profiles/{id}/fingerprint — Get full voice fingerprint
- POST /api/v1/style-profiles/{id}/analyze — Add more samples, re-analyze
- POST /api/v1/style-profiles/{id}/generate-sample — Generate a sample text matching the profile
- DELETE /api/v1/style-profiles/{id} — Soft delete
- POST /api/v1/style-profiles/{id}/conformity-check — Check text against profile (returns 0-100 match score)

## What to Build

### Backend
1. **backend/app/modules/style_cloning/__init__.py**
2. **backend/app/modules/style_cloning/router.py** — All endpoints
3. **backend/app/modules/style_cloning/schemas.py** — CreateProfileRequest, ProfileResponse, VoiceFingerprint, StyleCard, ConformityCheckResult
4. **backend/app/modules/style_cloning/service.py** — Profile CRUD, orchestrate pipeline stages
5. **backend/app/modules/style_cloning/ingestion.py** — Text extraction from DOCX/EPUB/PDF/TXT, normalization, segmentation
6. **backend/app/modules/style_cloning/features.py** — Linguistic feature extraction: vocabulary analysis, sentence patterns, paragraph patterns, rhetorical devices, dialogue analysis
7. **backend/app/modules/style_cloning/profile_generator.py** — Aggregate features into voice vector, generate style guide, create style card
8. **backend/app/modules/style_cloning/conformity.py** — Compare generated text features against profile, return match score 0-100
9. **backend/app/tasks/style_cloning.py** — Celery task for async profile analysis (can take minutes for large manuscripts)

### Tests
10. **backend/tests/unit/test_feature_extraction.py** — Test vocabulary, sentence, paragraph analysis
11. **backend/tests/unit/test_conformity.py** — Test style match scoring
12. **backend/tests/integration/test_style_api.py** — Test profile CRUD and analysis endpoints

## Database Tables (from W02, read-only)
style_profiles

## Commit Convention
`feat(style): implement style cloning engine with NLP pipeline and voice profiles`
