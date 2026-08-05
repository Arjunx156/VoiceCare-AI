"""The two ways a turn used to fail without anyone noticing.

Both regressions here degraded silently: the pipeline kept answering the
customer, so nothing looked broken from the outside. One capped every
resolution's confidence at 0.3 and escalated the whole queue; the other threw
away every anonymous caller's ticket. Neither raised, neither failed a test.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAnonymousPlaceholderPhone:
    """Anonymous callers get a synthetic phone; it has to fit the column."""

    def test_placeholder_fits_the_phone_column(self):
        """The anonymous phone fits varchar(20), or every such ticket is lost."""
        from app.agents.pipeline import _anon_phone
        from app.db.models import User

        limit = User.__table__.c.phone.type.length
        # A full UUID4 is the widest session id the frontend ever sends.
        assert len(_anon_phone(str(uuid.uuid4()))) <= limit

    def test_placeholder_keeps_the_anon_prefix(self):
        """Ghost rows stay filterable — customers.py excludes them by prefix."""
        from app.agents.pipeline import _anon_phone

        assert _anon_phone(str(uuid.uuid4())).startswith("anon-")

    def test_placeholder_is_stable_across_turns_of_one_conversation(self):
        """One ghost user per conversation, however many times the caller speaks."""
        from app.agents.pipeline import _anon_phone

        session_id = str(uuid.uuid4())
        assert _anon_phone(session_id) == _anon_phone(session_id)

    def test_distinct_conversations_get_distinct_placeholders(self):
        """Two anonymous callers must not collide on the unique phone column."""
        from app.agents.pipeline import _anon_phone

        assert _anon_phone(str(uuid.uuid4())) != _anon_phone(str(uuid.uuid4()))


class TestThinkingIsDisabled:
    """Thinking tokens come out of max_output_tokens, truncating the JSON."""

    @pytest.mark.asyncio
    async def test_call_passes_a_zero_thinking_budget(self):
        """Every Gemini call sends thinking_budget=0, or its JSON gets truncated."""
        from app.services.gemini_service import GeminiService

        svc = GeminiService.__new__(GeminiService)
        response = MagicMock(text='{"ok": true}', candidates=[])
        svc.client = MagicMock()
        svc.client.aio.models.generate_content = AsyncMock(return_value=response)

        await svc._call_gemini("prompt", max_output_tokens=640)

        config = svc.client.aio.models.generate_content.await_args.kwargs["config"]
        assert config.thinking_config.thinking_budget == 0

    def test_the_sdk_in_use_supports_a_thinking_budget(self):
        """The installed SDK accepts thinking_config — the retired one silently didn't."""
        from google.genai import types

        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )
        assert config.thinking_config.thinking_budget == 0


class TestTruncatedJsonIsReported:
    """A truncated candidate returns HTTP 200, so it must be named explicitly."""

    def test_unparseable_output_is_logged_before_it_becomes_a_fallback(self):
        """Bad LLM JSON is logged with a preview, not swallowed into a canned reply."""
        import json

        from app.services.gemini_service import GeminiService

        svc = GeminiService.__new__(GeminiService)
        truncated = '{"recommended_action": "Track", "resolution_summ'

        with patch("app.services.gemini_service.logger") as mock_logger:
            with pytest.raises(json.JSONDecodeError):
                svc._parse_json(truncated)

        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args.args[0] == "gemini_json_parse_failed"


class TestRetryClassification:
    """Retrying a permanent failure just burns the customer's latency budget."""

    @pytest.mark.parametrize(
        "code,retryable",
        [(500, True), (503, True), (400, False), (403, False), (404, False), (429, False)],
    )
    def test_only_transient_status_codes_are_retried(self, code, retryable):
        """Only 5xx is retried; 4xx — including a per-day 429 — repeats identically."""
        from app.services.gemini_service import _is_gemini_retryable

        exc = Exception("boom")
        exc.code = code
        assert _is_gemini_retryable(exc) is retryable
