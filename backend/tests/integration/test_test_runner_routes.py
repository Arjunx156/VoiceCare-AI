"""
HTTP-level tests for the Test Runs API routes: auth is required, a second
concurrent run is rejected with 409 (the single-run lock), an unknown
scenario id is rejected with 400, and the scenario catalog endpoint reflects
the real static catalog.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.db.models import TestRun
from data.test_scenarios import TEST_SCENARIOS


def _fake_run(total=1) -> TestRun:
    return TestRun(
        run_id=uuid.uuid4(),
        status="running",
        total_scenarios=total,
        completed_scenarios=0,
        live_call_count=0,
        mock_fallback_count=0,
        started_at=datetime.utcnow(),
        created_by="agent@test.com",
    )


class TestScenarioCatalog:
    @pytest.mark.asyncio
    async def test_lists_the_real_static_catalog(self, authed_client):
        response = await authed_client.get("/api/test-runs/scenarios")

        assert response.status_code == 200
        ids = {s["id"] for s in response.json()}
        assert ids == {s.id for s in TEST_SCENARIOS}

    @pytest.mark.asyncio
    async def test_requires_admin_auth(self):
        """No require_admin override here — a real 401 for a missing token."""
        from httpx import AsyncClient, ASGITransport
        from main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            response = await client.get("/api/test-runs/scenarios")
        assert response.status_code == 401


class TestStartRun:
    @pytest.mark.asyncio
    async def test_starts_a_run_and_returns_its_id(self, authed_client):
        with patch(
            "app.api.test_runner.test_runner_service.start_test_run",
            new=AsyncMock(return_value=_fake_run(total=3)),
        ) as mock_start:
            response = await authed_client.post("/api/test-runs/", json={"scenario_ids": None})

        assert response.status_code == 201
        assert response.json()["total_scenarios"] == 3
        mock_start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_conflict_when_a_run_is_already_active(self, authed_client):
        with patch(
            "app.api.test_runner.test_runner_service.start_test_run",
            new=AsyncMock(side_effect=RuntimeError("A test run is already active.")),
        ):
            response = await authed_client.post("/api/test-runs/", json={})

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_bad_request_for_unknown_scenario_ids(self, authed_client):
        with patch(
            "app.api.test_runner.test_runner_service.start_test_run",
            new=AsyncMock(side_effect=ValueError("No matching scenarios found.")),
        ):
            response = await authed_client.post(
                "/api/test-runs/", json={"scenario_ids": ["not-a-real-scenario"]}
            )

        assert response.status_code == 400


class TestGetRun:
    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_run(self, authed_client):
        response = await authed_client.get(f"/api/test-runs/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_400_for_a_malformed_run_id(self, authed_client):
        response = await authed_client.get("/api/test-runs/not-a-uuid")
        assert response.status_code == 400


class TestCancelRun:
    @pytest.mark.asyncio
    async def test_cancel_returns_409_when_not_active(self, authed_client):
        with patch(
            "app.api.test_runner.test_runner_service.cancel_test_run",
            new=AsyncMock(return_value=False),
        ):
            response = await authed_client.post(f"/api/test-runs/{uuid.uuid4()}/cancel")

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_cancel_succeeds_when_active(self, authed_client):
        with patch(
            "app.api.test_runner.test_runner_service.cancel_test_run",
            new=AsyncMock(return_value=True),
        ):
            response = await authed_client.post(f"/api/test-runs/{uuid.uuid4()}/cancel")

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
