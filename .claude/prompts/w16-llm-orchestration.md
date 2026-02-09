# W16: LLM Orchestration Layer
**Branch:** `ai-feature/llm-orchestration`
**Scope:** api

## Mission
Build the model-agnostic LLM orchestration layer: model routing, streaming responses, token tracking, semantic caching, cost management, and quality assurance.

## Model Routing (from blueprint)
| Task | Primary | Fallback |
|------|---------|----------|
| Long-form writing | Claude Opus | Claude Sonnet |
| Blurb/ad copy | Claude Sonnet | GPT-4 |
| Market analysis | Claude Sonnet | GPT-4 |
| Style fingerprinting | Claude Opus | None |
| Review sentiment | Claude Haiku | Claude Sonnet |
| Quick edits/grammar | Claude Haiku | GPT-4 Mini |

## Cost Management Strategies
- Model tiering (40-60% savings vs all-Opus)
- Semantic caching in Redis (TTL: 24h market data, 7d style analysis)
- Prompt optimization (minimize tokens)
- Batch processing for small tasks
- Per-org budgets with alerts at 50/75/90/100%
- Output length controls (task-specific max_tokens)
- Progressive enhancement (Haiku draft -> Sonnet if quality < threshold)

## What to Build

### Backend
1. **backend/app/modules/llm_orchestration/__init__.py**
2. **backend/app/modules/llm_orchestration/router_config.py** — Model routing rules: task_type -> model selection, fallback chain
3. **backend/app/modules/llm_orchestration/orchestrator.py** — Central orchestrator:
   - generate(task_type, prompt, context, options) -> response
   - Route to correct model based on task type
   - Handle streaming (SSE events)
   - Retry with fallback on failure
   - Track tokens and cost per request
4. **backend/app/modules/llm_orchestration/providers/base.py** — Abstract LLM provider interface
5. **backend/app/modules/llm_orchestration/providers/anthropic.py** — Claude API client (Opus, Sonnet, Haiku)
6. **backend/app/modules/llm_orchestration/providers/openai.py** — OpenAI client (GPT-4, GPT-4 Mini)
7. **backend/app/modules/llm_orchestration/cache.py** — Semantic caching: hash prompts, store in Redis, TTL per task type
8. **backend/app/modules/llm_orchestration/cost_tracker.py** — Token counting, USD cost calculation per model, per-org budget tracking, alerts
9. **backend/app/modules/llm_orchestration/quality.py** — Post-generation quality checks: readability, plagiarism detection placeholder, hallucination detection placeholder

### Tests
10. **backend/tests/unit/test_model_routing.py** — Test task-to-model routing
11. **backend/tests/unit/test_cost_tracker.py** — Test token counting, budget alerts
12. **backend/tests/unit/test_semantic_cache.py** — Test cache hit/miss, TTL
13. **backend/tests/integration/test_llm_orchestration.py** — Test generation flow with mocked providers

## Database Tables (from W02, read-only)
agent_tasks (for logging), agent_budgets (for cost control)

## Commit Convention
`feat(llm): implement LLM orchestration with model routing, caching, and cost management`
