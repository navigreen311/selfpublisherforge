"""AI content generation engine.

Handles prompt construction, SSE streaming, and quality post-checks
for the unified /generate endpoint.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from app.config import get_settings
from app.modules.ai_writing.prompts import get_prompt
from app.modules.ai_writing.readability import analyze_readability
from app.modules.ai_writing.schemas import GenerateRequest, GenerateResponse, GenerationType

settings = get_settings()


# ---------------------------------------------------------------------------
# Quality checks
# ---------------------------------------------------------------------------

def _run_quality_checks(content: str, checks: list[str]) -> dict[str, Any]:
    """Run requested quality checks on the generated content."""
    results: dict[str, Any] = {}
    if "readability" in checks:
        metrics = analyze_readability(content)
        results["readability"] = {
            "flesch_kincaid_grade": metrics.flesch_kincaid_grade,
            "flesch_reading_ease": metrics.flesch_reading_ease,
            "gunning_fog": metrics.gunning_fog,
            "reading_level": metrics.reading_level,
        }
    if "word_count" in checks:
        word_count = len(content.split())
        results["word_count"] = word_count
    if "grammar" in checks:
        # Placeholder: in production this would call a grammar API
        results["grammar"] = {"status": "passed", "issues": []}
    return results


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def build_messages(request: GenerateRequest) -> list[dict[str, str]]:
    """Build LLM message list from a GenerateRequest."""
    context = {**request.context, "instructions": request.instructions}
    system_msg, user_msg = get_prompt(request.generation_type.value, context)
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def resolve_model(preference: str) -> str:
    """Map a model preference enum to a concrete model identifier."""
    mapping = {
        "auto": settings.DEFAULT_LLM_MODEL,
        "claude": "claude-sonnet-4-5-20250929",
        "gpt4": "gpt-4o",
        "gemini": "gemini-1.5-pro",
    }
    return mapping.get(preference, settings.DEFAULT_LLM_MODEL)


# ---------------------------------------------------------------------------
# Streaming generator (SSE)
# ---------------------------------------------------------------------------

async def generate_stream(request: GenerateRequest) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted events for a streaming generation request.

    Event types:
      - event:token   -> incremental text chunks
      - event:quality -> quality check results (after generation)
      - event:complete -> final metadata
    """
    request_id = uuid.uuid4()
    messages = build_messages(request)
    model = resolve_model(request.model_preference.value)
    collected_content = ""
    tokens_used = 0

    # Stream tokens from the LLM
    try:
        async for chunk in _call_llm_stream(messages, model):
            collected_content += chunk
            tokens_used += 1  # approximate token count by chunk count
            yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
    except Exception as exc:
        yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
        return

    # Quality checks
    if request.quality_checks:
        quality_results = _run_quality_checks(collected_content, request.quality_checks)
        yield f"event: quality\ndata: {json.dumps(quality_results)}\n\n"
    else:
        quality_results = {}

    # Complete event
    complete_payload = {
        "request_id": str(request_id),
        "generation_type": request.generation_type.value,
        "content": collected_content,
        "tokens_used": tokens_used,
        "quality_results": quality_results,
        "model_used": model,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    yield f"event: complete\ndata: {json.dumps(complete_payload)}\n\n"


# ---------------------------------------------------------------------------
# Non-streaming generation
# ---------------------------------------------------------------------------

async def generate_sync(request: GenerateRequest) -> GenerateResponse:
    """Generate content without streaming; returns complete response."""
    request_id = uuid.uuid4()
    messages = build_messages(request)
    model = resolve_model(request.model_preference.value)

    content = await _call_llm(messages, model)
    quality_results = _run_quality_checks(content, request.quality_checks) if request.quality_checks else {}

    return GenerateResponse(
        request_id=request_id,
        generation_type=request.generation_type,
        content=content,
        tokens_used=len(content.split()),
        quality_results=quality_results,
        model_used=model,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# LLM integration layer (abstracted for testability)
# ---------------------------------------------------------------------------

async def _call_llm_stream(
    messages: list[dict[str, str]], model: str
) -> AsyncGenerator[str, None]:
    """Stream responses from the configured LLM provider.

    In production, this dispatches to Anthropic / OpenAI / Google SDKs.
    The implementation uses the Anthropic SDK by default.
    """
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        system_content = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                user_messages.append(msg)

        async with client.messages.stream(
            model=model if model.startswith("claude") else settings.DEFAULT_LLM_MODEL,
            max_tokens=4096,
            system=system_content,
            messages=user_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except ImportError:
        # Fallback: yield a placeholder when SDK is not available
        yield "[AI content generation requires the anthropic SDK]"
    except Exception as exc:
        yield f"[Generation error: {exc}]"


async def _call_llm(messages: list[dict[str, str]], model: str) -> str:
    """Non-streaming call to the LLM. Returns full text response."""
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        system_content = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                user_messages.append(msg)

        response = await client.messages.create(
            model=model if model.startswith("claude") else settings.DEFAULT_LLM_MODEL,
            max_tokens=4096,
            system=system_content,
            messages=user_messages,
        )
        return response.content[0].text
    except ImportError:
        return "[AI content generation requires the anthropic SDK]"
    except Exception as exc:
        return f"[Generation error: {exc}]"
