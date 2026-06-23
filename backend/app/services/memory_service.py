"""
CommerceMind VoiceCare AI — Memory Cache Service
Replaces Redis with an in-memory dictionary for free deployments.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# In-memory stores
_memory_store: Dict[str, Any] = {}
_expiry_store: Dict[str, datetime] = {}
_list_store: Dict[str, List[str]] = {}

class MemoryService:
    """Service for in-memory session memory, caching, and rate limiting."""

    async def ping(self) -> bool:
        """Check memory connectivity (always true)."""
        return True

    def _clean_expired(self, key: str):
        """Helper to clean up expired keys."""
        if key in _expiry_store and datetime.now() > _expiry_store[key]:
            _memory_store.pop(key, None)
            _list_store.pop(key, None)
            _expiry_store.pop(key, None)

    # ---- Conversation Memory ----

    async def store_conversation_turn(self, session_id: str, role: str, content: str):
        """Store a single turn in the conversation history list."""
        key = f"session:{session_id}:history"
        self._clean_expired(key)
        
        turn = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        
        if key not in _list_store:
            _list_store[key] = []
        
        _list_store[key].append(json.dumps(turn))
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

    async def get_cache(self, key: str) -> Optional[dict]:
        """Retrieve a cached dict."""
        self._clean_expired(key)
        cached = _memory_store.get(key)
        if cached:
            return json.loads(cached)
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

    async def close(self):
        """Close connection (no-op)."""
        pass


# Global singleton
_memory_service: Optional[MemoryService] = None

async def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
