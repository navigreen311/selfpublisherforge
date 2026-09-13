"""Unit tests for AI generator: prompt construction, model resolution, streaming."""

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.ai_writing.generator import (
    _run_quality_checks,
    build_messages,
    generate_stream,
    generate_sync,
    resolve_model,
)
from app.modules.ai_writing.prompts import PROMPT_REGISTRY, get_prompt
from app.modules.ai_writing.schemas import (
    GenerateRequest,
    GenerationType,
)

# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


class TestBuildMessages:
    def _make_request(self, gen_type: str = "chapter", **overrides) -> GenerateRequest:
        defaults = {
            "generation_type": gen_type,
            "project_id": uuid.uuid4(),
            "instructions": "Write a compelling opening.",
            "context": {"genre": "fantasy", "chapter_title": "The Beginning"},
            "model_preference": "auto",
            "stream": True,
            "quality_checks": [],
        }
        defaults.update(overrides)
        return GenerateRequest(**defaults)

    def test_returns_system_and_user_messages(self):
        request = self._make_request()
        messages = build_messages(request)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_system_message_contains_genre(self):
        request = self._make_request(context={"genre": "science fiction"})
        messages = build_messages(request)
        assert "science fiction" in messages[0]["content"].lower()

    def test_user_message_contains_instructions(self):
        request = self._make_request(instructions="Include a dragon.")
        messages = build_messages(request)
        assert "dragon" in messages[1]["content"].lower()

    def test_all_generation_types_have_prompts(self):
        """Every GenerationType should have a registered prompt builder."""
        for gen_type in GenerationType:
            assert gen_type.value in PROMPT_REGISTRY, f"Missing prompt for generation type: {gen_type.value}"


class TestGetPrompt:
    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown generation type"):
            get_prompt("nonexistent_type", {})

    def test_outline_returns_tuple(self):
        system, user = get_prompt("outline", {"premise": "A hero's journey"})
        assert isinstance(system, str)
        assert isinstance(user, str)
        assert "outline" in user.lower() or "chapter" in user.lower()

    def test_blurb_prompt_mentions_blurb(self):
        system, user = get_prompt("blurb", {"title": "The Lost City"})
        assert "blurb" in user.lower() or "description" in user.lower()

    def test_title_suggestions_returns_json_instruction(self):
        system, user = get_prompt("title_suggestions", {"synopsis": "A story about..."})
        assert "json" in user.lower()

    def test_continue_writing_includes_existing_text(self):
        _, user = get_prompt("continue_writing", {"existing_text": "Once upon a time"})
        assert "Once upon a time" in user

    def test_edit_selection_includes_selected_text(self):
        _, user = get_prompt("edit_selection", {"selected_text": "bad prose here"})
        assert "bad prose here" in user

    def test_tone_adjustment_includes_target_tone(self):
        _, user = get_prompt("tone_adjustment", {"target_tone": "humorous"})
        assert "humorous" in user


# ---------------------------------------------------------------------------
# Model resolution
# ---------------------------------------------------------------------------


class TestResolveModel:
    def test_auto_returns_default(self):
        model = resolve_model("auto")
        assert "claude" in model.lower() or model != ""

    def test_claude_returns_claude_model(self):
        model = resolve_model("claude")
        assert "claude" in model.lower()

    def test_gpt4_returns_openai_model(self):
        model = resolve_model("gpt4")
        assert "gpt" in model.lower()

    def test_gemini_returns_gemini_model(self):
        model = resolve_model("gemini")
        assert "gemini" in model.lower()

    def test_unknown_returns_default(self):
        model = resolve_model("unknown_model")
        assert model != ""


# ---------------------------------------------------------------------------
# Quality checks
# ---------------------------------------------------------------------------


