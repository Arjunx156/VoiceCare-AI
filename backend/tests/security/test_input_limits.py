"""
Unit tests for request input size limits — Pydantic field constraints on the
voice REST endpoint and the Content-Length body middleware.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.constants import MAX_AUDIO_B64_LEN, MAX_BODY_BYTES, MAX_TEXT_LEN


class TestVoiceQueryFieldLimits:

    @pytest.mark.asyncio
    async def test_oversized_text_rejected(self, test_client):
        """Text beyond MAX_TEXT_LEN returns 422 before any pipeline work."""
        response = await test_client.post(
            "/api/voice/query",
            json={"text": "x" * (MAX_TEXT_LEN + 1)},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_oversized_phone_rejected(self, test_client):
        response = await test_client.post(
            "/api/voice/query",
            json={"text": "where is my order", "phone": "9" * 21},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_oversized_session_id_rejected(self, test_client):
        response = await test_client.post(
            "/api/voice/query",
            json={"text": "hello", "session_id": "s" * 65},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_audio_limit_matches_ten_megabytes(self):
        """The base64 cap corresponds to ~10 MB of raw audio and fits the body cap."""
        assert MAX_AUDIO_B64_LEN == 14_316_558
        assert MAX_AUDIO_B64_LEN < MAX_BODY_BYTES

    @pytest.mark.asyncio
    async def test_valid_payload_reaches_pipeline(self, test_client):
        """A well-formed payload passes validation and runs the pipeline."""
        from app.agents.state import PipelineState

        completed = PipelineState(
            raw_text="Where is my order?",
            response_text="Your order is on the way.",
            intent="order_status",
            recommended_action="Inform",
        )

        with patch(
            "app.api.voice.VoiceCarePipeline.run",
            new=AsyncMock(return_value=completed),
        ):
            response = await test_client.post(
                "/api/voice/query",
                json={"text": "Where is my order?", "language": "English"},
            )

        assert response.status_code == 200
        assert response.json()["response_text"] == "Your order is on the way."


class TestBodySizeMiddleware:

    @pytest.mark.asyncio
    async def test_huge_body_rejected_with_413(self, test_client):
        """A body above MAX_BODY_BYTES is refused from its Content-Length."""
        oversized = b'{"text": "' + b"a" * (MAX_BODY_BYTES + 10) + b'"}'
        response = await test_client.post(
            "/api/voice/query",
            content=oversized,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 413
        assert response.json()["error"] == "PAYLOAD_TOO_LARGE"

    @pytest.mark.asyncio
    async def test_normal_body_passes_middleware(self, test_client):
        """Small bodies are unaffected (422 here proves it reached validation)."""
        response = await test_client.post(
            "/api/voice/query",
            json={"text": "x" * (MAX_TEXT_LEN + 1)},
        )
        assert response.status_code == 422
