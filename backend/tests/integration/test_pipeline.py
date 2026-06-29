"""
Integration tests for the full 9-agent pipeline.
All external services (Gemini, Bhashini, Chroma) are mocked.
Tests verify state transitions through each agent stage.
"""

import json
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_mock_db():
    """SQLAlchemy session mock that returns None for scalars."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.scalar_one_or_none = AsyncMock(return_value=None)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    db.execute = AsyncMock(return_value=mock_result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


def _patch_all_services(gemini_svc, bhashini_svc, chroma_svc, memory_svc):
    """Context manager that patches all external service getters."""
    return (
        patch("app.agents.pipeline.get_gemini_service", return_value=gemini_svc),
        patch("app.agents.pipeline.get_bhashini_service", return_value=bhashini_svc),
        patch("app.agents.pipeline.get_chroma_service", return_value=chroma_svc),
        patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=memory_svc)),
    )


# ---------------------------------------------------------------------------
# Agent 1: Voice Intake
# ---------------------------------------------------------------------------
class TestAgent1VoiceIntake:

    @pytest.mark.asyncio
    async def test_text_input_sets_transcript(self):
        """Text-only input: transcript fields populated, no Bhashini call."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(raw_text="Where is my order?", language_code="en")
        mock_bhashini = MagicMock()
        mock_bhashini.speech_to_text = AsyncMock()

        with patch("app.agents.pipeline.get_bhashini_service", return_value=mock_bhashini):
            pipeline = VoiceCarePipeline(db=_make_mock_db())
            result = await pipeline.agent_voice_intake(state)

        assert result.transcript_original == "Where is my order?"
        assert result.transcript_english == "Where is my order?"
        assert result.has_error is False
        mock_bhashini.speech_to_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_input_sets_error(self):
        """Missing audio AND text → error state set."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(raw_audio_base64=None, raw_text=None)
        pipeline = VoiceCarePipeline(db=_make_mock_db())
        result = await pipeline.agent_voice_intake(state)

        assert result.has_error is True
        assert result.error is not None


# ---------------------------------------------------------------------------
# Agent 3 (pipeline order): Order Lookup
# ---------------------------------------------------------------------------
class TestAgent2CustomerIdentification:

    @pytest.mark.asyncio
    async def test_phone_lookup_populates_user_data(self, sample_user_data):
        """DB lookup by phone populates user_data dict."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(phone="9876543210")

        mock_db = _make_mock_db()
        mock_user = MagicMock()
        mock_user.user_id = uuid.UUID(sample_user_data["user_id"])
        mock_user.name = sample_user_data["name"]
        mock_user.phone = "9876543210"
        mock_user.preferred_language = sample_user_data["preferred_language"]
        mock_user.customer_segment = sample_user_data["customer_segment"]
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=mock_user)

        pipeline = VoiceCarePipeline(db=mock_db)
        result = await pipeline.agent_order_lookup(state)

        assert result.user_data is not None
        assert result.user_data["name"] == "Priya Sharma"
        assert result.user_data["preferred_language"] == "Hindi"
        assert result.has_error is False

    @pytest.mark.asyncio
    async def test_unknown_phone_returns_no_user_data(self):
        """Unknown phone number: user_data stays None, no error."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(phone="0000000000")
        mock_db = _make_mock_db()
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value.scalars.return_value.all = MagicMock(return_value=[])

        pipeline = VoiceCarePipeline(db=mock_db)
        result = await pipeline.agent_order_lookup(state)

        assert result.user_data is None
        assert result.has_error is False


# ---------------------------------------------------------------------------
# Agent 3: Intent Classification
# ---------------------------------------------------------------------------
class TestAgent3IntentClassification:

    @pytest.mark.asyncio
    async def test_intent_set_from_gemini(self, mock_gemini_intent_response, mock_gemini_service):
        """Intent, sentiment, and priority derived from Gemini response."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(transcript_english="Where is my order?")

        with patch("app.agents.pipeline.get_gemini_service", return_value=mock_gemini_service):
            pipeline = VoiceCarePipeline(db=_make_mock_db())
            result = await pipeline.agent_intent_analysis(state)

        assert result.intent == "order_status"
        assert result.sentiment == "Neutral"
        assert result.priority == "Medium"

    @pytest.mark.asyncio
    async def test_intent_fallback_on_gemini_failure(self):
        """Falls back to general_inquiry when Gemini fails."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(transcript_english="Test query")
        mock_gemini = MagicMock()
        mock_gemini.analyze_intent = AsyncMock(side_effect=Exception("LLM error"))

        with patch("app.agents.pipeline.get_gemini_service", return_value=mock_gemini):
            pipeline = VoiceCarePipeline(db=_make_mock_db())
            result = await pipeline.agent_intent_analysis(state)

        assert result.has_error is False
        assert result.intent == "general_inquiry"


# ---------------------------------------------------------------------------
# Agent 4: Policy RAG
# ---------------------------------------------------------------------------
class TestAgent4PolicyRAG:

    @pytest.mark.asyncio
    async def test_policy_context_set_from_chroma(self, mock_chroma_service):
        """Policy context string is populated from ChromaDB."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(
            transcript_english="I want to return my order",
            intent="return_request",
            summary_english="Customer wants to return order",
        )

        with patch("app.agents.pipeline.get_chroma_service", return_value=mock_chroma_service):
            pipeline = VoiceCarePipeline(db=_make_mock_db())
            result = await pipeline.agent_policy_rag(state)

        assert result.policy_context is not None
        assert len(result.policy_context) > 0

    @pytest.mark.asyncio
    async def test_policy_rag_fallback_on_chroma_failure(self):
        """Sets empty/fallback context when ChromaDB fails."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(transcript_english="Order issue")
        mock_chroma = MagicMock()
        mock_chroma.get_policy_context = MagicMock(side_effect=Exception("ChromaDB down"))
        mock_chroma.query_policies = MagicMock(side_effect=Exception("ChromaDB down"))

        with patch("app.agents.pipeline.get_chroma_service", return_value=mock_chroma):
            pipeline = VoiceCarePipeline(db=_make_mock_db())
            result = await pipeline.agent_policy_rag(state)

        assert result.has_error is False


# ---------------------------------------------------------------------------
# Agent 9: Session Persistence (Session ID validation fix)
# ---------------------------------------------------------------------------
class TestAgent9SessionPersistence:

    @pytest.mark.asyncio
    async def test_valid_session_id_persisted(self, sample_session_id):
        """Valid UUID session_id is stored without error."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(
            session_id=sample_session_id,
            transcript_english="Test query",
            final_response_text="Response text",
        )

        mock_db = _make_mock_db()
        pipeline = VoiceCarePipeline(db=mock_db)
        result = await pipeline.agent_ticket_creation(state)

        assert result.has_error is False

    @pytest.mark.asyncio
    async def test_invalid_session_id_does_not_crash(self):
        """Invalid session_id string → error set gracefully, no crash."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        state = PipelineState(
            session_id="not-a-valid-uuid",
            transcript_english="Test query",
            final_response_text="Response text",
        )

        mock_db = _make_mock_db()
        pipeline = VoiceCarePipeline(db=mock_db)

        # CRITICAL: must not raise an exception (was the original bug)
        try:
            result = await pipeline.agent_ticket_creation(state)
            # Acceptable outcomes: error state set or session_id set to None
            if result.has_error:
                assert result.error is not None
        except Exception as e:
            pytest.fail(f"agent_ticket_creation crashed with invalid session_id: {e}")

    @pytest.mark.asyncio
    async def test_missing_session_id_uses_default(self):
        """PipelineState always has a valid session_id via default_factory; agent_ticket_creation must not crash."""
        from app.agents.state import PipelineState
        from app.agents.pipeline import VoiceCarePipeline

        # session_id defaults to a new UUID; omitting it is the safe path.
        state = PipelineState(
            transcript_english="Test query",
            final_response_text="Response text",
        )
        assert state.session_id  # always a non-empty string

        mock_db = _make_mock_db()
        pipeline = VoiceCarePipeline(db=mock_db)

        try:
            result = await pipeline.agent_ticket_creation(state)
        except Exception as e:
            pytest.fail(f"agent_ticket_creation crashed: {e}")


# ---------------------------------------------------------------------------
# Agent 9: One ticket per conversation (real in-memory DB)
# ---------------------------------------------------------------------------
class TestAgent9TicketReuse:

    @staticmethod
    def _turn(session_id, text, response, **over):
        from app.agents.state import PipelineState
        return PipelineState(
            session_id=session_id,
            transcript_original=text,
            transcript_english=text,
            response_text=response,
            response_english=response,
            intent="order_status",
            language_detected="English",
            extracted_phone="9999900000",
            summary_english="Order status query",
            recommended_action="Inform",
            confidence_score=0.9,
            **over,
        )

    @pytest.mark.asyncio
    async def test_followup_reuses_same_ticket(self, db_session):
        """A follow-up turn with the same session_id continues ONE ticket."""
        from sqlalchemy import select
        from app.agents.pipeline import VoiceCarePipeline
        from app.db.models import SupportTicket, SupportMessage, SupportResolution

        sid = str(uuid.uuid4())
        pipeline = VoiceCarePipeline(db=db_session)

        r1 = await pipeline.agent_ticket_creation(
            self._turn(sid, "Where is my order?", "It is on the way.")
        )
        assert r1.has_error is False
        first_ticket = r1.ticket_id
        assert first_ticket is not None

        r2 = await pipeline.agent_ticket_creation(
            self._turn(sid, "Still not delivered!", "Let me check for you.",
                       priority="High", sentiment="Negative")
        )
        assert r2.has_error is False
        # Same ticket reused across the two turns.
        assert r2.ticket_id == first_ticket

        # Scope to this conversation (the session-scoped test engine retains
        # rows from sibling tests, so don't count globally).
        tickets = (await db_session.execute(
            select(SupportTicket).where(SupportTicket.session_id == uuid.UUID(sid))
        )).scalars().all()
        assert len(tickets) == 1

        msgs = (await db_session.execute(
            select(SupportMessage).where(
                SupportMessage.ticket_id == uuid.UUID(first_ticket)
            )
        )).scalars().all()
        assert len(msgs) == 4  # 2 customer + 2 AI

        # One resolution row, updated to the latest turn's response.
        resolutions = (await db_session.execute(
            select(SupportResolution).where(
                SupportResolution.ticket_id == uuid.UUID(first_ticket)
            )
        )).scalars().all()
        assert len(resolutions) == 1
        assert resolutions[0].final_response_text == "Let me check for you."

    @pytest.mark.asyncio
    async def test_distinct_sessions_create_distinct_tickets(self, db_session):
        """Different session_ids (e.g. after 'New conversation') get new tickets."""
        from sqlalchemy import select
        from app.agents.pipeline import VoiceCarePipeline
        from app.db.models import SupportTicket

        sid1, sid2 = str(uuid.uuid4()), str(uuid.uuid4())
        pipeline = VoiceCarePipeline(db=db_session)
        r1 = await pipeline.agent_ticket_creation(self._turn(sid1, "Q1", "A1"))
        r2 = await pipeline.agent_ticket_creation(self._turn(sid2, "Q2", "A2"))
        assert r1.ticket_id != r2.ticket_id
        # Each distinct session owns exactly one ticket.
        for sid in (sid1, sid2):
            owned = (await db_session.execute(
                select(SupportTicket).where(SupportTicket.session_id == uuid.UUID(sid))
            )).scalars().all()
            assert len(owned) == 1


# ---------------------------------------------------------------------------
# Full pipeline end-to-end (mocked)
# ---------------------------------------------------------------------------
class TestFullPipeline:

    @pytest.mark.asyncio
    async def test_full_pipeline_text_input_english(
        self,
        mock_gemini_service,
        mock_bhashini_service,
        mock_chroma_service,
        mock_memory_service,
    ):
        """Full 9-agent pipeline completes without error for English text input."""
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        mock_db = _make_mock_db()

        patches = _patch_all_services(
            mock_gemini_service,
            mock_bhashini_service,
            mock_chroma_service,
            mock_memory_service,
        )

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=mock_db)
            result = await pipeline.run(
                PipelineState(
                    phone="9876543210",
                    raw_text="Where is my order?",
                    language_code="en",
                )
            )

        assert result is not None
        assert result.has_error is False
        assert result.response_text is not None

    @pytest.mark.asyncio
    async def test_full_pipeline_records_agent_trace(
        self,
        mock_gemini_service,
        mock_bhashini_service,
        mock_chroma_service,
        mock_memory_service,
    ):
        """Pipeline builds agent_trace with records for each completed stage."""
        from app.agents.pipeline import VoiceCarePipeline

        mock_db = _make_mock_db()
        patches = _patch_all_services(
            mock_gemini_service,
            mock_bhashini_service,
            mock_chroma_service,
            mock_memory_service,
        )

        from app.agents.state import PipelineState
        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=mock_db)
            result = await pipeline.run(
                PipelineState(
                    phone="9876543210",
                    raw_text="Where is my order?",
                    language_code="en",
                )
            )

        assert len(result.agent_trace) >= 1
        for trace_entry in result.agent_trace:
            assert trace_entry.agent_name is not None
            assert trace_entry.stage_number >= 1

    @pytest.mark.asyncio
    async def test_full_pipeline_graceful_on_llm_failure(
        self,
        mock_bhashini_service,
        mock_chroma_service,
        mock_memory_service,
    ):
        """Pipeline returns fallback response when Gemini is completely down."""
        from app.agents.pipeline import VoiceCarePipeline

        mock_db = _make_mock_db()
        failing_gemini = MagicMock()
        failing_gemini.analyze_intent = AsyncMock(side_effect=Exception("LLM down"))
        failing_gemini.generate_resolution = AsyncMock(side_effect=Exception("LLM down"))
        failing_gemini.generate_response = AsyncMock(side_effect=Exception("LLM down"))

        patches = _patch_all_services(
            failing_gemini,
            mock_bhashini_service,
            mock_chroma_service,
            mock_memory_service,
        )

        from app.agents.state import PipelineState
        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=mock_db)
            result = await pipeline.run(
                PipelineState(
                    phone="9876543210",
                    raw_text="Any query",
                    language_code="en",
                )
            )

        # Should not crash; should produce some response (even apologetic)
        assert result is not None
