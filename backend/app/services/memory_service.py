"""
CommerceMind VoiceCare AI — Memory Cache Service
Replaces Redis with an in-memory dictionary for free deployments.
"""

import json
import structlog
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = structlog.get_logger()

# In-memory stores
_memory_store: Dict[str, Any] = {}
_expiry_store: Dict[str, datetime] = {}
_list_store: Dict[str, List[str]] = {}

class MemoryService:
    """Service for in-memory session memory, caching, and rate limiting."""

    async def ping(self) -> bool:
        """Check memory connectivity (always true)."""
        return True

    _MAX_HISTORY_TURNS = 50

    def _clean_expired(self, key: str):
        """Evict a single key if its TTL has elapsed."""
        if key in _expiry_store and datetime.now() > _expiry_store[key]:
            _memory_store.pop(key, None)
            _list_store.pop(key, None)
            _expiry_store.pop(key, None)

    def _clean_all_expired(self):
        """Sweep all stores and evict every expired key."""
        now = datetime.now()
        expired = [k for k, exp in _expiry_store.items() if now > exp]
        for k in expired:
            _memory_store.pop(k, None)
            _list_store.pop(k, None)
            _expiry_store.pop(k, None)

    # ---- Conversation Memory ----

    async def store_conversation_turn(self, session_id: str, role: str, content: str):
        """Store a single turn in the conversation history list."""
        key = f"session:{session_id}:history"
        self._clean_all_expired()

        turn = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}

        if key not in _list_store:
            _list_store[key] = []

        history = _list_store[key]
        if len(history) >= self._MAX_HISTORY_TURNS:
            history.pop(0)  # drop oldest turn to keep memory bounded
        history.append(json.dumps(turn))
        _expiry_store[key] = datetime.now() + timedelta(hours=2)

    async def get_conversation_history(self, session_id: str, max_turns: int = 10) -> List[dict]:
        """Retrieve recent conversation history."""
        key = f"session:{session_id}:history"
        self._clean_expired(key)
        
        if key not in _list_store:
            return []
            
        history = _list_store[key][-max_turns:]
        return [json.loads(turn) for turn in history]

    async def clear_conversation(self, session_id: str):
        """Clear conversation history."""
        key = f"session:{session_id}:history"
        _list_store.pop(key, None)
        _expiry_store.pop(key, None)

    # ---- Generic Caching ----

    async def set_cache(self, key: str, response: dict, ttl_seconds: int = 3600):
        """Cache an API response or generic dict."""
        _memory_store[key] = json.dumps(response)
        _expiry_store[key] = datetime.now() + timedelta(seconds=ttl_seconds)
        logger.debug("cache_set", key=key[:40], ttl_seconds=ttl_seconds)

    async def get_cache(self, key: str) -> Optional[dict]:
        """Retrieve a cached dict."""
        self._clean_expired(key)
        cached = _memory_store.get(key)
        if cached:
            logger.debug("cache_hit", key=key[:40])
            return json.loads(cached)
        logger.debug("cache_miss", key=key[:40])
        return None

    # ---- Rate Limiting ----

    async def check_rate_limit(self, identifier: str, limit: int = 10, window_seconds: int = 60) -> bool:
        """Simple memory-based rate limiting."""
        key = f"ratelimit:{identifier}"
        self._clean_expired(key)

        current = _memory_store.get(key)

        if current is None:
            _memory_store[key] = 1
            _expiry_store[key] = datetime.now() + timedelta(seconds=window_seconds)
            return True

        if current >= limit:
            return False

        _memory_store[key] += 1
        return True

    async def increment_with_expiry(self, key: str, window_seconds: int = 60) -> Optional[int]:
        """
        Atomically increment a counter and set TTL if it doesn't exist yet.
        Returns the new counter value. Used for sliding-window rate limiting.
        """
        self._clean_expired(key)
        current = _memory_store.get(key)
        if current is None:
            _memory_store[key] = 1
            _expiry_store[key] = datetime.now() + timedelta(seconds=window_seconds)
            return 1
        _memory_store[key] = current + 1
        return _memory_store[key]


    # ---- Pipeline State Sharing ----

    async def set_pipeline_state(self, session_id: str, state: dict, ttl_seconds: int = 3600):
        """Store pipeline state for recovery or handoffs."""
        key = f"state:{session_id}"
        _memory_store[key] = json.dumps(state, default=str)
        _expiry_store[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    async def get_pipeline_state(self, session_id: str) -> Optional[dict]:
        """Retrieve pipeline state."""
        key = f"state:{session_id}"
        self._clean_expired(key)
        state = _memory_store.get(key)
        if state:
            return json.loads(state)
        return None

    # ---- Session Context (identity across turns) ----

    async def set_session_context(self, session_id: str, context: dict, ttl_seconds: int = 7200):
        """Persist compact identity context so follow-up turns can reuse phone/order_id."""
        key = f"session:{session_id}:context"
        _memory_store[key] = json.dumps(context, default=str)
        _expiry_store[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    async def get_session_context(self, session_id: str) -> Optional[dict]:
        """Retrieve session identity context."""
        key = f"session:{session_id}:context"
        self._clean_expired(key)
        raw = _memory_store.get(key)
        if raw:
            return json.loads(raw)
        return None

    async def close(self):
        """Close connection (no-op)."""
        pass


# Global singleton — type is Union[MemoryService, RedisMemoryService] at runtime
_memory_service = None


async def get_memory_service():
    """
    Return the memory backend singleton.
    Prefers Upstash Redis when UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN are set;
    falls back to the in-process dict (MemoryService) if absent — safe for local dev / tests.
    """
    global _memory_service
    if _memory_service is not None:
        return _memory_service

    from app.core.config import get_settings
    settings = get_settings()

    url = getattr(settings, "upstash_redis_rest_url", None)
    token = getattr(settings, "upstash_redis_rest_token", None)

    if url and token:
        try:
            from app.services.redis_memory_service import RedisMemoryService
            svc = RedisMemoryService(url=url, token=token)
            reachable = await svc.ping()
            if reachable:
                logger.info("memory_backend", backend="upstash_redis")
                _memory_service = svc
                return _memory_service
            logger.warning("upstash_redis_unreachable", fallback="in_process")
        except Exception as exc:
            logger.warning("upstash_redis_init_failed", error=str(exc), fallback="in_process")

    logger.info("memory_backend", backend="in_process")
    _memory_service = MemoryService()
    return _memory_service
