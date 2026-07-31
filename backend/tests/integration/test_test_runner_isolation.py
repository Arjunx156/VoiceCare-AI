"""
Integration test for the Test Runs QA scenario runner against a real (in-memory
SQLite) database: proves the budget-exhaustion fallback lets a run always
finish, and that scenario runs never create a SupportTicket row — the entire
reason results live in their own test_runs/test_case_results tables instead of
reusing the ticket schema.
"""

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.db.models import SupportTicket, TestRun
from app.services import test_runner_service
from data.test_scenarios import TestScenario

from tests.conftest import patch_all_services

SCENARIOS = [
    TestScenario(id=f"s{i}", label=f"Scenario {i}", query_text="Where is my order?", language="English")
    for i in range(4)
]


@pytest.fixture(autouse=True)
def _reset_active_run():
    test_runner_service._active_run_id = None
    yield
    test_runner_service._active_run_id = None


@pytest.fixture
def mocked_services(mock_gemini_service, mock_bhashini_service, mock_chroma_service, mock_memory_service):
    patches = patch_all_services(
        mock_gemini_service, mock_bhashini_service, mock_chroma_service, mock_memory_service
    )
    with patches[0], patches[1], patches[2], patches[3]:
        yield


async def _seed_run(sessionmaker_, total_scenarios: int) -> uuid.UUID:
    run_id = uuid.uuid4()
    async with sessionmaker_() as db:
        db.add(TestRun(
            run_id=run_id, status="running", total_scenarios=total_scenarios,
            created_by="agent@test.com",
        ))
        await db.commit()
    return run_id


class TestBudgetFallbackCompletesTheRun:

    @pytest.mark.asyncio
    async def test_all_scenarios_run_live_within_default_budget(
        self, monkeypatch, sessionmaker_, mocked_services
    ):
        """Default budget (30 calls / 10 scenarios) comfortably covers 4 scenarios
        (12 calls) — every one should hit the (mocked-in-test) real Gemini."""
        monkeypatch.setattr("app.core.database.async_session", sessionmaker_)

        run_id = await _seed_run(sessionmaker_, len(SCENARIOS))
        await test_runner_service._execute_run(run_id, SCENARIOS)

        async with sessionmaker_() as db:
            run = await db.get(TestRun, run_id)

        assert run.status == "completed"
        assert run.completed_scenarios == len(SCENARIOS)
        assert run.live_call_count == len(SCENARIOS) * 3
        assert run.mock_fallback_count == 0
        assert len(run.results) == len(SCENARIOS)

    @pytest.mark.asyncio
    async def test_run_completes_after_exhausting_a_tight_budget(
        self, monkeypatch, sessionmaker_, mocked_services
    ):
        """With a budget covering only 1 scenario, the run must still finish —
        the remaining 3 fall back to the mocked stub instead of erroring out."""
        monkeypatch.setattr("app.core.database.async_session", sessionmaker_)
        monkeypatch.setattr(
            test_runner_service, "get_settings",
            lambda: SimpleNamespace(test_run_gemini_call_budget=3),
        )

        run_id = await _seed_run(sessionmaker_, len(SCENARIOS))
        await test_runner_service._execute_run(run_id, SCENARIOS)

        async with sessionmaker_() as db:
            run = await db.get(TestRun, run_id)

        assert run.status == "completed"
        assert run.completed_scenarios == len(SCENARIOS)
        assert run.live_call_count == 3
        assert run.mock_fallback_count == len(SCENARIOS) - 1
        live_flags = [r.used_live_api for r in run.results]
        assert live_flags.count(True) == 1
        assert live_flags.count(False) == len(SCENARIOS) - 1

    @pytest.mark.asyncio
    async def test_run_never_creates_a_support_ticket(
        self, monkeypatch, sessionmaker_, mocked_services
    ):
        """The whole point of a separate table: running scenarios must never
        write to support_tickets, no matter how many scenarios run. Compares
        the count before/after rather than asserting zero, since this shared
        in-memory DB may already carry committed tickets from other tests
        that ran earlier in the same session."""
        monkeypatch.setattr("app.core.database.async_session", sessionmaker_)

        async with sessionmaker_() as db:
            before = len((await db.execute(select(SupportTicket))).scalars().all())

        run_id = await _seed_run(sessionmaker_, len(SCENARIOS))
        await test_runner_service._execute_run(run_id, SCENARIOS)

        async with sessionmaker_() as db:
            after = len((await db.execute(select(SupportTicket))).scalars().all())

        assert after == before

    @pytest.mark.asyncio
    async def test_cancelled_run_stops_before_remaining_scenarios(
        self, monkeypatch, sessionmaker_, mocked_services
    ):
        """cancel_test_run flips status; _execute_run must stop picking up new
        scenarios once it sees that on its next per-scenario DB check."""
        monkeypatch.setattr("app.core.database.async_session", sessionmaker_)

        run_id = await _seed_run(sessionmaker_, len(SCENARIOS))
        cancelled = await test_runner_service.cancel_test_run(run_id)
        assert cancelled is True

        await test_runner_service._execute_run(run_id, SCENARIOS)

        async with sessionmaker_() as db:
            run = await db.get(TestRun, run_id)

        assert run.status == "cancelled"
        assert run.completed_scenarios == 0
