"""Shared outbound HTTP client.

Every external call in this codebase used to construct its own
`httpx.AsyncClient` inside an `async with` block — Groq Whisper STT, the Groq
LLM fallback, and four separate Bhashini calls. That means a fresh DNS lookup,
TCP handshake and TLS negotiation on every single one, costing 100-300 ms each
against APIs we talk to several times per conversation turn.

One process-wide client with a keep-alive pool amortises all of that.

The client is created lazily rather than at import time on purpose: an
`AsyncClient` binds to the event loop that is running when it is first used, and
importing this module happens long before uvicorn's loop exists. Tests make this
sharper still — pytest-asyncio gives each test its own loop, so a client cached
from a previous test's dead loop raises on reuse (see the reset fixture in
tests/conftest.py).
"""

from __future__ import annotations

import httpx

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Return the shared client, creating it on first use in this loop."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            # Generous read budget for slow Indian-language TTS, short connect
            # budget so an unreachable host fails fast instead of eating the turn.
            timeout=httpx.Timeout(20.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        )
    return _client


async def close_http_client() -> None:
    """Close the shared client. Called from the FastAPI lifespan on shutdown."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
