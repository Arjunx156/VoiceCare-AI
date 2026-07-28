"""The caching and connection-reuse machinery behind the latency work.

Every one of these exists to remove a network round trip from the hot path.
Because their whole value is *not* making a call, a regression is invisible in
behaviour — the system still works, just slower. Asserting on call counts is
the only way to notice.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


class TestSharedHttpClient:

    def test_the_same_client_is_reused_across_calls(self):
        """One pooled client, so we pay TLS setup once rather than per call."""
        from app.core.http import get_http_client

        assert get_http_client() is get_http_client()

    def test_a_closed_client_is_replaced(self):
        """A client closed at shutdown must not be handed out again."""
        import app.core.http as http_module
        from app.core.http import get_http_client

        first = get_http_client()
        first._state = httpx._client.ClientState.CLOSED

        second = get_http_client()

        assert second is not first
        assert not second.is_closed

    def test_connect_fails_faster_than_a_slow_read(self):
        """An unreachable host must fail fast; a slow one gets time to answer.

        Indian-language TTS is genuinely slow, so the read budget is generous —
        but a dead host should not hold a turn open for that whole window.
        """
        from app.core.http import get_http_client

        timeout = get_http_client().timeout
        assert timeout.connect < timeout.read
        assert timeout.read >= 10.0

    @pytest.mark.asyncio
    async def test_closing_is_idempotent(self):
        """Shutdown runs the lifespan teardown; a double close must not raise."""
        from app.core.http import close_http_client, get_http_client

        get_http_client()
        await close_http_client()
        await close_http_client()


class TestBhashiniConfigCache:
    """The ULCA pipeline config is static per (task, language) but was refetched
    over HTTPS before every single STT and TTS call."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        from app.services.bhashini_service import reset_pipeline_config_cache

        reset_pipeline_config_cache()
        yield
        reset_pipeline_config_cache()

    def _service_with_stubbed_http(self, response_json=None):
        from app.services.bhashini_service import BhashiniService

        response = MagicMock()
        response.status_code = 200
        response.json = MagicMock(return_value=response_json or {"pipelineResponseConfig": []})
        response.raise_for_status = MagicMock()

        client = MagicMock()
        client.post = AsyncMock(return_value=response)
        return BhashiniService(), client

    @pytest.mark.asyncio
    async def test_the_second_lookup_makes_no_network_call(self):
        """A cache hit is what removes a full round trip from every turn."""
        service, client = self._service_with_stubbed_http()

        with patch("app.services.bhashini_service.get_http_client", return_value=client):
            await service._get_pipeline_config("tts", "hi")
            await service._get_pipeline_config("tts", "hi")

        assert client.post.await_count == 1

    @pytest.mark.asyncio
    async def test_each_language_is_cached_separately(self):
        """Hindi's config must never be served for a Tamil request."""
        service, client = self._service_with_stubbed_http()

        with patch("app.services.bhashini_service.get_http_client", return_value=client):
            await service._get_pipeline_config("tts", "hi")
            await service._get_pipeline_config("tts", "ta")

        assert client.post.await_count == 2

    @pytest.mark.asyncio
    async def test_stt_and_tts_configs_do_not_collide(self):
        """Same language, different task — different pipeline."""
        service, client = self._service_with_stubbed_http()

        with patch("app.services.bhashini_service.get_http_client", return_value=client):
            await service._get_pipeline_config("tts", "hi")
            await service._get_pipeline_config("asr", "hi")

        assert client.post.await_count == 2

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_the_cache(self):
        """The escape hatch for a rotated inference key.

        Without it a stale key would break audio for the full 6-hour TTL.
        """
        service, client = self._service_with_stubbed_http()

        with patch("app.services.bhashini_service.get_http_client", return_value=client):
            await service._get_pipeline_config("tts", "hi")
            await service._get_pipeline_config("tts", "hi", force_refresh=True)

        assert client.post.await_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_cold_lookups_fetch_once(self):
        """A cold start with several simultaneous turns must not stampede."""
        import asyncio

        service, client = self._service_with_stubbed_http()

        with patch("app.services.bhashini_service.get_http_client", return_value=client):
            await asyncio.gather(
                service._get_pipeline_config("tts", "hi"),
                service._get_pipeline_config("tts", "hi"),
                service._get_pipeline_config("tts", "hi"),
            )

        assert client.post.await_count == 1

    @pytest.mark.asyncio
    async def test_a_failed_lookup_is_not_cached(self):
        """Caching a failure would turn a blip into a 6-hour outage."""
        from app.services.bhashini_service import BhashiniService

        response = MagicMock()
        response.status_code = 500
        response.text = "upstream error"
        response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("boom", request=MagicMock(), response=MagicMock())
        )
        client = MagicMock()
        client.post = AsyncMock(return_value=response)
        service = BhashiniService()

        with patch("app.services.bhashini_service.get_http_client", return_value=client):
            with pytest.raises(httpx.HTTPStatusError):
                await service._get_pipeline_config("tts", "hi")
            with pytest.raises(httpx.HTTPStatusError):
                await service._get_pipeline_config("tts", "hi")

        assert client.post.await_count == 2


class TestChromaContextFormatting:

    def test_retrieved_policies_render_with_title_and_relevance(self):
        """The resolution prompt needs the source and the score, not raw text."""
        from app.services.chroma_service import ChromaService

        rendered = ChromaService._format_context(
            [
                {
                    "content": "Returns accepted within 7 days.",
                    "title": "Return Policy",
                    "category": "Returns",
                    "relevance_score": 0.92,
                }
            ]
        )

        assert "Return Policy" in rendered
        assert "Returns accepted within 7 days." in rendered
        assert "0.92" in rendered

    def test_no_matches_produces_an_explicit_statement(self):
        """The LLM must be told there is no policy, not handed an empty string.

        An empty context reads as "no constraints" and invites invention.
        """
        from app.services.chroma_service import ChromaService

        rendered = ChromaService._format_context([])

        assert rendered.strip()
        assert "No relevant policy" in rendered

    def test_every_retrieved_policy_appears(self):
        """Truncating the context would silently drop grounding."""
        from app.services.chroma_service import ChromaService

        policies = [
            {
                "content": f"Policy body {i}",
                "title": f"Policy {i}",
                "category": "General",
                "relevance_score": 0.8,
            }
            for i in range(3)
        ]

        rendered = ChromaService._format_context(policies)

        for i in range(3):
            assert f"Policy body {i}" in rendered

    def test_query_with_context_searches_once_for_both_shapes(self):
        """The whole point: one embed + one search, two return values."""
        from app.services.chroma_service import ChromaService

        service = ChromaService.__new__(ChromaService)
        service.query_policies = MagicMock(
            return_value=[
                {
                    "content": "Refunds in 5-7 days.",
                    "title": "Refunds",
                    "category": "Refunds",
                    "relevance_score": 0.88,
                }
            ]
        )

        context, policies = ChromaService.query_with_context(service, "refund", 3)

        service.query_policies.assert_called_once_with("refund", 3)
        assert "Refunds in 5-7 days." in context
        assert len(policies) == 1

    def test_get_policy_context_delegates_to_the_same_path(self):
        """Kept as a thin wrapper so existing callers keep working."""
        from app.services.chroma_service import ChromaService

        service = ChromaService.__new__(ChromaService)
        service.query_policies = MagicMock(return_value=[])

        assert "No relevant policy" in ChromaService.get_policy_context(service, "x", 3)
