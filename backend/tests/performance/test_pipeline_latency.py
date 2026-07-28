"""Latency budgets for the voice pipeline.

These are the regression guards for the work that took a turn from ~10-25s down
to under 10s. Each one pins a specific property that, when it broke, cost
seconds — not a synthetic benchmark number that would flake on slow CI.

External services are mocked with realistic fixed delays, so the figures measure
*our* orchestration (what runs concurrently, how many round trips we make),
never the speed of the machine running the tests.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import make_mock_db, patch_all_services

# Simulated cost of one external call. Large enough that a serialised pair is
# unambiguously distinguishable from a concurrent one, small enough to keep the
# suite fast.
FAKE_SERVICE_DELAY_S = 0.10

# The product requirement: a customer waits under 10 seconds for an answer.
# Asserted against mocked services, so this checks that our own orchestration
# adds no hidden serialisation — not that Gemini is fast.
ANSWER_BUDGET_S = 10.0


def _slow(return_value):
    """An async mock that takes FAKE_SERVICE_DELAY_S to answer."""

    async def _call(*args, **kwargs):
        await asyncio.sleep(FAKE_SERVICE_DELAY_S)
        return return_value

    return AsyncMock(side_effect=_call)


def _gemini(intent, resolution, response):
    svc = MagicMock()
    svc.analyze_intent = _slow(intent)
    svc.generate_resolution = _slow(resolution)
    svc.generate_response = _slow(response)
    return svc


def _memory():
    mem = MagicMock()
    mem.get_conversation_history = AsyncMock(return_value=[])
    mem.store_conversation_turn = AsyncMock()
    mem.get_session_context = AsyncMock(return_value=None)
    mem.set_session_context = AsyncMock()
    mem.get_cache = AsyncMock(return_value=None)
    mem.set_cache = AsyncMock()
    return mem


class TestAnswerLatencyBudget:

    @pytest.mark.asyncio
    async def test_run_critical_stays_within_the_answer_budget(
        self,
        mock_gemini_intent_response,
        mock_gemini_resolution_response,
        mock_gemini_response_response,
        mock_chroma_service,
    ):
        """Agents 1-7 deliver an answer inside the 10s product budget."""
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        gemini = _gemini(
            mock_gemini_intent_response,
            mock_gemini_resolution_response,
            mock_gemini_response_response,
        )
        bhashini = MagicMock()
        bhashini.text_to_speech = _slow("audio")
        patches = patch_all_services(gemini, bhashini, mock_chroma_service, _memory())

        state = PipelineState(raw_text="Where is my order?", language_code="en")

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            started = time.perf_counter()
            result = await pipeline.run_critical(state)
            elapsed = time.perf_counter() - started

        assert result.response_text
        assert elapsed < ANSWER_BUDGET_S

    @pytest.mark.asyncio
    async def test_answer_does_not_wait_for_tts_or_ticket(
        self,
        mock_gemini_intent_response,
        mock_gemini_resolution_response,
        mock_gemini_response_response,
        mock_chroma_service,
    ):
        """run_critical returns before speech synthesis and ticket persistence.

        This is what lets the WebSocket send the answer 2-6s earlier. If someone
        moves agent 8 or 9 back into run_critical, this fails.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        gemini = _gemini(
            mock_gemini_intent_response,
            mock_gemini_resolution_response,
            mock_gemini_response_response,
        )
        bhashini = MagicMock()
        bhashini.text_to_speech = _slow("base64audio")
        patches = patch_all_services(gemini, bhashini, mock_chroma_service, _memory())

        state = PipelineState(raw_text="Where is my order?", language_code="en")

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            result = await pipeline.run_critical(state)

        assert result.response_text
        assert result.response_audio_base64 is None
        assert result.ticket_created is False
        bhashini.text_to_speech.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_total_duration_is_reported_and_monotonic(self):
        """elapsed_ms() grows with real time and is exposed to the client."""
        from app.agents.state import PipelineState

        state = PipelineState(raw_text="hello")
        first = state.elapsed_ms()
        await asyncio.sleep(0.05)
        second = state.elapsed_ms()

        assert first >= 0
        assert second > first


