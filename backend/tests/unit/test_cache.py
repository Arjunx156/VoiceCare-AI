"""
Unit tests for the policy RAG caching layer in agent_policy_rag.
Verifies that a warm cache bypasses Chroma and a cold cache populates it.
"""

import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


class TestPolicyRAGCache:

    def _make_cache_key(self, query: str) -> str:
        return f"policy_rag:{hashlib.md5(query.encode()).hexdigest()}"

    @pytest.mark.asyncio
    async def test_cache_miss_calls_chroma(self, sample_pipeline_state):
        """On cache miss, Chroma is queried and result is stored."""
        from app.agents.pipeline import VoiceCarePipeline

        sample_pipeline_state.transcript_english = "Where is my order?"
        sample_pipeline_state.transcript_original = "Where is my order?"

        mock_chroma = MagicMock()
        mock_chroma.get_policy_context = MagicMock(return_value="Policy: 5-7 days delivery")
        mock_chroma.query_policies = MagicMock(return_value=[{"id": "p1", "content": "5-7 days", "score": 0.9}])

        mock_memory = MagicMock()
        mock_memory.get_cache = AsyncMock(return_value=None)  # cache miss
        mock_memory.set_cache = AsyncMock()

        pipeline = VoiceCarePipeline(db=MagicMock())
        pipeline.chroma = mock_chroma

        with patch("app.agents.pipeline.get_memory_service", return_value=mock_memory):
            result = await pipeline.agent_policy_rag(sample_pipeline_state)

        mock_chroma.get_policy_context.assert_called_once()
        mock_memory.set_cache.assert_called_once()
        assert result.policy_context == "Policy: 5-7 days delivery"

    @pytest.mark.asyncio
    async def test_cache_hit_skips_chroma(self, sample_pipeline_state):
        """On cache hit, Chroma is NOT called and cached values are used."""
        from app.agents.pipeline import VoiceCarePipeline

        query = "Where is my order?"
        sample_pipeline_state.transcript_english = query
        sample_pipeline_state.transcript_original = query

        cached_payload = {
            "policy_context": "Cached policy context",
            "retrieved_policies": [{"id": "cached-p1", "content": "cached", "score": 0.95}],
        }

        mock_chroma = MagicMock()
        mock_memory = MagicMock()
        mock_memory.get_cache = AsyncMock(return_value=cached_payload)
        mock_memory.set_cache = AsyncMock()

        pipeline = VoiceCarePipeline(db=MagicMock())
        pipeline.chroma = mock_chroma

        with patch("app.agents.pipeline.get_memory_service", return_value=mock_memory):
            result = await pipeline.agent_policy_rag(sample_pipeline_state)

        mock_chroma.get_policy_context.assert_not_called()
        mock_memory.set_cache.assert_not_called()
        assert result.policy_context == "Cached policy context"
        assert len(result.retrieved_policies) == 1

    @pytest.mark.asyncio
    async def test_cache_key_is_deterministic(self, sample_pipeline_state):
        """Same query always produces the same cache key."""
        query = "Where is my refund?"
        key1 = self._make_cache_key(query)
        key2 = self._make_cache_key(query)
        assert key1 == key2
        assert key1.startswith("policy_rag:")

    @pytest.mark.asyncio
    async def test_different_queries_produce_different_keys(self):
        """Different queries produce different cache keys."""
        key1 = self._make_cache_key("refund status")
        key2 = self._make_cache_key("delivery delay")
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_chroma_error_returns_fallback(self, sample_pipeline_state):
        """Chroma failure sets fallback policy_context without crashing."""
        from app.agents.pipeline import VoiceCarePipeline

        sample_pipeline_state.transcript_english = "What is your return policy?"
        sample_pipeline_state.transcript_original = "What is your return policy?"

        mock_chroma = MagicMock()
        mock_chroma.get_policy_context = MagicMock(side_effect=RuntimeError("Chroma unavailable"))
        mock_chroma.query_policies = MagicMock(side_effect=RuntimeError("Chroma unavailable"))

        mock_memory = MagicMock()
        mock_memory.get_cache = AsyncMock(return_value=None)
        mock_memory.set_cache = AsyncMock()

        pipeline = VoiceCarePipeline(db=MagicMock())
        pipeline.chroma = mock_chroma

        with patch("app.agents.pipeline.get_memory_service", return_value=mock_memory):
            result = await pipeline.agent_policy_rag(sample_pipeline_state)

        assert result.policy_context == "No policy documents available."
        assert not result.has_error
