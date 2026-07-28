"""Behaviour when an external dependency fails.

Every one of these dependencies has failed in production at least once. The
pipeline's contract is that a single dependency going down degrades the answer
but never drops the turn, and never silently pretends the failure did not
happen — a confident-sounding answer built on a failed policy lookup is worse
than an honest escalation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_mock_db, patch_all_services


def _memory():
    mem = MagicMock()
    mem.get_conversation_history = AsyncMock(return_value=[])
    mem.store_conversation_turn = AsyncMock()
    mem.get_session_context = AsyncMock(return_value=None)
    mem.set_session_context = AsyncMock()
    mem.get_cache = AsyncMock(return_value=None)
    mem.set_cache = AsyncMock()
    return mem


class TestPolicyRetrievalOutage:

    @pytest.mark.asyncio
    async def test_chroma_failure_leaves_a_usable_fallback_context(self):
        """A vector-store outage does not fail the turn."""
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        chroma = MagicMock()
        chroma.query_with_context = MagicMock(side_effect=RuntimeError("Chroma down"))
        patches = patch_all_services(MagicMock(), MagicMock(), chroma, _memory())

        state = PipelineState(summary_english="refund policy", transcript_english="refund")

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            result = await pipeline.agent_policy_rag(state)

        assert result.has_error is False
        assert result.policy_context
        assert result.rag_retrieved_count == 0

    @pytest.mark.asyncio
    async def test_no_retrieved_policy_caps_confidence(
        self, mock_gemini_resolution_response
    ):
        """An answer with no policy behind it cannot claim high confidence.

        Escalation rule 5 fires below 0.4 and human review is advised below
        0.65, so this cap is what routes an ungrounded answer to a person. A
        Chroma outage must not produce a confident-sounding ungrounded reply.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        CONFIDENCE_CEILING_WITHOUT_POLICY = 0.65

        overconfident = {**mock_gemini_resolution_response, "confidence_score": 0.99}
        gemini = MagicMock()
        gemini.generate_resolution = AsyncMock(return_value=overconfident)
        patches = patch_all_services(gemini, MagicMock(), MagicMock(), _memory())

        state = PipelineState(
            transcript_english="I want a refund",
            intent="refund_status",
            rag_retrieved_count=0,
        )

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            result = await pipeline.agent_resolution(state)

        assert result.confidence_score <= CONFIDENCE_CEILING_WITHOUT_POLICY


