"""
VoiceCare AI — Pytest Configuration & Shared Fixtures
All tests use async fixtures, fully mocked external APIs, and an in-memory SQLite DB.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Event loop policy — needed for pytest-asyncio
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


# ---------------------------------------------------------------------------
# In-memory async SQLite DB for fast, isolated tests
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Import Base after engine creation to avoid circular imports. Importing the
    # models module registers every table on Base.metadata so create_all builds
    # them (without this, real-DB tests hit "no such table").
    from app.core.database import Base
    import app.db.models  # noqa: F401  (registers ORM models on Base.metadata)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provides a rollback-isolated async DB session per test."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def test_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """ASGI test client with the real app, DB session overridden."""
    from app.core.database import get_db

    async def override_get_db():
        yield db_session

    from main import app
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_user_id():
    return uuid.uuid4()


@pytest.fixture
def sample_order_id():
    return uuid.uuid4()


@pytest.fixture
def sample_ticket_id():
    return uuid.uuid4()


@pytest.fixture
def sample_session_id():
    return str(uuid.uuid4())


@pytest.fixture
def sample_user_data(sample_user_id):
    return {
        "user_id": str(sample_user_id),
        "name": "Priya Sharma",
        "phone": "9876543210",
        "preferred_language": "Hindi",
        "customer_segment": "Premium",
    }


@pytest.fixture
def sample_order_data(sample_order_id):
    return {
        "order_id": str(sample_order_id),
        "order_date": "2024-01-15 10:30:00",
        "status": "Shipped",
        "total_amount": 2500.0,
    }


@pytest.fixture
def sample_pipeline_state(sample_session_id):
    from app.agents.state import PipelineState
    return PipelineState(
        session_id=sample_session_id,
        raw_text="Where is my order?",
        phone="9876543210",
        language_detected="English",
        language_code="en",
    )


# ---------------------------------------------------------------------------
# Gemini mock fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_gemini_intent_response():
    return {
        "intent": "order_status",
        "sub_intent": "customer wants to know delivery status",
        "sentiment": "Neutral",
        "priority": "Medium",
        "summary_english": "Customer asking about order status",
        "requires_order_lookup": True,
        "extracted_order_id": None,
        "extracted_phone": "9876543210",
        "extracted_name": "Priya",
    }


@pytest.fixture
def mock_gemini_resolution_response():
    return {
        "recommended_action": "Inform",
        "resolution_summary": "Order is in transit and will be delivered soon.",
        "policy_reference": "Standard shipping policy: delivery within 5-7 days.",
        "internal_note": "Order shipped on time, within SLA.",
        "confidence_score": 0.9,
        "requires_human_review": False,
        "reason_for_action": "Order status is clear from DB lookup.",
    }


@pytest.fixture
def mock_gemini_response_response():
    return {
        "response_text": "आपका ऑर्डर रास्ते में है और जल्द ही डिलीवर होगा।",
        "response_english": "Your order is in transit and will be delivered soon.",
        "tone": "Professional",
    }


@pytest.fixture
def mock_gemini_service(
    mock_gemini_intent_response,
    mock_gemini_resolution_response,
    mock_gemini_response_response,
):
    """Fully mocked GeminiService — no real API calls."""
    mock = MagicMock()
    mock.analyze_intent = AsyncMock(return_value=mock_gemini_intent_response)
    mock.generate_resolution = AsyncMock(return_value=mock_gemini_resolution_response)
    mock.generate_response = AsyncMock(return_value=mock_gemini_response_response)
    return mock


# ---------------------------------------------------------------------------
# Bhashini mock fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_bhashini_service():
    """Fully mocked BhashiniService — no real API calls."""
    mock = MagicMock()
    mock.speech_to_text = AsyncMock(return_value=("मेरा ऑर्डर कहाँ है?", "hi"))
    mock.translate_text = AsyncMock(return_value="Where is my order?")
    mock.text_to_speech = AsyncMock(return_value="base64_audio_string_here")
    return mock


# ---------------------------------------------------------------------------
# Chroma mock fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_chroma_service():
    """Fully mocked ChromaService — no real vector store calls."""
    mock = MagicMock()
    mock.get_policy_context = MagicMock(
        return_value="Policy: Orders are delivered within 5-7 business days."
    )
    mock.query_policies = MagicMock(
        return_value=[
            {
                "id": "policy_1",
                "content": "Standard delivery policy: 5-7 business days.",
                "category": "Shipping",
                "score": 0.95,
            }
        ]
    )
    return mock


# ---------------------------------------------------------------------------
# Memory service mock
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_memory_service():
    mock = MagicMock()
    mock.get_conversation_history = AsyncMock(return_value=[])
    mock.store_conversation_turn = AsyncMock()
    mock.increment_with_expiry = AsyncMock(return_value=1)
    mock.check_rate_limit = AsyncMock(return_value=True)
    return mock
