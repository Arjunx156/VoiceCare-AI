"""
Unit tests for BhashiniService — all HTTP calls are mocked.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGttsFallbackGate:

    @pytest.mark.asyncio
    async def test_gtts_fallback_skipped_when_disabled(self):
        """ALLOW_GTTS_FALLBACK=false: no response text is sent to Google."""
        from app.services.bhashini_service import BhashiniService

        service = BhashiniService()
        disabled_settings = MagicMock()
        disabled_settings.allow_gtts_fallback = False

        with (
            patch.object(
                service, "_get_pipeline_config",
                new=AsyncMock(side_effect=Exception("Bhashini down")),
            ),
            patch("app.core.config.get_settings", return_value=disabled_settings),
            patch("app.services.bhashini_service.httpx.AsyncClient") as mock_client,
        ):
            result = await service.text_to_speech("Your refund of 2500 was approved", "hi")

        assert result is None
        mock_client.assert_not_called()  # no HTTP egress at all

    @pytest.mark.asyncio
    async def test_gtts_fallback_runs_when_enabled(self):
        """Default behavior unchanged: fallback audio is produced."""
        from app.services.bhashini_service import BhashiniService

        service = BhashiniService()
        enabled_settings = MagicMock()
        enabled_settings.allow_gtts_fallback = True

        mock_response = MagicMock()
        mock_response.content = b"mp3bytes"
        mock_response.raise_for_status = MagicMock()
        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(
                service, "_get_pipeline_config",
                new=AsyncMock(side_effect=Exception("Bhashini down")),
            ),
            patch("app.core.config.get_settings", return_value=enabled_settings),
            patch("app.services.bhashini_service.httpx.AsyncClient", return_value=mock_http),
        ):
            result = await service.text_to_speech("Hello there", "hi")

        assert result is not None
        assert result.startswith("mp3:")


class TestBhashiniSTT:

    @pytest.mark.asyncio
    async def test_stt_fallback_when_bhashini_unavailable(self):
        """When Bhashini fails, the pipeline falls back to raw_text."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(
            raw_audio_base64=None,
            raw_text="Where is my order?",
            language_detected="English",
            language_code="en",
        )

        mock_db = MagicMock()
        mock_bhashini = MagicMock()
        mock_bhashini.speech_to_text = AsyncMock(side_effect=Exception("Bhashini unavailable"))

        with (
            patch("app.agents.pipeline.get_gemini_service", return_value=MagicMock()),
            patch("app.agents.pipeline.get_bhashini_service", return_value=mock_bhashini),
            patch("app.agents.pipeline.get_chroma_service", return_value=MagicMock()),
            patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=MagicMock())),
        ):
            pipeline = VoiceCarePipeline(db=mock_db)
            result = await pipeline.agent_voice_intake(state)

        # Should fall back to raw_text, not error
        assert result.transcript_english == "Where is my order?"
        assert result.has_error is False

    @pytest.mark.asyncio
    async def test_stt_error_no_fallback_sets_error_state(self):
        """When Bhashini AND raw_text both unavailable, error state is set."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(
            raw_audio_base64=None,
            raw_text=None,
        )

        mock_db = MagicMock()

        with (
            patch("app.agents.pipeline.get_gemini_service", return_value=MagicMock()),
            patch("app.agents.pipeline.get_bhashini_service", return_value=MagicMock()),
            patch("app.agents.pipeline.get_chroma_service", return_value=MagicMock()),
            patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=MagicMock())),
        ):
            pipeline = VoiceCarePipeline(db=mock_db)
            result = await pipeline.agent_voice_intake(state)

        assert result.has_error is True
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_text_passthrough_no_audio(self):
        """Text-only input passes through Voice Intake without STT call."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(
            raw_audio_base64=None,
            raw_text="I need a refund",
            language_detected="English",
            language_code="en",
        )

        mock_db = MagicMock()
        mock_bhashini = MagicMock()
        mock_bhashini.speech_to_text = AsyncMock()  # Should NOT be called

        with (
            patch("app.agents.pipeline.get_gemini_service", return_value=MagicMock()),
            patch("app.agents.pipeline.get_bhashini_service", return_value=mock_bhashini),
            patch("app.agents.pipeline.get_chroma_service", return_value=MagicMock()),
            patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=MagicMock())),
        ):
            pipeline = VoiceCarePipeline(db=mock_db)
            result = await pipeline.agent_voice_intake(state)

        assert result.transcript_original == "I need a refund"
        assert result.transcript_english == "I need a refund"
        mock_bhashini.speech_to_text.assert_not_called()
