"""
Tests for the shared rate limiter — unit behavior of app/core/rate_limit.py,
endpoint-level 429 enforcement on the voice REST route (anonymous + phone),
and the WebSocket origin / connection-cap / message-budget protections.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Unit: core enforce/count_hit behavior
# ---------------------------------------------------------------------------

class TestRateLimitCore:

    @pytest.mark.asyncio
    async def test_count_hit_increments(self):
        from app.core.rate_limit import count_hit

        assert await count_hit("rate_limit:test:a", 60) == 1
        assert await count_hit("rate_limit:test:a", 60) == 2
        assert await count_hit("rate_limit:test:b", 60) == 1

    @pytest.mark.asyncio
    async def test_enforce_raises_429_over_limit(self):
        from app.core.rate_limit import enforce

        for _ in range(3):
            await enforce("rate_limit:test:c", limit=3, window_seconds=60, detail="slow down")

        with pytest.raises(HTTPException) as exc_info:
            await enforce("rate_limit:test:c", limit=3, window_seconds=60, detail="slow down")

        assert exc_info.value.status_code == 429
        assert exc_info.value.headers["Retry-After"] == "60"

    @pytest.mark.asyncio
    async def test_degrades_to_in_process_counter_when_store_fails(self):
        """A broken store must not disable limiting — the fallback counts."""
        from app.core import rate_limit

        with patch(
            "app.core.rate_limit.get_memory_service",
            new=AsyncMock(side_effect=RuntimeError("redis down")),
        ):
            counts = [await rate_limit.count_hit("rate_limit:test:d", 60) for _ in range(3)]

        assert counts == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_fallback_window_resets(self):
        from app.core import rate_limit

        with patch(
            "app.core.rate_limit.get_memory_service",
            new=AsyncMock(side_effect=RuntimeError("redis down")),
        ):
            await rate_limit.count_hit("rate_limit:test:e", 60)
            # Simulate window expiry by rewinding the stored window start
            start, count = rate_limit._fallback_counters["rate_limit:test:e"]
            rate_limit._fallback_counters["rate_limit:test:e"] = (start - 61, count)
            assert await rate_limit.count_hit("rate_limit:test:e", 60) == 1


# ---------------------------------------------------------------------------
# Endpoint: REST voice per-IP (anonymous) and per-phone limits
# ---------------------------------------------------------------------------

def _completed_state():
    from app.agents.state import PipelineState

    return PipelineState(
        raw_text="hi",
        response_text="hello",
        intent="general_inquiry",
        recommended_action="Inform",
    )


class TestVoiceEndpointRateLimit:

    @pytest.mark.asyncio
    async def test_anonymous_requests_are_rate_limited(self, test_client):
        """The per-IP limit now applies with no phone supplied (was a bypass)."""
        from app.core.config import get_settings

        ip_limit = get_settings().voice_rate_limit_ip_per_minute
        with patch(
            "app.api.voice.VoiceCarePipeline.run",
            new=AsyncMock(return_value=_completed_state()),
        ):
            for _ in range(ip_limit):
                response = await test_client.post("/api/voice/query", json={"text": "hi"})
                assert response.status_code == 200

            response = await test_client.post("/api/voice/query", json={"text": "hi"})

        assert response.status_code == 429
        assert "Retry-After" in response.headers

    @pytest.mark.asyncio
    async def test_phone_limit_applies_before_ip_limit(self, test_client):
        """The tighter per-phone limit still fires below the per-IP ceiling."""
        from app.core.config import get_settings

        phone_limit = get_settings().voice_rate_limit_per_minute
        assert phone_limit < get_settings().voice_rate_limit_ip_per_minute

        with patch(
            "app.api.voice.VoiceCarePipeline.run",
            new=AsyncMock(return_value=_completed_state()),
        ):
            for _ in range(phone_limit):
                response = await test_client.post(
                    "/api/voice/query", json={"text": "hi", "phone": "9876543210"}
                )
                assert response.status_code == 200

            response = await test_client.post(
                "/api/voice/query", json={"text": "hi", "phone": "9876543210"}
            )

        assert response.status_code == 429


# ---------------------------------------------------------------------------
# WebSocket: origin check, connection cap, message budget
# ---------------------------------------------------------------------------

@pytest.fixture
def ws_client():
    from starlette.testclient import TestClient

    from app.api import voice
    from main import app

    voice._ws_connections.clear()
    # Plain client (no context manager) so app lifespan/DB init never runs.
    client = TestClient(app)
    yield client
    voice._ws_connections.clear()


class TestVoiceWebSocketProtections:

    def test_origin_allowed_helper(self):
        from app.api.voice import _origin_allowed

        assert _origin_allowed("http://localhost:3000") is True
        assert _origin_allowed("https://evil.example.com") is False
        # Vercel previews are allowed outside production
        assert _origin_allowed("https://myapp-preview.vercel.app") is True

    def test_cross_origin_handshake_rejected(self, ws_client):
        with pytest.raises(Exception):
            with ws_client.websocket_connect(
                "/api/voice/ws/test-session",
                headers={"origin": "https://evil.example.com"},
            ):
                pass

    def test_connection_cap_rejects_extra_connections(self, ws_client):
        from app.core.config import get_settings

        cap = get_settings().ws_max_connections_per_ip
        sessions = []
        try:
            for i in range(cap):
                sessions.append(
                    ws_client.websocket_connect(f"/api/voice/ws/session-{i}").__enter__()
                )

            with pytest.raises(Exception):
                with ws_client.websocket_connect("/api/voice/ws/one-too-many"):
                    pass
        finally:
            for session in sessions:
                session.__exit__(None, None, None)

    def test_connection_slots_are_released(self, ws_client):
        """Closing a connection frees its slot for the same IP."""
        from app.core.config import get_settings

        cap = get_settings().ws_max_connections_per_ip
        for i in range(cap + 2):  # sequential opens must all succeed
            with ws_client.websocket_connect(f"/api/voice/ws/seq-{i}"):
                pass

    def test_message_over_budget_gets_rate_limited(self, ws_client):
        """A message beyond the shared per-IP budget is refused pre-pipeline."""
        from app.core.config import get_settings
        from app.services.memory_service import _expiry_store, _memory_store

        limit = get_settings().voice_rate_limit_ip_per_minute
        with ws_client.websocket_connect("/api/voice/ws/budget-session") as session:
            # Pre-fill the shared counter to the limit (as if REST consumed it)
            _memory_store["rate_limit:voice:ip:testclient"] = limit
            _expiry_store["rate_limit:voice:ip:testclient"] = datetime.now() + timedelta(seconds=60)

            session.send_json({"text": "hello"})
            message = session.receive_json()

        assert message["error"] == "RATE_LIMITED"
        assert message["retry_after"] == 60
