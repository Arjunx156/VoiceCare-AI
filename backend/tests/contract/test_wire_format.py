"""Wire-format guarantees between the backend and the browser.

The frontend narrows every WebSocket frame in parseWsMessage and renders from
the result. Nothing type-checks across that boundary at build time, so a
renamed field is only caught here or by a user watching a spinner that never
stops. Each test pins one thing the client depends on.
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


async def _collect_frames(state, *, on_deferred=False):
    """Run the pipeline with a capturing transport and return every frame sent."""
    from app.agents.pipeline import VoiceCarePipeline

    frames = []

    async def capture(payload):
        frames.append(payload)

    bhashini = MagicMock()
    bhashini.text_to_speech = AsyncMock(return_value="UklGRg==")
    patches = patch_all_services(MagicMock(), bhashini, MagicMock(), _memory())

    with patches[0], patches[1], patches[2], patches[3]:
        pipeline = VoiceCarePipeline(
            db=make_mock_db(), on_stage_update=capture, turn_id="turn-1"
        )
        if on_deferred:
            await pipeline.run_deferred(state)
        else:
            await pipeline.run_critical(state)
    return frames


class TestStageFrames:

    @pytest.mark.asyncio
    async def test_each_stage_emits_a_start_then_a_timed_done(self):
        """Every stage is bracketed, and only the done frame carries a duration."""
        from app.agents.state import PipelineState

        frames = await _collect_frames(
            PipelineState(raw_text="Where is my order?", language_code="en")
        )
        stage_frames = [f for f in frames if f.get("type") == "stage"]

        starts = [f for f in stage_frames if f["status"] == "start"]
        dones = [f for f in stage_frames if f["status"] == "done"]

        assert len(starts) == len(dones)
        assert all("duration_ms" not in f for f in starts)
        assert all(isinstance(f["duration_ms"], float) for f in dones)

    @pytest.mark.asyncio
    async def test_stage_frames_carry_the_fields_the_client_narrows_on(self):
        """parseWsMessage keys off stage_number; StatusStream needs the rest."""
        from app.agents.state import PipelineState

        frames = await _collect_frames(
            PipelineState(raw_text="Where is my order?", language_code="en")
        )
        stage_frames = [f for f in frames if f.get("type") == "stage"]

        assert stage_frames
        for frame in stage_frames:
            assert isinstance(frame["stage_number"], int)
            assert frame["total_stages"] == 9
            assert isinstance(frame["message"], str) and frame["message"]
            assert frame["status"] in {"start", "done"}
            assert frame["turn_id"] == "turn-1"

    @pytest.mark.asyncio
    async def test_a_stage_that_short_circuits_still_reports_done(self):
        """Agent 5 can return early; the client must not be left waiting.

        The done frame comes from a `finally`, so an early return or an
        exception cannot strand a stage in the running state forever.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        frames = []

        async def capture(payload):
            frames.append(payload)

        async def exploding_agent(state):
            raise RuntimeError("agent blew up")

        patches = patch_all_services(MagicMock(), MagicMock(), MagicMock(), _memory())

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db(), on_stage_update=capture)
            with pytest.raises(RuntimeError):
                await pipeline._staged(5, "Resolving...", exploding_agent, PipelineState())

        assert [f for f in frames if f["status"] == "start"]
        assert [f for f in frames if f["status"] == "done"]


