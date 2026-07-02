"""
Integration tests for the identity-verification (anti-IDOR) rules in the
order-lookup and resolution agents.

A phone number alone is a claim, not proof: uncorroborated callers must be
challenged and receive no order/refund/payment data. One corroborating factor
(owned order ID, matching name, or a previously verified session) unlocks the
account for the rest of the session.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.pipeline import VoiceCarePipeline
from app.agents.state import PipelineState
from app.db.models import Order, User

PHONE = "9812345678"
CUSTOMER_NAME = "Priya Sharma"
ORDER_NUMBER = "ORD-IDV1"


@pytest.fixture
async def seeded_customer(db_session):
    user = User(
        name=CUSTOMER_NAME,
        phone=PHONE,
        preferred_language="Hindi",
        customer_segment="Premium",
        created_by="test",
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        user_id=user.user_id,
        order_number=ORDER_NUMBER,
        order_date=datetime(2026, 6, 1),
        status="Shipped",
        total_amount=2500.0,
        created_by="test",
    )
    db_session.add(order)
    await db_session.flush()
    return user, order


def _sensitive_fields(state: PipelineState) -> list:
    return [
        state.order_data,
        state.shipment_data,
        state.return_data,
        state.refund_data,
        state.payment_data,
    ]


class TestPhoneLookupCorroboration:

    @pytest.mark.asyncio
    async def test_phone_only_lookup_is_challenged(self, db_session, seeded_customer):
        """Phone alone: user is found but no sensitive data is populated."""
        state = PipelineState(phone=PHONE)
        pipeline = VoiceCarePipeline(db=db_session)

        result = await pipeline.agent_order_lookup(state)

        assert result.user_data is not None
        assert result.identity_needs_confirmation is True
        assert result.identity_verified is False
        assert result.lookup_successful is False
        assert all(field is None for field in _sensitive_fields(result))
        # Candidate order held internally for next-turn matching only
        assert result.candidate_order_data["order_number"] == ORDER_NUMBER

    @pytest.mark.asyncio
    async def test_phone_with_owned_order_id_is_verified(self, db_session, seeded_customer):
        """Phone + an order ID belonging to the account unlocks full data."""
        _, order = seeded_customer
        state = PipelineState(phone=PHONE, input_order_id=str(order.order_id))
        pipeline = VoiceCarePipeline(db=db_session)

        result = await pipeline.agent_order_lookup(state)

        assert result.identity_verified is True
        assert result.identity_needs_confirmation is False
        assert result.lookup_successful is True
        assert result.order_data["order_number"] == ORDER_NUMBER

    @pytest.mark.asyncio
    async def test_phone_with_matching_name_is_verified(self, db_session, seeded_customer):
        """Phone + first name matching the account verifies the caller."""
        state = PipelineState(phone=PHONE, extracted_name="Priya")
        pipeline = VoiceCarePipeline(db=db_session)

        result = await pipeline.agent_order_lookup(state)

        assert result.identity_verified is True
        assert result.lookup_successful is True
        assert result.order_data is not None

    @pytest.mark.asyncio
    async def test_phone_with_wrong_name_is_challenged(self, db_session, seeded_customer):
        state = PipelineState(phone=PHONE, extracted_name="Rahul Verma")
        pipeline = VoiceCarePipeline(db=db_session)

        result = await pipeline.agent_order_lookup(state)

        assert result.identity_verified is False
        assert result.identity_needs_confirmation is True
        assert all(field is None for field in _sensitive_fields(result))

    @pytest.mark.asyncio
    async def test_verified_session_skips_challenge(self, db_session, seeded_customer):
        """A session already verified (hydrated from context) is not re-challenged."""
        state = PipelineState(phone=PHONE, identity_verified=True)
        pipeline = VoiceCarePipeline(db=db_session)

        result = await pipeline.agent_order_lookup(state)

        assert result.identity_needs_confirmation is False
        assert result.lookup_successful is True
        assert result.order_data["order_number"] == ORDER_NUMBER


class TestChallengeResponseLeakage:

    @pytest.mark.asyncio
    async def test_challenge_reveals_no_order_number_or_account_name(
        self, db_session, seeded_customer
    ):
        """The RequestIdentity short-circuit must not speak account details."""
        state = PipelineState(phone=PHONE)
        pipeline = VoiceCarePipeline(db=db_session)

        state = await pipeline.agent_order_lookup(state)
        state = await pipeline.agent_resolution(state)

        assert state.recommended_action == "RequestIdentity"
        assert ORDER_NUMBER not in (state.resolution_summary or "")
        assert CUSTOMER_NAME not in (state.resolution_summary or "")

    @pytest.mark.asyncio
    async def test_name_only_lookup_hides_candidate_order(self, db_session, seeded_customer):
        """Name-only match stashes the order as candidate, never as order_data."""
        state = PipelineState(extracted_name="Priya")
        pipeline = VoiceCarePipeline(db=db_session)

        state = await pipeline.agent_order_lookup(state)

        assert state.identity_needs_confirmation is True
        assert state.order_data is None
        assert state.candidate_order_data["order_number"] == ORDER_NUMBER

        state = await pipeline.agent_resolution(state)
        assert state.recommended_action == "RequestIdentity"
        assert ORDER_NUMBER not in (state.resolution_summary or "")


class TestSessionVerificationPersistence:

    def _mock_memory(self, ctx=None):
        memory = MagicMock()
        memory.get_session_context = AsyncMock(return_value=ctx)
        memory.set_session_context = AsyncMock()
        memory.get_conversation_history = AsyncMock(return_value=[])
        memory.store_conversation_turn = AsyncMock()
        memory.get_cache = AsyncMock(return_value=None)
        memory.set_cache = AsyncMock()
        return memory

    def _mock_gemini(self, extracted_name):
        gemini = MagicMock()
        gemini.analyze_intent = AsyncMock(return_value={
            "intent": "order_status",
            "sub_intent": "delivery status",
            "sentiment": "Neutral",
            "priority": "Medium",
            "summary_english": "Order status query",
            "requires_order_lookup": True,
            "extracted_order_id": None,
            "extracted_phone": None,
            "extracted_name": extracted_name,
        })
        gemini.generate_resolution = AsyncMock(return_value={
            "recommended_action": "Inform",
            "resolution_summary": "Order is in transit.",
            "policy_reference": "Shipping policy",
            "internal_note": "",
            "confidence_score": 0.9,
            "requires_human_review": False,
        })
        gemini.generate_response = AsyncMock(return_value={
            "response_text": "Your order is on the way.",
            "response_english": "Your order is on the way.",
            "tone": "Professional",
        })
        return gemini

    @pytest.mark.asyncio
    async def test_verified_turn_persists_identity_to_session_context(
        self, db_session, seeded_customer, mock_bhashini_service, mock_chroma_service
    ):
        """After a corroborated turn, identity_verified=True is stored for the session."""
        memory = self._mock_memory(ctx=None)
        with (
            patch("app.agents.pipeline.get_gemini_service", return_value=self._mock_gemini("Priya")),
            patch("app.agents.pipeline.get_bhashini_service", return_value=mock_bhashini_service),
            patch("app.agents.pipeline.get_chroma_service", return_value=mock_chroma_service),
            patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=memory)),
        ):
            pipeline = VoiceCarePipeline(db=db_session)
            result = await pipeline.run(
                PipelineState(phone=PHONE, raw_text="Where is my order?", language_code="en")
            )

        assert result.identity_verified is True
        memory.set_session_context.assert_called_once()
        saved_ctx = memory.set_session_context.call_args.args[1]
        assert saved_ctx["identity_verified"] is True

    @pytest.mark.asyncio
    async def test_hydrated_verified_session_gets_full_data_without_name(
        self, db_session, seeded_customer, mock_bhashini_service, mock_chroma_service
    ):
        """A later turn in a verified session gets data with no new corroboration."""
        memory = self._mock_memory(ctx={"phone": PHONE, "identity_verified": True})
        with (
            patch("app.agents.pipeline.get_gemini_service", return_value=self._mock_gemini(None)),
            patch("app.agents.pipeline.get_bhashini_service", return_value=mock_bhashini_service),
            patch("app.agents.pipeline.get_chroma_service", return_value=mock_chroma_service),
            patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=memory)),
        ):
            pipeline = VoiceCarePipeline(db=db_session)
            result = await pipeline.run(
                PipelineState(raw_text="What is the status now?", language_code="en")
            )

        assert result.identity_needs_confirmation is False
        assert result.order_data is not None
        assert result.order_data["order_number"] == ORDER_NUMBER

    @pytest.mark.asyncio
    async def test_unverified_turn_persists_unverified(
        self, db_session, seeded_customer, mock_bhashini_service, mock_chroma_service
    ):
        """A challenged turn must not mark the session as verified."""
        memory = self._mock_memory(ctx=None)
        with (
            patch("app.agents.pipeline.get_gemini_service", return_value=self._mock_gemini(None)),
            patch("app.agents.pipeline.get_bhashini_service", return_value=mock_bhashini_service),
            patch("app.agents.pipeline.get_chroma_service", return_value=mock_chroma_service),
            patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=memory)),
        ):
            pipeline = VoiceCarePipeline(db=db_session)
            result = await pipeline.run(
                PipelineState(phone=PHONE, raw_text="Where is my order?", language_code="en")
            )

        assert result.identity_verified is False
        assert result.recommended_action == "RequestIdentity"
        if memory.set_session_context.called:
            saved_ctx = memory.set_session_context.call_args.args[1]
            assert saved_ctx["identity_verified"] is False


class TestNameMatching:

    def test_exact_and_first_name_matches(self):
        assert VoiceCarePipeline._name_matches("Priya Sharma", "Priya Sharma") is True
        assert VoiceCarePipeline._name_matches("priya sharma", "Priya Sharma") is True
        assert VoiceCarePipeline._name_matches("Priya", "Priya Sharma") is True

    def test_non_matches(self):
        assert VoiceCarePipeline._name_matches("Rahul", "Priya Sharma") is False
        assert VoiceCarePipeline._name_matches(None, "Priya Sharma") is False
        assert VoiceCarePipeline._name_matches("Priya", None) is False
        assert VoiceCarePipeline._name_matches("  ", "Priya Sharma") is False