class TestLLMOutage:

    @pytest.mark.asyncio
    async def test_intent_analysis_falls_back_without_failing_the_turn(self):
        """A Gemini outage yields a safe default intent, not an error state."""
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        gemini = MagicMock()
        gemini.analyze_intent = AsyncMock(side_effect=RuntimeError("429 quota exceeded"))
        patches = patch_all_services(gemini, MagicMock(), MagicMock(), _memory())

        state = PipelineState(transcript_english="Where is my order?", language_code="en")

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            result = await pipeline.agent_intent_analysis(state)

        assert result.has_error is False
        assert result.intent

    @pytest.mark.asyncio
    async def test_resolution_outage_escalates_rather_than_guessing(self):
        """When the resolution LLM is down, a human gets the ticket.

        The service-level fallback reports confidence 0.3 precisely so that
        escalation rule 5 (< 0.4) fires. The alternative — a plausible-sounding
        canned answer at high confidence — would silently mislead the customer.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        gemini = MagicMock()
        gemini.generate_resolution = AsyncMock(
            return_value={
                "recommended_action": "Inform",
                "resolution_summary": "System fallback",
                "policy_reference": "Standard Practice",
                "internal_note": "LLM unavailable",
                "confidence_score": 0.3,
                "requires_human_review": True,
                "reason_for_action": "System fallback",
            }
        )
        patches = patch_all_services(gemini, MagicMock(), MagicMock(), _memory())

        state = PipelineState(
            transcript_english="Where is my refund?",
            intent="refund_status",
            sentiment="Neutral",
            rag_retrieved_count=3,
        )

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            state = await pipeline.agent_resolution(state)
            result = await pipeline.agent_escalation_check(state)

        assert result.is_escalated is True
        assert result.escalation_rules_triggered


class TestSpeechSynthesisOutage:

    @pytest.mark.asyncio
    async def test_tts_failure_keeps_the_text_answer(self):
        """No audio is a degraded turn, not a failed one.

        The client falls back to the browser's own speech synthesiser, so the
        customer still hears a reply.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        bhashini = MagicMock()
        bhashini.text_to_speech = AsyncMock(side_effect=RuntimeError("Bhashini 503"))
        patches = patch_all_services(MagicMock(), bhashini, MagicMock(), _memory())

        state = PipelineState(
            response_text="Your order arrives tomorrow.",
            language_code="hi",
        )

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            result = await pipeline.agent_tts(state)

        assert result.response_text == "Your order arrives tomorrow."
        assert result.response_audio_base64 is None
        assert result.has_error is False

    @pytest.mark.asyncio
    async def test_tts_returning_none_emits_no_audio_frame(self):
        """A silent TTS must not push an empty audio frame to the client.

        An audio frame is what makes the client cancel its browser-speech
        fallback, so emitting one with no payload would produce total silence.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        frames = []

        async def capture(payload):
            frames.append(payload)

        bhashini = MagicMock()
        bhashini.text_to_speech = AsyncMock(return_value=None)
        patches = patch_all_services(MagicMock(), bhashini, MagicMock(), _memory())

        state = PipelineState(response_text="Your order arrives tomorrow.", language_code="en")

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db(), on_stage_update=capture)
            await pipeline.run_deferred(state)

        assert not [f for f in frames if f.get("type") == "audio"]
        assert [f for f in frames if f.get("type") == "done"]


class TestPersistenceOutage:

    @pytest.mark.asyncio
    async def test_ticket_write_failure_is_reported_not_hidden(self):
        """A failed ticket write surfaces as ticket_created=False.

        Never a 500 (the customer already has their answer) and never a
        ticket_id that was rolled back.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        db = make_mock_db()
        db.execute = AsyncMock(side_effect=RuntimeError("connection reset"))
        patches = patch_all_services(MagicMock(), MagicMock(), MagicMock(), _memory())

        state = PipelineState(
            transcript_english="Where is my order?",
            response_text="Tomorrow.",
            intent="order_status",
        )

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=db)
            result = await pipeline.agent_ticket_creation(state)

        assert result.ticket_created is False
        assert result.ticket_id is None

    @pytest.mark.asyncio
    async def test_deferred_stage_failure_still_releases_the_client(self):
        """A crash in the background stages must not hang the UI.

        The client keeps its spinner up until a terminal `done` frame arrives,
        so the failure path has to send one anyway.
        """
        from app.agents.state import PipelineState
        from app.api.voice import _run_deferred_stages

        frames = []

        async def capture(payload):
            frames.append(payload)

        state = PipelineState(response_text="Tomorrow.", transcript_english="order?")

        # Fail at session acquisition — the earliest and most total way the
        # background task can die, and the one that skips every later guard.
        with patch(
            "app.core.database.async_session",
            side_effect=RuntimeError("pool exhausted"),
        ):
            await _run_deferred_stages(state, capture, "turn-1")

        done = [f for f in frames if f.get("type") == "done"]
        assert done, "a terminal done frame must be sent even when the task fails"
        assert done[-1]["is_complete"] is True


class TestTransportFailures:

    @pytest.mark.asyncio
    async def test_a_dead_socket_does_not_fail_the_pipeline(self):
        """Send failures are swallowed, not reported as pipeline errors.

        Without this guard a closed socket raises inside whichever agent was
        emitting, is caught by that agent's own except block, and is
        misreported to the next customer as a processing failure.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        async def dead_socket(payload):
            raise ConnectionResetError("client went away")

        patches = patch_all_services(MagicMock(), MagicMock(), MagicMock(), _memory())
        state = PipelineState(raw_text="Where is my order?", language_code="en")

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db(), on_stage_update=dead_socket)
            result = await pipeline.agent_voice_intake(state)

        assert result.has_error is False
        assert result.transcript_english == "Where is my order?"
