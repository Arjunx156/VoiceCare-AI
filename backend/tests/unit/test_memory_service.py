"""
Unit tests for MemoryService — in-memory implementation.
"""

import pytest
import asyncio


class TestMemoryService:

    @pytest.mark.asyncio
    async def test_store_and_retrieve_conversation(self):
        """store_conversation_turn then get_conversation_history returns turns."""
        from app.services.memory_service import MemoryService
        svc = MemoryService()
        session_id = "test-session-001"

        await svc.store_conversation_turn(session_id, "customer", "Where is my order?")
        await svc.store_conversation_turn(session_id, "ai", "Your order is in transit.")

        history = await svc.get_conversation_history(session_id)
        assert len(history) == 2
        assert history[0]["role"] == "customer"
        assert history[1]["role"] == "ai"

    @pytest.mark.asyncio
    async def test_get_conversation_history_empty(self):
        """Returns empty list for unknown session."""
        from app.services.memory_service import MemoryService
        svc = MemoryService()
        result = await svc.get_conversation_history("non-existent-session")
        assert result == []

    @pytest.mark.asyncio
    async def test_clear_conversation(self):
        """clear_conversation removes all turns for session."""
        from app.services.memory_service import MemoryService
        svc = MemoryService()
        session_id = "test-clear-session"

        await svc.store_conversation_turn(session_id, "customer", "Hello")
        await svc.clear_conversation(session_id)
        history = await svc.get_conversation_history(session_id)
        assert history == []

    @pytest.mark.asyncio
    async def test_rate_limit_allows_within_limit(self):
        """Returns True for requests within rate limit."""
        from app.services.memory_service import MemoryService
        svc = MemoryService()
        identifier = "ratelimit-test-1"

        for _ in range(5):
            result = await svc.check_rate_limit(identifier, limit=10, window_seconds=60)
            assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_over_limit(self):
        """Returns False when rate limit exceeded."""
        from app.services.memory_service import MemoryService
        svc = MemoryService()
        identifier = "ratelimit-test-2"

        for _ in range(5):
            await svc.check_rate_limit(identifier, limit=5, window_seconds=60)

        result = await svc.check_rate_limit(identifier, limit=5, window_seconds=60)
        assert result is False

    @pytest.mark.asyncio
    async def test_increment_with_expiry_counts_correctly(self):
        """increment_with_expiry returns incremented counter value."""
        from app.services.memory_service import MemoryService
        svc = MemoryService()
        key = "counter-test-key"

        first = await svc.increment_with_expiry(key, 60)
        second = await svc.increment_with_expiry(key, 60)
        third = await svc.increment_with_expiry(key, 60)

        assert first == 1
        assert second == 2
        assert third == 3

    @pytest.mark.asyncio
    async def test_set_and_get_cache(self):
        """set_cache and get_cache work correctly."""
        from app.services.memory_service import MemoryService
        svc = MemoryService()

        data = {"result": "test_value", "count": 42}
        await svc.set_cache("test-cache-key", data, ttl_seconds=3600)
        retrieved = await svc.get_cache("test-cache-key")

        assert retrieved == data

    @pytest.mark.asyncio
    async def test_get_cache_miss_returns_none(self):
        """get_cache returns None for missing keys."""
        from app.services.memory_service import MemoryService
        svc = MemoryService()
        result = await svc.get_cache("nonexistent-key-xyz")
        assert result is None
