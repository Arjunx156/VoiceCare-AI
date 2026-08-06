"""
Unit tests for GeminiService — all LLM calls are mocked.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Test analyze_intent
# ---------------------------------------------------------------------------
class TestAnalyzeIntent:

    @pytest.mark.asyncio
    async def test_analyze_intent_happy_path(self, mock_gemini_intent_response):
        """analyze_intent returns structured dict on success."""
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
            svc._call_gemini = AsyncMock(return_value=json.dumps(mock_gemini_intent_response))
            svc._parse_json = lambda text: json.loads(text)

            result = await svc.analyze_intent("Where is my order?", "English")

        assert result["intent"] == "order_status"
        assert result["sentiment"] == "Neutral"
        assert result["priority"] == "Medium"
        assert result["requires_order_lookup"] is True

    @pytest.mark.asyncio
    async def test_analyze_intent_fallback_on_llm_failure(self):
        """On LLM failure, analyze_intent returns safe fallback dict."""
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
            svc._call_gemini = AsyncMock(side_effect=Exception("API rate limit"))

            result = await svc.analyze_intent("Test query", "English")

        assert result["intent"] == "general_inquiry"
        assert result["sentiment"] == "Neutral"
        assert result["requires_order_lookup"] is False

    @pytest.mark.asyncio
    async def test_analyze_intent_angry_sentiment(self):
        """Angry sentiment is correctly extracted from LLM response."""
        angry_response = {
            "intent": "refund_status",
            "sub_intent": "demanding refund",
            "sentiment": "Very Angry",
            "priority": "Critical",
            "summary_english": "Customer very angry about refund delay",
            "requires_order_lookup": True,
            "extracted_order_id": None,
            "extracted_phone": None,
            "extracted_name": None,
        }
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
            svc._call_gemini = AsyncMock(return_value=json.dumps(angry_response))
            svc._parse_json = lambda text: json.loads(text)

            result = await svc.analyze_intent("Give me my money back!", "English")

        assert result["sentiment"] == "Very Angry"
        assert result["priority"] == "Critical"


# ---------------------------------------------------------------------------
# Test generate_resolution
# ---------------------------------------------------------------------------
class TestGenerateResolution:

    @pytest.mark.asyncio
    async def test_generate_resolution_inform(self, mock_gemini_resolution_response):
        """Generates Inform resolution for non-critical case."""
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
            svc._call_gemini = AsyncMock(return_value=json.dumps(mock_gemini_resolution_response))
            svc._parse_json = lambda text: json.loads(text)

            result = await svc.generate_resolution(
                query="Where is my order?",
                intent="order_status",
                order_data={"status": "Shipped"},
                policy_context="Delivery in 5-7 days",
                sentiment="Neutral",
            )

        assert result["recommended_action"] == "Inform"
        assert result["confidence_score"] >= 0.8
        assert result["requires_human_review"] is False

    @pytest.mark.asyncio
    async def test_generate_resolution_fallback_on_error(self):
        """Returns fallback resolution dict when LLM fails."""
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
            svc._call_gemini = AsyncMock(side_effect=Exception("Quota exceeded"))

            result = await svc.generate_resolution(
                query="Test", intent="general_inquiry",
                order_data=None, policy_context="", sentiment="Neutral",
            )

        assert result["recommended_action"] == "Escalate"
        # The LLM never ran — confidence must be low enough to trip the
        # deterministic low-confidence escalation rule (< 0.4).
        assert result["confidence_score"] < 0.4
        assert result["requires_human_review"] is True


# ---------------------------------------------------------------------------
# Test generate_response
# ---------------------------------------------------------------------------
class TestGenerateResponse:

    @pytest.mark.asyncio
    async def test_generate_response_happy_path(self, mock_gemini_response_response):
        """Generates customer response with correct structure."""
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
            svc._call_gemini = AsyncMock(return_value=json.dumps(mock_gemini_response_response))
            svc._parse_json = lambda text: json.loads(text)

            result = await svc.generate_response(
                query="Where is my order?",
                resolution={"recommended_action": "Inform"},
                language="Hindi",
                customer_name="Priya",
            )

        assert "response_text" in result
        assert "response_english" in result
        assert "tone" in result

    @pytest.mark.asyncio
    async def test_generate_response_fallback_on_error(self):
        """Returns apologetic fallback response when LLM fails."""
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
            svc._call_gemini = AsyncMock(side_effect=Exception("Service unavailable"))

            result = await svc.generate_response(
                query="Test", resolution={}, language="English",
            )

        assert "apologize" in result["response_text"].lower() or "difficulty" in result["response_text"].lower()
        assert result["tone"] == "Apologetic"


# ---------------------------------------------------------------------------
# Test _parse_json
# ---------------------------------------------------------------------------
class TestParseJson:

    def test_parse_clean_json(self):
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
        raw = '{"intent": "order_status", "priority": "Medium"}'
        result = svc._parse_json(raw)
        assert result["intent"] == "order_status"

    def test_parse_markdown_wrapped_json(self):
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
        raw = '```json\n{"intent": "refund_status"}\n```'
        result = svc._parse_json(raw)
        assert result["intent"] == "refund_status"

    def test_parse_invalid_json_raises(self):
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
        with pytest.raises(Exception):
            svc._parse_json("not valid json {{{")


# ---------------------------------------------------------------------------
# Test token budgeting
# ---------------------------------------------------------------------------
class TestTokenBudgets:
    """On gemini-2.5-* the thinking budget is spent OUT OF max_output_tokens.

    A ceiling at or below its thinking budget leaves nothing for the JSON, so
    every call comes back truncated and silently degrades to a fallback dict —
    which is how intent analysis stopped returning extracted_order_id at all.
    """

    def _budgets(self):
        with patch("app.services.gemini_service.genai"):
            from app.services import gemini_service as gs
        return [
            ("intent", gs._THINKING_BUDGET_INTENT, gs._MAX_TOKENS_INTENT),
            ("resolution", gs._THINKING_BUDGET_RESOLUTION, gs._MAX_TOKENS_RESOLUTION),
            ("response", gs._THINKING_BUDGET_RESPONSE, gs._MAX_TOKENS_RESPONSE),
        ]

    def test_every_call_leaves_room_for_its_json_payload(self):
        """Each call's output ceiling exceeds its thinking budget by 1024+ tokens."""
        for name, thinking, ceiling in self._budgets():
            assert ceiling - thinking >= 1024, (
                f"{name}: only {ceiling - thinking} tokens left for output"
            )

    @pytest.mark.asyncio
    async def test_oversized_thinking_budget_is_clamped_not_honoured(self):
        """A budget that would crowd out the payload is clamped, and logged."""
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)

        captured = {}

        async def _generate_content(model, contents, config):
            captured["thinking"] = config.thinking_config.thinking_budget
            captured["max"] = config.max_output_tokens
            return MagicMock(candidates=[MagicMock(finish_reason=None)], text="{}")

        svc.client = MagicMock()
        svc.client.aio.models.generate_content = _generate_content

        await svc._call_gemini("prompt", max_output_tokens=800, thinking_budget=1024)

        assert captured["thinking"] < captured["max"]

    @pytest.mark.asyncio
    async def test_each_call_forwards_its_own_thinking_budget(self):
        """analyze_intent/generate_resolution/generate_response each set a budget."""
        with patch("app.services.gemini_service.genai"):
            from app.services import gemini_service as gs
            svc = gs.GeminiService.__new__(gs.GeminiService)
        svc._parse_json = lambda text: {}
        svc._call_gemini = AsyncMock(return_value="{}")

        await svc.analyze_intent("q", "English")
        assert svc._call_gemini.await_args.kwargs["thinking_budget"] == gs._THINKING_BUDGET_INTENT

        await svc.generate_resolution("q", "order_status", None, "policy", "Neutral")
        assert svc._call_gemini.await_args.kwargs["thinking_budget"] == gs._THINKING_BUDGET_RESOLUTION

        await svc.generate_response("q", {}, "English")
        assert svc._call_gemini.await_args.kwargs["thinking_budget"] == gs._THINKING_BUDGET_RESPONSE


