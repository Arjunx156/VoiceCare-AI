"""
CommerceMind VoiceCare AI — Test Runs API Routes
Isolated QA scenario runner for the dashboard's "Test Runs" tab. Never reads
or writes SupportTicket/SupportResolution — see test_runner_service.py.
"""

import uuid
import structlog
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.auth import require_admin
from app.core.rate_limit import enforce as enforce_rate_limit, get_client_ip
from app.db.models import TestRun, TestCaseResult
from app.services import test_runner_service
from data.test_scenarios import TEST_SCENARIOS

logger = structlog.get_logger()

_TEST_RUN_RATE_LIMIT = 20
_TEST_RUN_RATE_WINDOW = 60


async def _test_run_rate_limit(request: Request) -> None:
    await enforce_rate_limit(
        key=f"rate_limit:test_runs:{get_client_ip(request)}",
        limit=_TEST_RUN_RATE_LIMIT,
        window_seconds=_TEST_RUN_RATE_WINDOW,
        detail="Too many requests. Please slow down.",
    )


router = APIRouter(
    prefix="/api/test-runs",
    tags=["test-runs"],
    dependencies=[Depends(require_admin), Depends(_test_run_rate_limit)],
)


class StartRunBody(BaseModel):
    scenario_ids: Optional[List[str]] = None


class ScenarioSummary(BaseModel):
    id: str
    label: str
    language: str
    expected_intent: Optional[str] = None


class TestCaseResultOut(BaseModel):
    result_id: uuid.UUID
    scenario_id: str
    scenario_label: str
    status: str
    used_live_api: bool
    intent: Optional[str]
    sentiment: Optional[str]
    priority: Optional[str]
    is_escalated: bool
    confidence_score: Optional[float]
    response_text: Optional[str]
    latency_ms: Optional[int]
    error_detail: Optional[str]

    model_config = {"from_attributes": True}


class TestRunOut(BaseModel):
    run_id: uuid.UUID
    status: str
    total_scenarios: int
    completed_scenarios: int
    live_call_count: int
    mock_fallback_count: int
    started_at: datetime
    completed_at: Optional[datetime]
    created_by: str
    results: List[TestCaseResultOut] = []

    model_config = {"from_attributes": True}


@router.get("/scenarios", response_model=List[ScenarioSummary])
async def list_scenarios():
    """The static QA scenario catalog available to run."""
    return [
        ScenarioSummary(
            id=s.id, label=s.label, language=s.language, expected_intent=s.expected_intent
        )
        for s in TEST_SCENARIOS
    ]


@router.post("/", response_model=TestRunOut, status_code=201)
async def start_run(
    body: StartRunBody,
    admin_email: str = Depends(require_admin),
):
    """Start a QA test run. 409 if one is already active."""
    try:
        run = await test_runner_service.start_test_run(
            scenario_ids=body.scenario_ids, created_by=admin_email
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    logger.info("test_run_started", run_id=str(run.run_id), agent=admin_email)
    return TestRunOut.model_validate(run)


@router.get("/", response_model=List[TestRunOut])
async def list_runs(db: AsyncSession = Depends(get_db)):
    """History of past and active test runs, most recent first."""
    result = await db.execute(select(TestRun).order_by(TestRun.started_at.desc()).limit(50))
    runs = result.scalars().all()
    return [TestRunOut.model_validate(r) for r in runs]


@router.get("/{run_id}", response_model=TestRunOut)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Run status plus every scenario result recorded so far — used for polling."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")

    run = await db.get(TestRun, rid)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return TestRunOut.model_validate(run)


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: str, admin_email: str = Depends(require_admin)):
    """Stop a running test run after the in-flight scenario finishes."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")

    cancelled = await test_runner_service.cancel_test_run(rid)
    if not cancelled:
        raise HTTPException(status_code=409, detail="Run is not currently active")

    logger.info("test_run_cancelled", run_id=run_id, agent=admin_email)
    return {"run_id": run_id, "status": "cancelled"}
