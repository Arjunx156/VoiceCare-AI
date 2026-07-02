"""
Tests for error hygiene — internal failure details must never reach clients,
and a failed ticket write must surface as ticket_created=False, not a 500.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.state import PipelineState


class TestVoiceQueryErrorLeakage:

    @pytest.mark.asyncio
    async def test_500_does_not_echo_internal_error(self, test_client):
        """state.error (raw exception text) stays server-side."""
        failed = PipelineState(
            raw_text="hi",
            has_error=True,
            error="asyncpg.InternalServerError: connection to db-internal-host:5432 refused",
        )
        with patch(
            "app.api.voice.VoiceCarePipeline.run",
            new=AsyncMock(return_value=failed),
        ):
            response = await test_client.post("/api/voice/query", json={"text": "hi"})

        assert response.status_code == 500
        body = response.text
        assert "asyncpg" not in body
        assert "db-internal-host" not in body
        assert response.json()["detail"] == "Voice query processing failed. Please try again."


class TestHealthEndpointLeakage:

    @pytest.mark.asyncio
    async def test_health_hides_dependency_error_details(self, test_client):
        """A failing dependency reports a generic 'error', not the exception."""
        mock_chroma = MagicMock()
        mock_chroma.get_collection_count = MagicMock(return_value=5)

        with (
            patch(
                "app.core.database.async_session",
                new=MagicMock(side_effect=Exception("connection to 10.0.0.7 failed: bad password")),
            ),
            patch(
                "app.services.chroma_service.get_chroma_service",
                return_value=mock_chroma,
            ),
        ):
            response = await test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["checks"]["database"] == "error"
        assert data["status"] == "degraded"
        assert "10.0.0.7" not in response.text
        assert "bad password" not in response.text


class TestTicketPersistFailure:

    @pytest.mark.asyncio
    async def test_ticket_write_failure_is_non_fatal(self):
        """A failed ticket write leaves the state error-free with ticket_created=False."""
        from app.agents.pipeline import VoiceCarePipeline

        mock_db = MagicMock()
        mock_db.begin_nested = MagicMock(side_effect=Exception("disk full"))

        state = PipelineState(
            raw_text="hi",
            transcript_english="hi",
            response_text="answer",
            intent="general_inquiry",
        )
        pipeline = VoiceCarePipeline(db=mock_db)
        result = await pipeline.agent_ticket_creation(state)

        assert result.has_error is False
        assert result.error is None
        assert result.ticket_created is False
        assert result.ticket_id is None
        assert result.ticket_number is None

    @pytest.mark.asyncio
    async def test_response_reports_ticket_created_false(self, test_client):
        """The API response carries ticket_created so the client stays truthful."""
        state = PipelineState(
            raw_text="hi",
            response_text="answer",
            intent="general_inquiry",
            recommended_action="Inform",
            ticket_created=False,
        )
        with patch(
            "app.api.voice.VoiceCarePipeline.run",
            new=AsyncMock(return_value=state),
        ):
            response = await test_client.post("/api/voice/query", json={"text": "hi"})

        assert response.status_code == 200
        assert response.json()["ticket_created"] is False


class TestSessionClearEndpoint:

    @pytest.mark.asyncio
    async def test_invalid_session_id_rejected(self, test_client):
        response = await test_client.delete("/api/voice/session/not-a-uuid")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_valid_session_id_cleared(self, test_client):
        session_id = str(uuid.uuid4())
        response = await test_client.delete(f"/api/voice/session/{session_id}")
        assert response.status_code == 200
        assert response.json()["cleared"] is True


class TestSessionHistoryEndpoint:

    @pytest.mark.asyncio
    async def test_invalid_session_id_rejected(self, test_client):
        response = await test_client.get("/api/voice/session/not-a-uuid/history")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_unknown_session_returns_empty_turns(self, test_client):
        session_id = str(uuid.uuid4())
        response = await test_client.get(f"/api/voice/session/{session_id}/history")
        assert response.status_code == 200
        assert response.json()["turns"] == []

    @pytest.mark.asyncio
    async def test_returns_stored_turns_in_order(self, test_client):
        from app.services.memory_service import get_memory_service

        session_id = str(uuid.uuid4())
        memory = await get_memory_service()
        await memory.store_conversation_turn(session_id, "customer", "मेरा ऑर्डर कहाँ है?")
        await memory.store_conversation_turn(session_id, "ai", "Your order ships tomorrow.")

        response = await test_client.get(f"/api/voice/session/{session_id}/history")

        assert response.status_code == 200
        turns = response.json()["turns"]
        assert [t["role"] for t in turns] == ["customer", "ai"]
        assert turns[0]["content"] == "मेरा ऑर्डर कहाँ है?"
        assert turns[1]["content"] == "Your order ships tomorrow."

    @pytest.mark.asyncio
    async def test_cleared_session_has_no_history(self, test_client):
        from app.services.memory_service import get_memory_service

        session_id = str(uuid.uuid4())
        memory = await get_memory_service()
        await memory.store_conversation_turn(session_id, "customer", "hello")

        await test_client.delete(f"/api/voice/session/{session_id}")
        response = await test_client.get(f"/api/voice/session/{session_id}/history")

        assert response.status_code == 200
        assert response.json()["turns"] == []


class TestWebSocketValidationErrors:

    def test_validation_error_returns_field_messages_only(self):
        from starlette.testclient import TestClient

        from app.api import voice
        from main import app

        voice._ws_connections.clear()
        client = TestClient(app)
        try:
            with client.websocket_connect("/api/voice/ws/ws-validation-test") as session:
                session.send_json({"text": 12345})
                message = session.receive_json()
        finally:
            voice._ws_connections.clear()

        assert message["error"] == "VALIDATION_ERROR"
        assert isinstance(message["detail"], list)
        assert message["detail"][0]["field"] == "text"
        assert "message" in message["detail"][0]
        # The submitted value must not be echoed back
        assert "12345" not in json.dumps(message)
