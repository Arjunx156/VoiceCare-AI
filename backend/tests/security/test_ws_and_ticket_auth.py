"""
WebSocket happy-path contract test and real-JWT enforcement tests for the
ticket routes (previous ticket tests bypassed auth via dependency_overrides,
so the actual 401 path was never exercised end-to-end).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.state import PipelineState


class TestWebSocketHappyPath:

    def test_ws_returns_full_response_payload(self):
        from starlette.testclient import TestClient

        from app.api import voice
        from main import app

        completed = PipelineState(
            raw_text="Where is my order?",
            response_text="Your order arrives tomorrow.",
            intent="order_status",
            recommended_action="Inform",
            confidence_score=0.9,
            ticket_created=True,
        )

        mock_db = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        session_cm = MagicMock()
        session_cm.__aenter__ = AsyncMock(return_value=mock_db)
        session_cm.__aexit__ = AsyncMock(return_value=False)

        voice._ws_connections.clear()
        try:
            with (
                patch("app.core.database.async_session", return_value=session_cm),
                patch("app.api.voice.VoiceCarePipeline") as MockPipeline,
            ):
                # The WS delivers the answer after agents 1-7; agents 8-9 run in
                # a background task and report via later frames. Session context
                # is hydrated concurrently with the history read.
                MockPipeline.return_value._hydrate_session_context = AsyncMock()
                MockPipeline.return_value.run_critical = AsyncMock(return_value=completed)
                MockPipeline.return_value.run_deferred = AsyncMock(return_value=completed)
                client = TestClient(app)
                with client.websocket_connect("/api/voice/ws/happy-session") as ws:
                    ws.send_json({"text": "Where is my order?"})
                    message = ws.receive_json()
        finally:
            voice._ws_connections.clear()

        assert message["type"] == "response"
        assert message["response_text"] == "Your order arrives tomorrow."
        assert message["intent"] == "order_status"
        # is_complete now rides on the terminal `done` frame — the answer frame
        # advertises what is still outstanding instead.
        assert message["is_complete"] is False
        assert set(message["pending"]) == {"tts", "ticket"}
        assert message["turn_id"]
        # Contract: WS payload carries every REST response field
        from app.schemas.schemas import VoiceQueryResponse

        missing = set(VoiceQueryResponse.model_fields.keys()) - set(message.keys())
        assert not missing


class TestTicketRoutesRealJwtEnforcement:

    @pytest.mark.asyncio
    async def test_tickets_list_requires_token(self, test_client):
        response = await test_client.get("/api/tickets/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_tickets_list_rejects_garbage_token(self, test_client):
        response = await test_client.get(
            "/api/tickets/", headers={"Authorization": "Bearer not.a.jwt"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_tickets_list_accepts_real_jwt(self, test_client):
        """A token signed with the configured secret passes require_admin."""
        from app.api.auth import _create_token

        token = _create_token("admin@voicecare.ai")
        response = await test_client.get(
            "/api/tickets/", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_customers_routes_also_enforced(self, test_client):
        response = await test_client.get("/api/customers/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_metrics_requires_token(self, test_client):
        response = await test_client.get("/metrics")
        assert response.status_code == 401
