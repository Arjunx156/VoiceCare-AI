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

        assert result["recommended_action"] == "Inform"
        assert "confidence_score" in result


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
