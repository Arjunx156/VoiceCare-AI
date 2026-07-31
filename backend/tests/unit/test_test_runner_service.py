"""
Unit tests for the Test Runs QA scenario runner (test_runner_service.py):
pass/fail evaluation logic, and the live-vs-mocked Gemini budget switch that
lets a run always finish instead of dying to a Gemini 429.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.state import PipelineState
from app.services import test_runner_service
from app.services.test_runner_service import _StubGeminiService, _evaluate, _run_one_scenario
from data.test_scenarios import TestScenario

from tests.conftest import make_mock_db, patch_all_services


def _scenario(**overrides) -> TestScenario:
    defaults = dict(
        id="s1",
        label="Scenario 1",
        query_text="Where is my order?",
        language="English",
        phone=None,
        order_id=None,
        expected_intent=None,
        expected_escalated=None,
        expected_min_confidence=None,
    )
    defaults.update(overrides)
    return TestScenario(**defaults)


class TestEvaluate:
    def test_observed_when_scenario_has_no_expectations(self):
        """A scenario with no expected_* fields is informational-only — never fails."""
        state = PipelineState(intent="order_status", confidence_score=0.1, is_escalated=True)
        assert _evaluate(_scenario(), state) == "observed"

    def test_passed_when_all_set_expectations_match(self):
        state = PipelineState(intent="refund_status", confidence_score=0.8, is_escalated=False)
        scenario = _scenario(expected_intent="refund_status", expected_escalated=False, expected_min_confidence=0.5)
        assert _evaluate(scenario, state) == "passed"

    def test_failed_when_intent_mismatches(self):
        state = PipelineState(intent="order_status", confidence_score=0.8)
        scenario = _scenario(expected_intent="refund_status")
        assert _evaluate(scenario, state) == "failed"

    def test_failed_when_escalation_mismatches(self):
        state = PipelineState(intent="order_status", is_escalated=False)
        scenario = _scenario(expected_intent="order_status", expected_escalated=True)
        assert _evaluate(scenario, state) == "failed"

    def test_failed_when_confidence_below_minimum(self):
        state = PipelineState(intent="order_status", confidence_score=0.2)
        scenario = _scenario(expected_intent="order_status", expected_min_confidence=0.5)
        assert _evaluate(scenario, state) == "failed"

    def test_failed_when_pipeline_errored_even_with_no_expectations(self):
        state = PipelineState(has_error=True, error="boom")
        assert _evaluate(_scenario(), state) == "failed"


class TestStubGeminiService:
    """The budget-exhausted fallback must never touch the network."""

    @pytest.mark.asyncio
    async def test_stub_returns_deterministic_shapes(self):
        stub = _StubGeminiService()
        intent = await stub.analyze_intent("query", "English")
        resolution = await stub.generate_resolution("q", "order_status", None, "", "Neutral")
        response = await stub.generate_response("q", resolution, "English")

        assert intent["intent"] == "general_inquiry"
        assert resolution["confidence_score"] == 0.3
        assert "Mocked" in response["response_text"]


class TestRunOneScenario:
    @pytest.mark.asyncio
    async def test_uses_real_gemini_when_budget_available(
        self, mock_gemini_service, mock_bhashini_service, mock_chroma_service, mock_memory_service
    ):
        """use_live=True keeps the pipeline on the real (mocked-in-test) GeminiService."""
        db = make_mock_db(scalar_result=None)
        patches = patch_all_services(
            mock_gemini_service, mock_bhashini_service, mock_chroma_service, mock_memory_service
        )
        with patches[0], patches[1], patches[2], patches[3]:
            result, error = await _run_one_scenario(db, uuid.uuid4(), _scenario(), use_live=True)

        assert error is None
        assert result.used_live_api is True
        assert result.intent == "order_status"  # from mock_gemini_intent_response
        mock_gemini_service.analyze_intent.assert_awaited()

    @pytest.mark.asyncio
    async def test_falls_back_to_stub_when_budget_exhausted(
        self, mock_gemini_service, mock_bhashini_service, mock_chroma_service, mock_memory_service
    ):
        """use_live=False must swap in the stub — the real (mocked) Gemini must
        never be called, proving zero live-API cost once the budget is spent."""
        db = make_mock_db(scalar_result=None)
        patches = patch_all_services(
            mock_gemini_service, mock_bhashini_service, mock_chroma_service, mock_memory_service
        )
        with patches[0], patches[1], patches[2], patches[3]:
            result, error = await _run_one_scenario(db, uuid.uuid4(), _scenario(), use_live=False)

        assert error is None
        assert result.used_live_api is False
        assert result.intent == "general_inquiry"
        assert "Mocked" in (result.response_text or "")
        mock_gemini_service.analyze_intent.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_broken_gemini_never_crashes_the_batch(
        self, mock_bhashini_service, mock_chroma_service, mock_memory_service
    ):
        """Each pipeline agent already swallows its own Gemini call failure and
        falls back to a safe default (agent_resolution -> Escalate/confidence 0.0)
        — a scenario against a broken Gemini must still yield a usable result row
        instead of raising out of the runner."""
        broken_gemini = MagicMock()
        broken_gemini.analyze_intent = AsyncMock(side_effect=RuntimeError("quota exceeded"))
        db = make_mock_db(scalar_result=None)
        patches = patch_all_services(
            broken_gemini, mock_bhashini_service, mock_chroma_service, mock_memory_service
        )
        with patches[0], patches[1], patches[2], patches[3]:
            result, error = await _run_one_scenario(db, uuid.uuid4(), _scenario(), use_live=True)

        assert result is not None
        assert result.confidence_score == 0.0  # agent_resolution's own failure fallback


class TestActiveRunLock:
    def test_is_run_active_reflects_module_state(self):
        original = test_runner_service._active_run_id
        try:
            test_runner_service._active_run_id = None
            assert test_runner_service.is_run_active() is False
            test_runner_service._active_run_id = "some-run-id"
            assert test_runner_service.is_run_active() is True
        finally:
            test_runner_service._active_run_id = original
