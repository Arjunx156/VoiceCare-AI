"""Defences against leaking data to the wrong person.

The voice endpoint is unauthenticated by design — a customer calls in and
speaks. That makes identity corroboration and output hygiene the only things
standing between a caller and someone else's order history.
"""

from unittest.mock import AsyncMock, MagicMock

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


class TestIdentityCorroboration:
    """A phone number is a claim, not proof — anyone can speak someone else's."""

    @pytest.mark.asyncio
    async def test_phone_alone_does_not_unlock_order_data(self):
        """An uncorroborated phone lookup is challenged, not answered."""
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState
        from app.db.models import Order, User

        user = MagicMock(spec=User)
        user.user_id = "u-1"
        user.name = "Priya Sharma"
        user.phone = "9876543210"
        user.preferred_language = "Hindi"
        user.customer_segment = "Premium"

        order = MagicMock(spec=Order)
        order.order_id = "o-1"
        order.order_number = "ORD-7K3F"
        order.order_date = "2026-07-01"
        order.status = "Shipped"
        order.total_amount = 2500

        db = make_mock_db()
        results = [user, order]
        call = {"n": 0}

        async def execute(*args, **kwargs):
            result = MagicMock()
            value = results[call["n"]] if call["n"] < len(results) else None
            call["n"] += 1
            result.scalar_one_or_none = MagicMock(return_value=value)
            result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
            return result

        db.execute = AsyncMock(side_effect=execute)
        patches = patch_all_services(MagicMock(), MagicMock(), MagicMock(), _memory())

        state = PipelineState(phone="9876543210", summary_english="where is my order")

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=db)
            result = await pipeline.agent_order_lookup(state)

        assert result.identity_needs_confirmation is True
        assert result.order_data is None

    def test_name_matching_rejects_a_different_person(self):
        """Corroboration by name does not accept an unrelated name."""
        from app.agents.pipeline import VoiceCarePipeline

        assert VoiceCarePipeline._name_matches("Priya Sharma", "Priya Sharma") is True
        assert VoiceCarePipeline._name_matches("Priya", "Priya Sharma") is True
        assert VoiceCarePipeline._name_matches("Rahul Verma", "Priya Sharma") is False
        assert VoiceCarePipeline._name_matches(None, "Priya Sharma") is False
        assert VoiceCarePipeline._name_matches("", "Priya Sharma") is False


class TestSecretHygiene:

    def test_response_payload_carries_no_internal_identifiers(self):
        """Nothing in the customer payload exposes credentials or internals."""
        from app.agents.state import PipelineState
        from app.api.voice import _build_voice_response

        payload = _build_voice_response(
            PipelineState(response_text="hi", internal_note="staff-only note")
        )

        forbidden = {"internal_note", "api_key", "password", "token", "user_id"}
        assert not (forbidden & set(payload.keys()))

    def test_settings_are_not_serialisable_into_a_response(self):
        """Config values never travel in a pipeline payload."""
        import json

        from app.agents.state import PipelineState
        from app.api.voice import _build_voice_response
        from app.core.config import get_settings

        settings = get_settings()
        serialised = json.dumps(_build_voice_response(PipelineState(response_text="hi")))

        for secret in (
            settings.gemini_api_key,
            settings.groq_api_key,
            settings.bhashini_api_key,
        ):
            if secret:
                assert secret not in serialised


class TestStageFrameHygiene:

    @pytest.mark.asyncio
    async def test_progress_frames_leak_no_customer_data(self):
        """Stage frames are status only — no transcript, no order details.

        They are the highest-frequency thing on the wire and the easiest place
        for a debugging field to be added and forgotten.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        frames = []

        async def capture(payload):
            frames.append(payload)

        secret_utterance = "my order 1234 to 42 Baker Street"
        patches = patch_all_services(MagicMock(), MagicMock(), MagicMock(), _memory())
        state = PipelineState(raw_text=secret_utterance, language_code="en", phone="9876543210")

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db(), on_stage_update=capture)
            await pipeline._staged(1, "Listening...", pipeline.agent_voice_intake, state)

        assert frames, "the stage wrapper must emit frames for this to prove anything"
        allowed_keys = {
            "type", "stage_number", "total_stages", "message",
            "is_complete", "status", "duration_ms", "turn_id",
        }
        for frame in frames:
            assert set(frame.keys()) <= allowed_keys
            assert secret_utterance not in str(frame)
            assert "9876543210" not in str(frame)


class TestTurnIsolation:

    @pytest.mark.asyncio
    async def test_frames_are_stamped_with_their_turn(self):
        """Every frame identifies its turn.

        Deferred stages keep emitting after the next turn may have started on
        the same socket; without this the client cannot tell them apart and
        would fold one customer's ticket into another turn's display.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        frames = []

        async def capture(payload):
            frames.append(payload)

        patches = patch_all_services(MagicMock(), MagicMock(), MagicMock(), _memory())

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(
                db=make_mock_db(), on_stage_update=capture, turn_id="turn-abc"
            )
            await pipeline._staged(
                1,
                "Listening...",
                pipeline.agent_voice_intake,
                PipelineState(raw_text="Where is my order?", language_code="en"),
            )

        assert frames
        assert all(f["turn_id"] == "turn-abc" for f in frames)