class TestDeferredFrames:

    @pytest.mark.asyncio
    async def test_audio_frame_shape(self):
        """The client reads response_audio_base64 off a frame typed "audio"."""
        from app.agents.state import PipelineState

        state = PipelineState(response_text="Tomorrow.", language_code="en")
        frames = await _collect_frames(state, on_deferred=True)

        audio = [f for f in frames if f.get("type") == "audio"]
        assert len(audio) == 1
        assert audio[0]["response_audio_base64"] == "UklGRg=="
        assert audio[0]["turn_id"] == "turn-1"

    @pytest.mark.asyncio
    async def test_done_frame_is_terminal_and_complete(self):
        """The terminal frame carries is_complete plus the settled ticket + trace.

        The client keeps its spinner up until it sees is_complete, and folds
        these fields into the turn it has already rendered.
        """
        from app.agents.state import PipelineState

        state = PipelineState(response_text="Tomorrow.", language_code="en")
        state.add_trace("Response Generation", 7, "in", "out", duration_ms=12.0)
        frames = await _collect_frames(state, on_deferred=True)

        done = [f for f in frames if f.get("type") == "done"]
        assert len(done) == 1
        frame = done[0]
        assert frame["is_complete"] is True
        assert "ticket_id" in frame
        assert "ticket_created" in frame
        assert isinstance(frame["agent_trace"], list)
        assert isinstance(frame["total_duration_ms"], float)

    @pytest.mark.asyncio
    async def test_done_arrives_after_audio(self):
        """Ordering matters: audio must land before the client stops listening."""
        from app.agents.state import PipelineState

        state = PipelineState(response_text="Tomorrow.", language_code="en")
        frames = await _collect_frames(state, on_deferred=True)

        types = [f.get("type") for f in frames]
        assert types.index("audio") < types.index("done")


class TestResponsePayloadParity:

    def test_builder_supplies_every_documented_response_field(self):
        """The WS answer frame carries the full REST response shape.

        Both transports build from _build_voice_response for exactly this
        reason; a field added to one must not be missing from the other.
        """
        from app.agents.state import PipelineState
        from app.api.voice import _build_voice_response
        from app.schemas.schemas import VoiceQueryResponse

        payload = _build_voice_response(PipelineState(response_text="hi"))

        missing = set(VoiceQueryResponse.model_fields.keys()) - set(payload.keys())
        assert not missing

    def test_response_is_constructible_from_the_builder(self):
        """Every builder value satisfies the schema's types."""
        from app.agents.state import PipelineState
        from app.api.voice import _build_voice_response
        from app.schemas.schemas import VoiceQueryResponse

        payload = _build_voice_response(PipelineState(response_text="hi"))
        assert VoiceQueryResponse(**payload).response_text == "hi"

    def test_total_duration_is_reported(self):
        """The client renders this figure; it must never be absent."""
        from app.agents.state import PipelineState
        from app.api.voice import _build_voice_response

        payload = _build_voice_response(PipelineState(response_text="hi"))
        assert isinstance(payload["total_duration_ms"], float)


class TestAgentTraceShape:

    def test_trace_steps_match_the_frontend_interface(self):
        """AgentTraceStep in api.ts mirrors these keys exactly."""
        from app.agents.state import PipelineState

        state = PipelineState()
        state.add_trace(
            agent_name="Voice Intake",
            stage_number=1,
            input_summary="in",
            output_summary="out",
            decision="text passthrough",
            duration_ms=4.2,
        )

        step = state.agent_trace[0].model_dump(mode="json")
        expected = {
            "agent_name",
            "stage_number",
            "input_summary",
            "output_summary",
            "decision",
            "reasoning",
            "duration_ms",
            "timestamp",
        }
        assert set(step.keys()) == expected
        assert isinstance(step["timestamp"], str)

    @pytest.mark.asyncio
    async def test_persisted_trace_includes_the_final_stage(self):
        """All 9 stages reach the stored ticket, including ticket creation itself.

        The trace was serialised before stage 9 recorded itself, so the admin
        replay silently showed 8 of 9 agents for every ticket ever created.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        patches = patch_all_services(MagicMock(), MagicMock(), MagicMock(), _memory())
        state = PipelineState(
            transcript_english="Where is my order?",
            response_text="Tomorrow.",
            intent="order_status",
        )
        for stage in range(1, 9):
            state.add_trace(f"Agent {stage}", stage, "in", "out", duration_ms=1.0)

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            result = await pipeline.agent_ticket_creation(state)

        stages = [step.stage_number for step in result.agent_trace]
        assert 9 in stages, "stage 9 must record itself before the trace is serialised"
