"""
CommerceMind VoiceCare AI — Redis Cache Service
Handles conversation memory, response caching, and throttle bookkeeping.
"""

import json
import structlog
from typing import Optional, List
from datetime import timedelta
import redis.asyncio as redis

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class RedisService:
    """Service for Redis-backed session memory, caching, and rate limiting."""

    def __init__(self):
        self.redis = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )

    async def ping(self) -> bool:
        """Check Redis connectivity."""
        try:
            return await self.redis.ping()
        except Exception as e:
            logger.error("redis_ping_failed", error=str(e))
            return False

    # ---- Conversation Memory ----

    async def store_conversation_turn(
        self, session_id: str, role: str, message: str, metadata: dict = None
    ) -> None:
        """Store a conversation turn for multi-turn memory."""
        key = f"session:{session_id}:history"
        turn = {
            "role": role,
            "message": message,
            "metadata": metadata or {},
        }
        await self.redis.rpush(key, json.dumps(turn))
        # Keep conversation history for 2 hours
        await self.redis.expire(key, timedelta(hours=2))

    async def get_conversation_history(
        self, session_id: str, max_turns: int = 10
    ) -> List[dict]:
        """Retrieve conversation history for a session."""
        key = f"session:{session_id}:history"
        history = await self.redis.lrange(key, -max_turns, -1)
        return [json.loads(turn) for turn in history]

    async def clear_conversation(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        key = f"session:{session_id}:history"
        await self.redis.delete(key)

    # ---- Response Caching ----

    async def cache_response(
        self, cache_key: str, response: dict, ttl_seconds: int = 3600
    ) -> None:
        """Cache a response to avoid redundant LLM calls."""
        key = f"cache:{cache_key}"
        await self.redis.setex(key, ttl_seconds, json.dumps(response))

    async def get_cached_response(self, cache_key: str) -> Optional[dict]:
        """Retrieve a cached response."""
        key = f"cache:{cache_key}"
        cached = await self.redis.get(key)
        if cached:
            logger.info("cache_hit", key=cache_key)
            return json.loads(cached)
        return None

    # ---- Rate Limiting / Throttle Bookkeeping ----

    async def check_rate_limit(
        self, identifier: str, max_requests: int = 30, window_seconds: int = 60
    ) -> bool:
        """
        Check if the identifier has exceeded the rate limit.
        Returns True if request is allowed, False if rate limited.
        """
        key = f"ratelimit:{identifier}"
        current = await self.redis.get(key)

        if current is None:
            await self.redis.setex(key, window_seconds, 1)
            return True

        if int(current) >= max_requests:
            logger.warning("rate_limited", identifier=identifier, count=current)
            return False

        await self.redis.incr(key)
        return True

    # ---- Session State ----

    async def store_session_state(
        self, session_id: str, state: dict, ttl_seconds: int = 7200
    ) -> None:
        """Store pipeline state for a session."""
        key = f"session:{session_id}:state"
        await self.redis.setex(key, ttl_seconds, json.dumps(state, default=str))

    async def get_session_state(self, session_id: str) -> Optional[dict]:
        """Retrieve pipeline state for a session."""
        key = f"session:{session_id}:state"
        state = await self.redis.get(key)
        if state:
            return json.loads(state)
        return None

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()


# Singleton
_redis_service: Optional[RedisService] = None


async def get_redis_service() -> RedisService:
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service
