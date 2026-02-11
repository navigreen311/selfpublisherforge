"""AI content generation engine.

Handles prompt construction, SSE streaming, and quality post-checks
for the unified /generate endpoint.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from app.config import get_settings
from app.modules.ai_writing.prompts import get_prompt
from app.modules.ai_writing.readability import analyze_readability
from app.modules.ai_writing.schemas import GenerateRequest, GenerateResponse

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# LLM SDK availability check (fail fast at import time)
# ---------------------------------------------------------------------------

_LLM_PROVIDER: str  # "anthropic" | "openai"

try:
    import anthropic  # noqa: F401
    _LLM_PROVIDER = "anthropic"
    logger.info("Using Anthropic SDK for LLM generation")
except ImportError:
    try:
        import openai  # noqa: F401
        _LLM_PROVIDER = "openai"
        logger.info("Anthropic SDK not found; falling back to OpenAI SDK for LLM generation")
    except ImportError:
        raise RuntimeError(
            "No LLM SDK available. Install at least one of: "
            "'pip install anthropic' or 'pip install openai'. "
            "The AI writing module requires an LLM provider to function."
        )


# ---------------------------------------------------------------------------
# Grammar checking (rule-based)
# ---------------------------------------------------------------------------

# Common confused-word patterns: (regex, description, suggestion)
_CONFUSED_WORDS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"\btheir\s+(is|was|are|were|has|have|will|shall|can|could|would|should)\b", re.IGNORECASE),
        "Possible confused word: 'their' (possessive) may should be 'there' (location/existence)",
        "there",
    ),
    (
        re.compile(r"\bthere\s+(car|house|book|dog|cat|name|idea|plan|work|team|friend|mother|father)\b", re.IGNORECASE),
        "Possible confused word: 'there' may should be 'their' (possessive)",
        "their",
    ),
    (
        re.compile(r"\byour\s+(welcome|right|wrong|going|coming|doing|making|getting)\b", re.IGNORECASE),
        "Possible confused word: 'your' (possessive) may should be 'you're' (you are)",
        "you're",
    ),
    (
        re.compile(r"\bits\s+a\s+(good|bad|great|nice|long|short|big|small)\b", re.IGNORECASE),
        "Check usage: 'its' (possessive) vs. \"it's\" (it is)",
        "it's",
    ),
    (
        re.compile(r"\bthen\s+(I|you|he|she|we|they)\b"),
        "Possible confused word: 'then' (time) may should be 'than' (comparison)",
        "than",
    ),
    (
        re.compile(r"\baffect\b(?=\s+(?:is|was|the))", re.IGNORECASE),
        "Possible confused word: 'affect' (verb) may should be 'effect' (noun)",
        "effect",
    ),
    (
        re.compile(r"\beffect\b(?=\s+(?:a change|the outcome|him|her|them|us|me|you))", re.IGNORECASE),
        "Possible confused word: 'effect' (noun) may should be 'affect' (verb)",
        "affect",
    ),
    (
        re.compile(r"\balot\b", re.IGNORECASE),
        "'alot' is not a word",
        "a lot",
    ),
    (
        re.compile(r"\bcould of\b", re.IGNORECASE),
        "'could of' should be 'could have'",
        "could have",
    ),
    (
        re.compile(r"\bshould of\b", re.IGNORECASE),
        "'should of' should be 'should have'",
        "should have",
    ),
    (
        re.compile(r"\bwould of\b", re.IGNORECASE),
        "'would of' should be 'would have'",
        "would have",
    ),
    (
        re.compile(r"\bmight of\b", re.IGNORECASE),
        "'might of' should be 'might have'",
        "might have",
    ),
    (
        re.compile(r"\bdefinately\b", re.IGNORECASE),
        "Misspelling of 'definitely'",
        "definitely",
    ),
    (
        re.compile(r"\boccured\b", re.IGNORECASE),
        "Misspelling of 'occurred'",
        "occurred",
    ),
    (
        re.compile(r"\brecieve\b", re.IGNORECASE),
        "Misspelling of 'receive'",
        "receive",
    ),
    (
        re.compile(r"\bseperate\b", re.IGNORECASE),
        "Misspelling of 'separate'",
        "separate",
    ),
    (
        re.compile(r"\boccasion(?:al)?ly\b"),
        "Misspelling of 'occasionally'",
        "occasionally",
    ),
    (
        re.compile(r"\buntill?\b(?!$)", re.IGNORECASE),
        "Misspelling of 'until'",
        "until",
    ),
    (
        re.compile(r"\bneccessary\b", re.IGNORECASE),
        "Misspelling of 'necessary'",
        "necessary",
    ),
    (
        re.compile(r"\baccommodate\b"),
        # This one is correct; skip — we only flag the misspelling
        "",
        "",
    ),
    (
        re.compile(r"\baccomodate\b", re.IGNORECASE),
        "Misspelling of 'accommodate'",
        "accommodate",
    ),
    (
        re.compile(r"\bwich\b", re.IGNORECASE),
        "Misspelling of 'which'",
        "which",
    ),
    (
        re.compile(r"\bteh\b", re.IGNORECASE),
        "Misspelling of 'the'",
        "the",
    ),
]


def _check_grammar(content: str) -> dict[str, Any]:
    """Run rule-based grammar checks and return issues with positions.

    Returns a dict with:
      - status: "passed" if no issues, "issues_found" otherwise
      - issues: list of dicts each with type, message, position, length, suggestion
      - issue_count: total number of issues found
    """
    if not content or not content.strip():
        return {"status": "passed", "issues": [], "issue_count": 0}

    issues: list[dict[str, Any]] = []

    # --- Rule 1: Double spaces (outside of line-leading indentation) ---
    for match in re.finditer(r"(?<=\S)  +", content):
        issues.append({
            "type": "whitespace",
            "message": "Multiple consecutive spaces",
            "position": match.start(),
            "length": len(match.group()),
            "suggestion": " ",
            "context": _excerpt(content, match.start(), match.end()),
        })

    # --- Rule 2: Missing capitalization after sentence-ending punctuation ---
    # Matches ". <lowercase>" but not inside abbreviations like "e.g." or "Dr."
    for match in re.finditer(r'([.!?])\s+([a-z])', content):
        # Skip common abbreviations that precede the period
        pre_text = content[max(0, match.start() - 5):match.start()]
        if re.search(r'\b(?:Mr|Mrs|Ms|Dr|Prof|Jr|Sr|St|vs|etc|e\.g|i\.e|a\.m|p\.m)\s*$', pre_text, re.IGNORECASE):
            continue
        issues.append({
            "type": "capitalization",
            "message": f"Sentence after '{match.group(1)}' should start with a capital letter",
            "position": match.start(2),
            "length": 1,
            "suggestion": match.group(2).upper(),
            "context": _excerpt(content, match.start(), match.end()),
        })

    # --- Rule 3: Repeated words (e.g., "the the") ---
    for match in re.finditer(r'\b(\w+)\s+\1\b', content, re.IGNORECASE):
        word = match.group(1).lower()
        # Skip intentional repetitions common in prose (e.g., "had had", "that that")
        if word in {"had", "that", "very", "so", "no", "bye"}:
            continue
        issues.append({
            "type": "repeated_word",
            "message": f"Repeated word: '{match.group(1)}'",
            "position": match.start(),
            "length": len(match.group()),
            "suggestion": match.group(1),
            "context": _excerpt(content, match.start(), match.end()),
        })

    # --- Rule 4: Missing punctuation at end of paragraph/sentence ---
    # Split into paragraphs and check if non-empty ones end without terminal punctuation
    paragraphs = content.split("\n")
    offset = 0
    for para in paragraphs:
        stripped = para.rstrip()
        if stripped and len(stripped) > 20:  # Only flag substantial lines
            # Skip lines that look like headings, list items, or dialogue tags
            if not re.match(r'^[\s]*[-*#>\d]', stripped):
                if not re.search(r'[.!?"\'\u2019\u201D)\]]\s*$', stripped):
                    end_pos = offset + len(stripped) - 1
                    issues.append({
                        "type": "punctuation",
                        "message": "Paragraph/sentence may be missing ending punctuation",
                        "position": end_pos,
                        "length": 1,
                        "suggestion": ".",
                        "context": _excerpt(content, max(0, end_pos - 30), end_pos + 1),
                    })
        offset += len(para) + 1  # +1 for the newline

    # --- Rule 5: Confused words and common misspellings ---
    for pattern, description, suggestion in _CONFUSED_WORDS:
        if not description:  # Skip entries with no error message (correct spellings)
            continue
        for match in pattern.finditer(content):
            issues.append({
                "type": "confused_word",
                "message": description,
                "position": match.start(),
                "length": len(match.group()),
                "suggestion": suggestion,
                "context": _excerpt(content, match.start(), match.end()),
            })

    # Sort issues by position for consistent output
    issues.sort(key=lambda x: x["position"])

    status = "passed" if not issues else "issues_found"
    return {"status": status, "issues": issues, "issue_count": len(issues)}


def _excerpt(text: str, start: int, end: int, margin: int = 20) -> str:
    """Return a short excerpt of text around a match for context."""
    ctx_start = max(0, start - margin)
    ctx_end = min(len(text), end + margin)
    excerpt = text[ctx_start:ctx_end]
    prefix = "..." if ctx_start > 0 else ""
    suffix = "..." if ctx_end < len(text) else ""
    return f"{prefix}{excerpt}{suffix}"


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
        results["grammar"] = _check_grammar(content)
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
    except (ConnectionError, TimeoutError, ValueError) as exc:
        logger.error("Stream generation failed: %s", exc, exc_info=True)
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
        "created_at": datetime.now(UTC).isoformat(),
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
        created_at=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# LLM integration helpers
# ---------------------------------------------------------------------------

def _split_messages(messages: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    """Separate system content from user/assistant messages."""
    system_content = ""
    user_messages: list[dict[str, str]] = []
    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
        else:
            user_messages.append(msg)
    return system_content, user_messages


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

async def _anthropic_stream(
    messages: list[dict[str, str]], model: str
) -> AsyncGenerator[str, None]:
    """Stream responses via the Anthropic SDK."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    system_content, user_messages = _split_messages(messages)

    async with client.messages.stream(
        model=model if model.startswith("claude") else settings.DEFAULT_LLM_MODEL,
        max_tokens=4096,
        system=system_content,
        messages=user_messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def _anthropic_call(messages: list[dict[str, str]], model: str) -> str:
    """Non-streaming call via the Anthropic SDK."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    system_content, user_messages = _split_messages(messages)

    response = await client.messages.create(
        model=model if model.startswith("claude") else settings.DEFAULT_LLM_MODEL,
        max_tokens=4096,
        system=system_content,
        messages=user_messages,
    )
    return response.content[0].text


# ---------------------------------------------------------------------------
# OpenAI provider (fallback)
# ---------------------------------------------------------------------------

async def _openai_stream(
    messages: list[dict[str, str]], model: str
) -> AsyncGenerator[str, None]:
    """Stream responses via the OpenAI SDK."""
    import openai

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    # Map Claude model names to OpenAI equivalents when needed
    oai_model = model if model.startswith("gpt") else "gpt-4o"

    response = await client.chat.completions.create(
        model=oai_model,
        max_tokens=4096,
        messages=messages,  # OpenAI accepts system role directly
        stream=True,
    )
    async for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


async def _openai_call(messages: list[dict[str, str]], model: str) -> str:
    """Non-streaming call via the OpenAI SDK."""
    import openai

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    oai_model = model if model.startswith("gpt") else "gpt-4o"

    response = await client.chat.completions.create(
        model=oai_model,
        max_tokens=4096,
        messages=messages,
    )
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# LLM integration layer (abstracted for testability)
# ---------------------------------------------------------------------------

async def _call_llm_stream(
    messages: list[dict[str, str]], model: str
) -> AsyncGenerator[str, None]:
    """Stream responses from the configured LLM provider.

    Dispatches to Anthropic or OpenAI based on SDK availability
    (determined at module import time).
    """
    try:
        if _LLM_PROVIDER == "anthropic":
            async for text in _anthropic_stream(messages, model):
                yield text
        else:
            async for text in _openai_stream(messages, model):
                yield text
    except (ConnectionError, TimeoutError) as exc:
        logger.error("LLM stream network error: %s", exc, exc_info=True)
        yield f"[Generation error: {exc}]"
    except ValueError as exc:
        logger.error("LLM stream value error: %s", exc, exc_info=True)
        yield f"[Generation error: {exc}]"


async def _call_llm(messages: list[dict[str, str]], model: str) -> str:
    """Non-streaming call to the LLM. Returns full text response."""
    try:
        if _LLM_PROVIDER == "anthropic":
            return await _anthropic_call(messages, model)
        return await _openai_call(messages, model)
    except (ConnectionError, TimeoutError) as exc:
        logger.error("LLM call network error: %s", exc, exc_info=True)
        return f"[Generation error: {exc}]"
    except ValueError as exc:
        logger.error("LLM call value error: %s", exc, exc_info=True)
        return f"[Generation error: {exc}]"
