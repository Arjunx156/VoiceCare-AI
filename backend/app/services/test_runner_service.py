"""
CommerceMind VoiceCare AI — Test Runner Service
Drives QA scenarios (data/test_scenarios.py) through the real pipeline via
run_critical() only — agents 1-7. That structurally guarantees a run never
reaches agent 8 (TTS/Bhashini) or agent 9 (ticket creation), so it can never
write a SupportTicket/SupportResolution row and never touches Bhashini.
Results land in TestRun/TestCaseResult, which have no FK into the ticket schema.
"""

import asyncio
import time
import uuid
import structlog
from datetime import datetime
from typing import Optional

from app.core.config import get_settings
from app.agents.state import PipelineState
from app.agents.pipeline import VoiceCarePipeline
from app.db.models import TestRun, TestCaseResult
from data.test_scenarios import TEST_SCENARIOS, TestScenario

logger = structlog.get_logger()

# One run at a time — a QA batch should never be able to stack concurrent
# live-API usage. A bare module attribute (not a DB flag) so a crashed process
# can't leave a permanently "locked" run behind after a restart.
_active_run_id: Optional[str] = None


class _StubGeminiService:
    """Zero-cost, zero-network substitute once a run's live-call budget is spent.

    Returns the same fallback shapes GeminiService itself already falls back to
    on a real error (gemini_service.py's analyze_intent/generate_resolution/
    generate_response except blocks) — no new response contract to invent.
    """

    async def analyze_intent(self, query: str, language: str, conversation_history: list = None) -> dict:
        return {
            "intent": "general_inquiry",
            "sub_intent": "test run — budget exhausted, mocked",
            "sentiment": "Neutral",
            "priority": "Medium",
            "summary_english": query,
            "requires_order_lookup": False,
            "extracted_order_id": None,
            "extracted_phone": None,
            "extracted_name": None,
        }

    async def generate_resolution(
        self, query, intent, order_data, policy_context, sentiment, conversation_history=None
    ) -> dict:
        return {
            "recommended_action": "Inform",
            "resolution_summary": "Test run — budget exhausted, mocked response.",
            "policy_reference": "Standard Practice",
            "internal_note": "Gemini call budget exhausted for this test run; mocked.",
            "confidence_score": 0.3,
            "requires_human_review": True,
            "reason_for_action": "Test run mock fallback",
        }

    async def generate_response(
        self, query, resolution, language, customer_name="Customer", conversation_history=None
    ) -> dict:
        return {
            "response_text": "[Mocked — Gemini call budget exhausted for this test run.]",
            "response_english": "[Mocked — Gemini call budget exhausted for this test run.]",
            "tone": "Apologetic",
        }


def is_run_active() -> bool:
    return _active_run_id is not None


def _evaluate(scenario: TestScenario, state: PipelineState) -> str:
    """Pass/fail/observed for one scenario outcome.

    A scenario with no expectations set is informational-only — it always
    comes back "observed", never "failed".
    """
    if state.has_error:
        return "failed"

    has_expectation = (
        scenario.expected_intent is not None
        or scenario.expected_escalated is not None
        or scenario.expected_min_confidence is not None
    )
    if not has_expectation:
        return "observed"

    if scenario.expected_intent is not None and state.intent != scenario.expected_intent:
        return "failed"
    if scenario.expected_escalated is not None and state.is_escalated != scenario.expected_escalated:
        return "failed"
    if (
        scenario.expected_min_confidence is not None
        and state.confidence_score < scenario.expected_min_confidence
    ):
        return "failed"
    return "passed"


async def start_test_run(scenario_ids: Optional[list[str]], created_by: str) -> TestRun:
    """Create the TestRun row and spawn the background scenario loop.

    Raises RuntimeError if a run is already active, ValueError if the
    requested scenario_ids match nothing — the API route translates both into
    the appropriate HTTP error.
    """
    from app.core.database import async_session

    global _active_run_id
    if _active_run_id is not None:
        raise RuntimeError("A test run is already active.")

    scenarios = (
        [s for s in TEST_SCENARIOS if s.id in scenario_ids] if scenario_ids else list(TEST_SCENARIOS)
    )
    if not scenarios:
        raise ValueError("No matching scenarios found.")

    run = TestRun(
        run_id=uuid.uuid4(),
        status="running",
        total_scenarios=len(scenarios),
        created_by=created_by,
    )
    async with async_session() as db:
        db.add(run)
        await db.commit()
        await db.refresh(run)

    _active_run_id = str(run.run_id)
    asyncio.create_task(_execute_run(run.run_id, scenarios))
    return run


async def cancel_test_run(run_id: uuid.UUID) -> bool:
    """Flip a running run to cancelled; the background loop stops after the
    in-flight scenario. Returns False if the run wasn't active."""
    from app.core.database import async_session

    async with async_session() as db:
        run = await db.get(TestRun, run_id)
        if run is None or run.status != "running":
            return False
        run.status = "cancelled"
        run.completed_at = datetime.utcnow()
        await db.commit()
        return True


async def _execute_run(run_id: uuid.UUID, scenarios: list[TestScenario]) -> None:
    from app.core.database import async_session

    global _active_run_id
    settings = get_settings()
    budget = settings.test_run_gemini_call_budget
    live_calls_used = 0

    try:
        for scenario in scenarios:
            async with async_session() as db:
                run = await db.get(TestRun, run_id)
                if run is None or run.status == "cancelled":
                    break

                use_live = live_calls_used + 3 <= budget
                result, error = await _run_one_scenario(db, run_id, scenario, use_live)

                if use_live and error is None:
                    live_calls_used += 3
                    run.live_call_count += 3
                else:
                    run.mock_fallback_count += 1

                db.add(result)
                run.completed_scenarios += 1
                await db.commit()

        async with async_session() as db:
            run = await db.get(TestRun, run_id)
            if run and run.status == "running":
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                await db.commit()
    except Exception:
        logger.error("test_run_failed", run_id=str(run_id), exc_info=True)
        async with async_session() as db:
            run = await db.get(TestRun, run_id)
            if run:
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                await db.commit()
    finally:
        _active_run_id = None


async def _run_one_scenario(
    db, run_id: uuid.UUID, scenario: TestScenario, use_live: bool
) -> tuple[TestCaseResult, Optional[str]]:
    start = time.time()

    state = PipelineState(
        raw_text=scenario.query_text,
        language_detected=scenario.language,
        phone=scenario.phone,
        input_order_id=scenario.order_id,
    )

    pipeline = VoiceCarePipeline(db=db)
    if not use_live:
        pipeline.gemini = _StubGeminiService()

    error_detail = None
    try:
        state = await pipeline.run_critical(state)
        if state.has_error:
            error_detail = state.error
    except Exception as exc:
        state.has_error = True
        error_detail = str(exc)
        logger.warning("test_scenario_failed", scenario_id=scenario.id, error=str(exc))

    status = _evaluate(scenario, state)
    latency_ms = round((time.time() - start) * 1000)

    result = TestCaseResult(
        result_id=uuid.uuid4(),
        run_id=run_id,
        scenario_id=scenario.id,
        scenario_label=scenario.label,
        status=status,
        used_live_api=use_live and error_detail is None,
        intent=state.intent,
        sentiment=state.sentiment,
        priority=state.priority,
        is_escalated=state.is_escalated,
        confidence_score=state.confidence_score,
        response_text=state.response_text,
        latency_ms=latency_ms,
        error_detail=error_detail,
    )
    return result, error_detail
