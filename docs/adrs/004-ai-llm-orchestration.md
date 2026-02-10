# ADR-004: AI/LLM Orchestration Strategy

**Date**: 2025-06-20
**Status**: Accepted

## Context

AI capabilities are central to SelfPublisherForge. At least 10 of the platform's 29 modules rely on large language model (LLM) calls for content generation, analysis, or decision support:

- **AI Writing Studio**: Manuscript drafting, chapter generation, writing prompts
- **AI Editing**: Style correction, readability improvement, consistency checks
- **AI Outline**: Book structure generation from research and genre conventions
- **AI Cover Design**: Image prompt generation for cover concepts and design analysis
- **Style Cloning Engine**: Voice fingerprint analysis and writing conformity scoring
- **Knowledge Vault**: AI-assisted note extraction and research summarization
- **Marketing Launch Planner**: Email copy, social media content, blurb generation
- **Product Page Lab**: A/B test copy variants, mobile-optimized blurb generation
- **Advertising Intelligence**: Ad creative generation, keyword expansion
- **Agent System**: Autonomous task execution with LLM-powered reasoning

These modules have different requirements:

| Requirement | Details |
|-------------|---------|
| **Quality** | Manuscript generation and style cloning demand the highest quality output. Marketing copy tolerates more variability. |
| **Latency** | Interactive features (writing suggestions, chat) need sub-5-second responses. Batch operations (full chapter generation) can tolerate minutes. |
| **Cost** | AI costs are a significant operational expense. Per-request cost tracking and optimization are essential for sustainable unit economics. |
| **Reliability** | A single provider outage should not disable all AI features. Graceful degradation is required. |
| **Streaming** | Long-form generation (manuscripts, outlines) must stream tokens to the user in real-time via WebSocket to provide immediate feedback. |
| **Context windows** | Manuscript editing and style analysis require large context windows (100K+ tokens) for full-document processing. |

### Approaches considered

| Option | Pros | Cons |
|--------|------|------|
| **Direct SDK calls per module** | Simple, no abstraction overhead, each module controls its own prompts | No shared retry/fallback logic, no cost tracking, no caching, provider coupling in 10+ modules, changing providers requires touching every module |
| **LangChain orchestration** | Feature-rich (chains, agents, memory, tools), large community | Heavy abstraction layer, opinionated patterns that may not fit all use cases, version churn, adds significant dependency surface, unnecessary complexity for our routing needs |
| **Custom abstraction layer** | Tailored to our specific needs (routing, fallback, caching, cost tracking), no unnecessary abstractions, full control | Must be built and maintained in-house, no community support for the abstraction itself |

## Decision

We will build a **custom multi-provider LLM orchestration layer** (`backend/app/modules/llm_orchestration/`) that provides a unified interface for all AI-consuming modules, with Anthropic Claude as the primary provider and OpenAI GPT as the fallback.

### Architecture

The orchestration layer consists of four components:

#### 1. Provider abstraction

A `BaseLLMProvider` interface defines the contract for all LLM providers:

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse: ...

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncGenerator[LLMChunk, None]: ...

    @abstractmethod
    async def count_tokens(self, text: str, model: str) -> int: ...
