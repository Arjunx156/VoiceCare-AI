"""
Upstash Redis-backed MemoryService.
Selected automatically when UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN are set.
Shares the exact same interface as MemoryService — no caller changes required.
"""

import json
import structlog
from datetime import datetime
from typing import Optional, List

logger = structlog.get_logger()

_MAX_HISTORY_TURNS = 50


class RedisMemoryService:
    """Durable, cross-instance memory backed by Upstash Redis (serverless REST API)."""

    def __init__(self, url: str, token: str):
        from upstash_redis.asyncio import Redis
        self._redis = Redis(url=url, token=token)

    async def ping(self) -> bool:
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False

    # ---- Conversation History ----

    async def store_conversation_turn(self, session_id: str, role: str, content: str):
        key = f"session:{session_id}:history"
        turn = json.dumps({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        await self._redis.rpush(key, turn)
        await self._redis.ltrim(key, -_MAX_HISTORY_TURNS, -1)
        await self._redis.expire(key, 7200)  # 2h TTL

    async def get_conversation_history(self, session_id: str, max_turns: int = 10) -> List[dict]:
        key = f"session:{session_id}:history"
        raw = await self._redis.lrange(key, -max_turns, -1)
        result = []
        for item in (raw or []):
            try:
                text = item if isinstance(item, str) else item.decode()
                result.append(json.loads(text))
            except Exception:
                pass
        return result

    async def clear_conversation(self, session_id: str):
        history_key = f"session:{session_id}:history"
        context_key = f"session:{session_id}:context"
        await self._redis.delete(history_key, context_key)

    # ---- Session Context (identity across turns — Part B) ----

    async def set_session_context(self, session_id: str, context: dict, ttl_seconds: int = 7200):
        key = f"session:{session_id}:context"
        await self._redis.set(key, json.dumps(context, default=str), ex=ttl_seconds)

    async def get_session_context(self, session_id: str) -> Optional[dict]:
        key = f"session:{session_id}:context"
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            text = raw if isinstance(raw, str) else raw.decode()
            return json.loads(text)
        except Exception:
            return None

    # ---- Generic Cache ----

    async def set_cache(self, key: str, response: dict, ttl_seconds: int = 3600):
        await self._redis.set(key, json.dumps(response, default=str), ex=ttl_seconds)
        logger.debug("redis_cache_set", key=key[:40], ttl=ttl_seconds)

    async def get_cache(self, key: str) -> Optional[dict]:
        raw = await self._redis.get(key)
        if raw is None:
            logger.debug("redis_cache_miss", key=key[:40])
            return None
        logger.debug("redis_cache_hit", key=key[:40])
        try:
            text = raw if isinstance(raw, str) else raw.decode()
            return json.loads(text)
        except Exception:
            return None

    # ---- Rate Limiting ----

    async def check_rate_limit(self, identifier: str, limit: int = 10, window_seconds: int = 60) -> bool:
        count = await self.increment_with_expiry(f"ratelimit:{identifier}", window_seconds)
        return count is None or count <= limit

    async def increment_with_expiry(self, key: str, window_seconds: int = 60) -> Optional[int]:
        count = await self._redis.incr(key)
        if count == 1:
            # First hit — set the expiry window
            await self._redis.expire(key, window_seconds)
        return count

    # ---- Pipeline State ----

    async def set_pipeline_state(self, session_id: str, state: dict, ttl_seconds: int = 3600):
        key = f"state:{session_id}"
        await self._redis.set(key, json.dumps(state, default=str), ex=ttl_seconds)

    async def get_pipeline_state(self, session_id: str) -> Optional[dict]:
        key = f"state:{session_id}"
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            text = raw if isinstance(raw, str) else raw.decode()
            return json.loads(text)
        except Exception:
            return None

    async def close(self):
        pass