class TestQualityChecks:
    SAMPLE_TEXT = "The quick brown fox jumps over the lazy dog. " "Simple sentences are easy to read."

    def test_readability_check(self):
        results = _run_quality_checks(self.SAMPLE_TEXT, ["readability"])
        assert "readability" in results
        assert "flesch_kincaid_grade" in results["readability"]
        assert "reading_level" in results["readability"]

    def test_word_count_check(self):
        results = _run_quality_checks(self.SAMPLE_TEXT, ["word_count"])
        assert "word_count" in results
        assert results["word_count"] > 0

    def test_grammar_check_placeholder(self):
        results = _run_quality_checks(self.SAMPLE_TEXT, ["grammar"])
        assert "grammar" in results
        assert results["grammar"]["status"] == "passed"

    def test_empty_checks(self):
        results = _run_quality_checks(self.SAMPLE_TEXT, [])
        assert results == {}

    def test_multiple_checks(self):
        results = _run_quality_checks(self.SAMPLE_TEXT, ["readability", "word_count", "grammar"])
        assert len(results) == 3


# ---------------------------------------------------------------------------
# Streaming (mocked LLM)
# ---------------------------------------------------------------------------


class TestGenerateStream:
    def _make_request(self, **overrides) -> GenerateRequest:
        defaults = {
            "generation_type": "chapter",
            "project_id": uuid.uuid4(),
            "instructions": "Write something.",
            "context": {},
            "model_preference": "auto",
            "stream": True,
            "quality_checks": ["word_count"],
        }
        defaults.update(overrides)
        return GenerateRequest(**defaults)

    @pytest.mark.asyncio
    async def test_stream_yields_token_events(self):
        """Mocked stream should yield token events."""

        async def mock_llm_stream(*args, **kwargs):
            for chunk in ["Hello ", "world ", "!"]:
                yield chunk

        with patch(
            "app.modules.ai_writing.generator._call_llm_stream",
            side_effect=mock_llm_stream,
        ):
            request = self._make_request()
            events = []
            async for event in generate_stream(request):
                events.append(event)

            # Should have token events + quality + complete
            token_events = [e for e in events if e.startswith("event: token")]
            assert len(token_events) == 3

    @pytest.mark.asyncio
    async def test_stream_ends_with_complete_event(self):
        async def mock_llm_stream(*args, **kwargs):
            yield "Done"

        with patch(
            "app.modules.ai_writing.generator._call_llm_stream",
            side_effect=mock_llm_stream,
        ):
            request = self._make_request(quality_checks=[])
            events = []
            async for event in generate_stream(request):
                events.append(event)

            complete_events = [e for e in events if e.startswith("event: complete")]
            assert len(complete_events) == 1

            # Parse the complete event data
            data_line = complete_events[0].split("data: ")[1].strip()
            data = json.loads(data_line)
            assert "request_id" in data
            assert data["content"] == "Done"

    @pytest.mark.asyncio
    async def test_stream_includes_quality_event(self):
        async def mock_llm_stream(*args, **kwargs):
            yield "Some text here."

        with patch(
            "app.modules.ai_writing.generator._call_llm_stream",
            side_effect=mock_llm_stream,
        ):
            request = self._make_request(quality_checks=["readability"])
            events = []
            async for event in generate_stream(request):
                events.append(event)

            quality_events = [e for e in events if e.startswith("event: quality")]
            assert len(quality_events) == 1


# ---------------------------------------------------------------------------
# Sync generation (mocked LLM)
# ---------------------------------------------------------------------------


class TestGenerateSync:
    @pytest.mark.asyncio
    async def test_returns_generate_response(self):
        with patch(
            "app.modules.ai_writing.generator._call_llm",
            new_callable=AsyncMock,
            return_value="Generated content here.",
        ):
            request = GenerateRequest(
                generation_type="blurb",
                project_id=uuid.uuid4(),
                instructions="Write a blurb.",
                context={},
                model_preference="auto",
                stream=False,
                quality_checks=[],
            )
            response = await generate_sync(request)
            assert response.content == "Generated content here."
            assert response.generation_type == GenerationType.blurb

    @pytest.mark.asyncio
    async def test_includes_quality_results(self):
        with patch(
            "app.modules.ai_writing.generator._call_llm",
            new_callable=AsyncMock,
            return_value="The quick brown fox jumps over the lazy dog.",
        ):
            request = GenerateRequest(
                generation_type="chapter",
                project_id=uuid.uuid4(),
                instructions="Write.",
                context={},
                model_preference="auto",
                stream=False,
                quality_checks=["word_count"],
            )
            response = await generate_sync(request)
            assert "word_count" in response.quality_results