# ---------------------------------------------------------------------------
# Test resolution grounding
# ---------------------------------------------------------------------------
class TestAccountContext:
    """Agent 3 loads shipment/return/refund/payment rows on every verified
    lookup, but only the order row used to reach the resolution prompt — so
    "where is my refund" was answered from policy text alone."""

    def _ctx(self, **kwargs):
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
        defaults = dict(
            order_data=None, shipment_data=None, return_data=None,
            refund_data=None, payment_data=None,
            order_not_found=False, order_reference=None,
        )
        return GeminiService._account_context(**{**defaults, **kwargs})

    def test_shipment_and_refund_reach_the_resolution_prompt(self):
        """Tracking and refund state are in the prompt, not just the order row."""
        context = self._ctx(
            order_data={"order_number": "ORD-7K3F", "status": "Shipped"},
            shipment_data={"tracking_number": "BD123456789", "shipment_status": "In Transit"},
            refund_data={"status": "Pending", "amount": 3499.0},
        )
        assert "BD123456789" in context
        assert "In Transit" in context
        assert "Pending" in context

    def test_unmatched_order_number_is_stated_not_hidden(self):
        """A named-but-missing order tells the model to ask, not to guess."""
        context = self._ctx(order_not_found=True, order_reference="ORD-ZZZZ")
        assert "ORD-ZZZZ" in context
        assert "no such order" in context.lower()

    def test_no_data_is_distinct_from_a_bad_order_number(self):
        """Saying nothing identifying must not read as a failed order lookup."""
        context = self._ctx()
        assert "no such order" not in context.lower()
        assert "No account or order data" in context


class TestParseJsonRecovery:
    """Live models append stray content after the answer often enough to matter;
    json.loads rejects the entire payload for it, discarding a usable result."""

    def _svc(self):
        with patch("app.services.gemini_service.genai"):
            from app.services.gemini_service import GeminiService
            return GeminiService.__new__(GeminiService)

    def test_trailing_content_after_the_object_is_ignored(self):
        """A second object appended after the answer does not lose the answer."""
        raw = '{"recommended_action": "Track", "confidence_score": 0.9}\n{"stray": 1}'
        assert self._svc()._parse_json(raw)["recommended_action"] == "Track"

    def test_leading_prose_before_the_object_is_skipped(self):
        """Prose emitted before the JSON does not fail the parse."""
        raw = 'Here is the result:\n{"intent": "order_status"}'
        assert self._svc()._parse_json(raw)["intent"] == "order_status"

    def test_genuinely_truncated_json_still_raises(self):
        """Recovery must not paper over a real truncation."""
        with pytest.raises(Exception):
            self._svc()._parse_json('{"resolution_summary": "the order is')