class TestConcurrency:

    @pytest.mark.asyncio
    async def test_order_lookup_and_policy_rag_actually_overlap(
        self, mock_gemini_intent_response, mock_gemini_resolution_response,
        mock_gemini_response_response, mock_chroma_service,
    ):
        """Stages 3 and 4 run concurrently, not back to back.

        They sit in an asyncio.gather, but that only buys concurrency if neither
        blocks the event loop. When the Gemini client was synchronous and the
        Chroma call was made inline, this gather was decorative — the pair cost
        the sum of its parts. Asserting on wall time is the only way to catch a
        regression back to blocking calls.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        gemini = _gemini(
            mock_gemini_intent_response,
            mock_gemini_resolution_response,
            mock_gemini_response_response,
        )
        patches = patch_all_services(gemini, MagicMock(), mock_chroma_service, _memory())

        state = PipelineState(
            raw_text="Where is my order?",
            language_code="en",
            summary_english="order status",
        )

        async def slow_db_execute(*args, **kwargs):
            await asyncio.sleep(FAKE_SERVICE_DELAY_S)
            result = MagicMock()
            result.scalar_one_or_none = MagicMock(return_value=None)
            result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
            return result

        db = make_mock_db()
        db.execute = AsyncMock(side_effect=slow_db_execute)

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=db)
            state.phone = "9876543210"
            started = time.perf_counter()
            await asyncio.gather(
                pipeline.agent_order_lookup(state),
                pipeline.agent_policy_rag(state),
            )
            elapsed = time.perf_counter() - started

        # Serialised, this would cost at least 2x the delay. Allow generous
        # headroom so the assertion tracks concurrency, not machine speed.
        assert elapsed < FAKE_SERVICE_DELAY_S * 1.8


class TestQueryEfficiency:

    @pytest.mark.asyncio
    async def test_policy_retrieval_embeds_the_query_once(self, mock_chroma_service):
        """One embed + one vector search per turn, not two.

        The agent used to call get_policy_context() and query_policies() back to
        back, running the sentence-transformer twice for identical results.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        state = PipelineState(summary_english="refund status", transcript_english="refund")
        patches = patch_all_services(
            MagicMock(), MagicMock(), mock_chroma_service, _memory()
        )

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            await pipeline.agent_policy_rag(state)

        assert mock_chroma_service.query_with_context.call_count == 1
        mock_chroma_service.get_policy_context.assert_not_called()

    @pytest.mark.asyncio
    async def test_order_lookup_issues_a_bounded_number_of_queries(self):
        """Agent 3 stays within a small, fixed query budget.

        models.py sets lazy="selectin" on almost every relationship, so a bare
        select(User) silently fans out to 15-25 round trips. The pipeline passes
        noload("*") to suppress that; this ceiling catches its removal.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        MAX_QUERIES_FOR_A_MISSING_USER = 3

        db = make_mock_db()
        state = PipelineState(phone="9876543210", summary_english="where is my order")
        patches = patch_all_services(MagicMock(), MagicMock(), MagicMock(), _memory())

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=db)
            await pipeline.agent_order_lookup(state)

        assert db.execute.await_count <= MAX_QUERIES_FOR_A_MISSING_USER


class TestPromptSize:

    def test_conversation_history_in_prompts_is_bounded(self):
        """A long session cannot grow the prompt without limit.

        analyze_intent used to serialise the entire history on every call, so
        prompt size — and therefore time-to-first-token — grew with the
        conversation.
        """
        from app.services.gemini_service import GeminiService

        long_history = [
            {"role": "customer", "content": f"message number {i} " + "x" * 500}
            for i in range(50)
        ]

        rendered = GeminiService._compact_history(long_history, 4)

        assert rendered.count('"role"') <= 4
        # Compact separators, not indent=2 — whitespace is 20-40% of the tokens.
        assert ", " not in rendered
        assert len(rendered) < 2000

    def test_history_serialisation_is_empty_when_there_is_none(self):
        """No history means no prompt overhead at all."""
        from app.services.gemini_service import GeminiService

        assert GeminiService._compact_history([], 4) == ""
        assert GeminiService._compact_history(None, 4) == ""
