"""
CommerceMind VoiceCare AI — Shared Rate-Limiting Helpers
Single implementation used by the voice REST endpoint, the voice WebSocket,
the ticket routes, and admin login.

Counters live in the memory service (Upstash Redis when configured, in-process
dict otherwise). If the store errors, limiting degrades to a per-worker
fixed-window counter instead of disappearing entirely (fail-open would let an
attacker turn a store outage into unlimited traffic).
"""

import time
from typing import Union

import structlog
from fastapi import HTTPException, Request, WebSocket

from app.core.config import get_settings
from app.services.memory_service import get_memory_service

logger = structlog.get_logger()

# In-process fixed-window fallback: key -> (window_start_monotonic, count).
# Per-worker only — used when the shared store is unavailable.
_fallback_counters: dict[str, tuple[float, int]] = {}


def reset_in_process_counters() -> None:
    """Test helper — clears the in-process fallback counters."""
    _fallback_counters.clear()


def get_client_ip(conn: Union[Request, WebSocket]) -> str:
    """Best-effort client IP.

    Behind the production proxy (Render) the socket peer is the proxy, so the
    first X-Forwarded-For hop is the real client. Outside production the header
    is untrusted (trivially spoofable) and the socket address is used.
    """
    if get_settings().is_production:
        forwarded = conn.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return conn.client.host if conn.client else "unknown"


def _fallback_hit(key: str, window_seconds: int) -> int:
    now = time.monotonic()
    window_start, count = _fallback_counters.get(key, (now, 0))
    if now - window_start >= window_seconds:
        window_start, count = now, 0
    count += 1
    _fallback_counters[key] = (window_start, count)
    return count


async def count_hit(key: str, window_seconds: int) -> int:
    """Increment and return the counter for a key within its window."""
    try:
        memory = await get_memory_service()
        count = await memory.increment_with_expiry(key, window_seconds)
        if count is not None:
            return count
    except Exception as exc:
        logger.warning("rate_limit_store_degraded", key=key, error=str(exc))
    return _fallback_hit(key, window_seconds)


async def enforce(key: str, limit: int, window_seconds: int, detail: str) -> None:
    """Count a hit and raise 429 (with Retry-After) once the limit is exceeded."""
    count = await count_hit(key, window_seconds)
    if count > limit:
        logger.warning("rate_limit_exceeded", key=key, count=count, limit=limit)
        raise HTTPException(
            status_code=429,
            detail=detail,
            headers={"Retry-After": str(window_seconds)},
        )


async def is_within_limit(key: str, limit: int, window_seconds: int) -> bool:
    """Non-raising variant for WebSocket handlers."""
    return await count_hit(key, window_seconds) <= limit
