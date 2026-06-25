"""
Unit tests for ChromaService — vector store calls are mocked.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestChromaService:

    def test_get_policy_context_returns_string(self, mock_chroma_service):
        """get_policy_context returns a non-empty string."""
        result = mock_chroma_service.get_policy_context("order status", n_results=3)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_query_policies_returns_list(self, mock_chroma_service):
        """query_policies returns a list of dicts."""
        result = mock_chroma_service.query_policies("refund request", n_results=3)
        assert isinstance(result, list)
        assert len(result) > 0
        assert "content" in result[0]

    def test_policy_rag_agent_uses_chroma(self):
        """Agent 4 (Policy RAG) calls chroma service correctly."""
        from app.agents.state import PipelineState

        state = PipelineState(
            transcript_english="I need a refund",
            summary_english="Customer requesting refund",
        )

        mock_chroma = MagicMock()
        mock_chroma.get_policy_context = MagicMock(return_value="Refund policy: 7 day window")
        mock_chroma.query_policies = MagicMock(return_value=[{"content": "...", "score": 0.9}])

        import asyncio
        from unittest.mock import AsyncMock

        mock_memory = MagicMock()
        mock_memory.get_cache = AsyncMock(return_value=None)  # cache miss
        mock_memory.set_cache = AsyncMock()

        mock_db = MagicMock()

        async def run():
            from app.agents.pipeline import VoiceCarePipeline
            with (
                patch("app.agents.pipeline.get_gemini_service", return_value=MagicMock()),
                patch("app.agents.pipeline.get_bhashini_service", return_value=MagicMock()),
                patch("app.agents.pipeline.get_chroma_service", return_value=mock_chroma),
                patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=mock_memory)),
            ):
                pipeline = VoiceCarePipeline(db=mock_db)
                return await pipeline.agent_policy_rag(state)

        result = asyncio.get_event_loop().run_until_complete(run())
        mock_chroma.get_policy_context.assert_called_once()
        mock_chroma.query_policies.assert_called_once()
        assert result.policy_context == "Refund policy: 7 day window"

    def test_policy_rag_agent_handles_chroma_failure(self):
        """Agent 4 sets fallback context if ChromaDB is unavailable."""
        from app.agents.state import PipelineState
        import asyncio
        from unittest.mock import AsyncMock

        state = PipelineState(transcript_english="My order is late")

        mock_chroma = MagicMock()
        mock_chroma.get_policy_context = MagicMock(side_effect=Exception("ChromaDB unavailable"))
        mock_chroma.query_policies = MagicMock(side_effect=Exception("ChromaDB unavailable"))

        mock_memory = MagicMock()
        mock_memory.get_cache = AsyncMock(return_value=None)  # cache miss → triggers Chroma call
        mock_memory.set_cache = AsyncMock()

        mock_db = MagicMock()

        async def run():
            from app.agents.pipeline import VoiceCarePipeline
            with (
                patch("app.agents.pipeline.get_gemini_service", return_value=MagicMock()),
                patch("app.agents.pipeline.get_bhashini_service", return_value=MagicMock()),
                patch("app.agents.pipeline.get_chroma_service", return_value=mock_chroma),
                patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=mock_memory)),
            ):
                pipeline = VoiceCarePipeline(db=mock_db)
                return await pipeline.agent_policy_rag(state)

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result.policy_context == "No policy documents available."
        assert result.has_error is False