```

Concrete implementations (`AnthropicProvider`, `OpenAIProvider`) wrap each provider's SDK and normalize responses into a common `LLMResponse` schema that includes token counts, latency, cost, and model metadata.

#### 2. Model router

The model router selects the appropriate provider and model based on the request's requirements:

| Criterion | Logic |
|-----------|-------|
| **Task type** | Each module declares its task type (e.g., `creative_writing`, `analysis`, `summarization`, `code_generation`). Task types map to preferred model configurations. |
| **Quality tier** | `high` routes to Claude Opus/Sonnet for maximum quality. `standard` routes to Claude Haiku or GPT-4o-mini for cost efficiency. `fast` routes to the lowest-latency available model. |
| **Context size** | Requests exceeding 100K tokens are automatically routed to models with sufficient context windows (Claude with 200K context). |
| **Cost budget** | Organization-level and request-level cost caps prevent runaway spending. If a request would exceed the budget, it is rejected with a clear error rather than silently degraded. |
| **Availability** | If the primary provider returns errors (HTTP 5xx, timeout, rate limit), the router falls back to the secondary provider with appropriate model mapping (e.g., Claude Sonnet falls back to GPT-4o). |

#### 3. Response cache

Deterministic requests (same prompt, same model, same parameters) are cached in Redis with configurable TTL. Cache keys are derived from a hash of the request parameters. This is especially valuable for:

- Repeated style analysis of the same text
- Keyword expansion with identical seed terms
- Template-based generation with the same inputs

Non-deterministic requests (creative generation with `temperature > 0`) skip the cache by default but can opt in if the caller accepts cached results.

#### 4. Cost tracker

Every LLM request logs:

- Provider and model used
- Input and output token counts
- Calculated cost (based on current provider pricing)
- Latency (time to first token, total time)
- Organization ID and module that initiated the request
- Whether the result was served from cache

This data is stored in a `llm_usage` table and exposed via the usage tracking module for billing, analytics, and cost optimization.

### Provider configuration

**Primary: Anthropic Claude**

- Claude Opus -- high-quality creative writing, complex analysis, agent reasoning
- Claude Sonnet -- general-purpose generation, marketing copy, editing
- Claude Haiku -- fast classification, summarization, simple extraction

**Fallback: OpenAI GPT**

- GPT-4o -- maps to Claude Sonnet use cases during Anthropic outages
- GPT-4o-mini -- maps to Claude Haiku use cases, cost-optimized tasks

**Fallback triggers**:
- HTTP 500/502/503 from the primary provider
- Request timeout exceeding configured threshold (default: 30 seconds)
- Rate limit response (HTTP 429) after retry exhaustion
- Explicit provider health check failure (checked every 60 seconds)

When fallback is triggered, the router logs the event, adjusts the health score for the primary provider, and temporarily increases fallback routing until the primary recovers. This circuit-breaker pattern prevents cascading failures.

### Module integration

Modules interact with the orchestration layer through a simple service interface:

```python
# In any module's service layer:
from app.modules.llm_orchestration.service import llm_service

response = await llm_service.generate(
    task_type="creative_writing",
    quality="high",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    org_id=org_id,
    max_tokens=4096,
    stream=False,
)
```

Modules declare **what** they need (task type, quality level, token budget) rather than **which** provider or model to use. The orchestration layer handles provider selection, fallback, caching, and cost tracking transparently.

## Consequences

### Positive

- **Provider independence**: All 10+ AI-consuming modules interact with a single service interface. Switching or adding a provider (e.g., Google Gemini, Mistral, a self-hosted model) requires implementing one new `BaseLLMProvider` subclass and updating the router configuration -- zero changes to consuming modules.
- **Automatic failover**: Provider outages degrade gracefully. If Anthropic is down, users experience slightly different output quality (OpenAI fallback) rather than complete feature unavailability. The circuit-breaker pattern prevents repeated failed requests.
- **Cost visibility and control**: Per-request cost tracking enables accurate per-organization billing, identifies cost optimization opportunities (e.g., a module using high-quality models for simple classification tasks), and supports organization-level spending caps.
- **Response caching**: Caching identical requests reduces latency and cost for repeated operations. Style analysis of the same manuscript, keyword expansion with the same seeds, and template-based generation all benefit significantly.
- **Centralized prompt management**: While each module defines its own prompts, the orchestration layer can enforce guardrails (maximum token budgets, required system prompts, content filtering) consistently across all modules.
- **Observability**: Centralized logging of all LLM interactions provides a single pane of glass for monitoring AI feature health, latency percentiles, error rates, and cost trends.

### Negative

- **Custom code maintenance**: Unlike using LangChain or another framework, the orchestration layer must be maintained in-house. New provider SDKs, pricing changes, and API updates require manual integration work.
- **Abstraction limitations**: The common `LLMRequest`/`LLMResponse` interface may not expose provider-specific features (e.g., Anthropic's tool use, OpenAI's function calling, vision capabilities) without extending the abstraction. This is mitigated by allowing modules to pass provider-specific parameters via an `extra_params` dictionary, but this reduces the abstraction's value for those use cases.
- **Fallback quality variance**: OpenAI and Anthropic models have different strengths and writing styles. A response generated by the fallback provider may differ noticeably from the primary provider, particularly for style-sensitive tasks like manuscript generation. Users may notice quality shifts during provider outages.
- **Cache invalidation complexity**: Determining when to invalidate cached responses (after prompt template changes, model version updates) requires careful cache key design and manual invalidation triggers. Stale cached responses could serve outdated outputs.
- **Single orchestration bottleneck**: All AI requests flow through one service. A bug in the orchestration layer could disable AI features across all 10+ modules simultaneously. This is mitigated by comprehensive test coverage and the ability for modules to bypass the orchestration layer in emergency situations via direct SDK access (documented as an escape hatch, not standard practice).
- **Model pricing drift**: The cost tracker relies on hardcoded pricing tables that must be updated when providers change their pricing. Stale pricing data would produce inaccurate cost reports. A periodic pricing verification task mitigates this but does not eliminate the risk entirely.
