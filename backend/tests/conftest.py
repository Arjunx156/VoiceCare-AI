"""
VoiceCare AI — Pytest Configuration & Shared Fixtures
All tests use async fixtures, fully mocked external APIs, and an in-memory SQLite DB.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from tests.report_plugin import TestReportCollector

# ---------------------------------------------------------------------------
# Category markers, applied from the directory a test lives in.
#
# Marking by hand never survives contact with a growing suite — the previous
# markers were declared in pytest.ini and applied to exactly zero tests, so
# `pytest -m unit` silently collected nothing. Deriving the marker from the
# path makes the directory the single source of truth.
# ---------------------------------------------------------------------------
TEST_CATEGORIES = (
    "unit",
    "integration",
    "performance",
    "security",
    "multilingual",
    "resilience",
    "contract",
)


def pytest_collection_modifyitems(items):
    tests_root = Path(__file__).parent
    for item in items:
        try:
            relative = Path(str(item.fspath)).relative_to(tests_root)
        except ValueError:
            continue
        category = relative.parts[0] if len(relative.parts) > 1 else None
        if category in TEST_CATEGORIES:
            item.add_marker(getattr(pytest.mark, category))


# ---------------------------------------------------------------------------
# Machine-readable run report, consumed by the public /tests page.
# ---------------------------------------------------------------------------
_report_collector = TestReportCollector()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach each test's docstring summary to its report.

    Read here rather than at write time because the report is the only object
    that survives to the reporting hook under distributed runs.
    """
    outcome = yield
    report = outcome.get_result()
    doc = (getattr(item, "function", None).__doc__ or "") if hasattr(item, "function") else ""
    report.voicecare_docstring = doc.strip().split("\n\n")[0].replace("\n", " ").strip()


def pytest_runtest_logreport(report):
    _report_collector.record(report)


def pytest_sessionfinish(session, exitstatus):
    _report_collector.write()


# ---------------------------------------------------------------------------
# Pipeline test helpers, shared by every category that drives the agents
# directly. These used to be copy-pasted between test_pipeline.py and
# test_escalation_rules.py.
# ---------------------------------------------------------------------------
def make_mock_db(scalar_result=None, scalars_list=None):
    """SQLAlchemy async-session mock. Returns `scalar_result` for every query."""
    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=scalar_result)
    mock_result.scalars = MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=scalars_list or []))
    )
    mock_result.first = MagicMock(return_value=None)
    db.execute = AsyncMock(return_value=mock_result)
    db.scalar_one_or_none = AsyncMock(return_value=scalar_result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


def patch_all_services(gemini_svc, bhashini_svc, chroma_svc, memory_svc):
    """Patch every external-service getter the pipeline resolves at construction."""
    return (
        patch("app.agents.pipeline.get_gemini_service", return_value=gemini_svc),
        patch("app.agents.pipeline.get_bhashini_service", return_value=bhashini_svc),
        patch("app.agents.pipeline.get_chroma_service", return_value=chroma_svc),
        patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=memory_svc)),
    )


# ---------------------------------------------------------------------------
# Event loop policy — needed for pytest-asyncio
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


# ---------------------------------------------------------------------------
# Memory backend isolation — a developer .env with Upstash credentials would
# otherwise make tests hit real Redis. Force the in-process backend.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _force_in_process_memory():
    import app.services.memory_service as memory_module

    memory_module._memory_service = memory_module.MemoryService()
    yield
    memory_module._memory_service = None


# ---------------------------------------------------------------------------
# Rate-limit isolation — counters live in module-level dicts and would bleed
# across tests (every test shares the same client IP), so reset before each.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_rate_limits():
    from app.core import rate_limit
    from app.services.memory_service import _expiry_store, _memory_store

    for store in (_memory_store, _expiry_store):
        for key in [k for k in store if k.startswith("rate_limit:")]:
            store.pop(key, None)
    rate_limit.reset_in_process_counters()
    yield


# ---------------------------------------------------------------------------
# Process-wide caches created for latency reasons must not survive a test.
#
# The shared httpx.AsyncClient binds to whichever event loop is running when it
# is first used, and pytest-asyncio gives each test its own loop — a client held
# over from a previous test would raise on reuse. The Bhashini pipeline-config
# cache is cleared for the ordinary reason: one test's stubbed config must not
# silently satisfy the next test's lookup and mask a real cache bug.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_process_caches():
    import app.core.http as http_module
    from app.services.bhashini_service import reset_pipeline_config_cache

    http_module._client = None
    reset_pipeline_config_cache()
    yield
    http_module._client = None
    reset_pipeline_config_cache()


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


# ---------------------------------------------------------------------------
# Committing-session fixtures for endpoint tests.
#
# The dashboard endpoints commit their own transactions, so they cannot run on
# the shared rollback-per-test session. These give each test independent
# committing sessions against the same in-memory database; isolation comes from
# every seeded customer getting a unique phone number.
# ---------------------------------------------------------------------------
ADMIN_EMAIL = "agent@test.com"


@pytest_asyncio.fixture
async def sessionmaker_(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def authed_client(sessionmaker_):
    """ASGI client with committing DB sessions and admin auth stubbed."""
    from app.api.auth import require_admin
    from app.core.database import get_db
    from main import app

    async def override_get_db():
        async with sessionmaker_() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = lambda: ADMIN_EMAIL

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(require_admin, None)


@pytest_asyncio.fixture
async def seeded_ticket(sessionmaker_):
    """A user + one escalated ticket committed to the shared test DB."""
    from app.db.models import SupportTicket, User

    phone = "9" + uuid.uuid4().hex[:9]
    async with sessionmaker_() as s:
        user = User(name="Asha Rao", phone=phone, preferred_language="Hindi")
        s.add(user)
        await s.flush()
        ticket = SupportTicket(
            user_id=user.user_id,
            ticket_type="Complaint",
            priority="High",
            status="Escalated",
            language="Hindi",
            summary="Damaged product on arrival",
        )
        s.add(ticket)
        await s.commit()
        return {
            "user_id": str(user.user_id),
            "ticket_id": str(ticket.ticket_id),
            "phone": phone,
        }


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
    # What the pipeline actually calls — one embed + one search for both shapes.
    mock.query_with_context = MagicMock(
        return_value=(
            "Policy: Orders are delivered within 5-7 business days.",
            [
                {
                    "id": "policy_1",
                    "content": "Standard delivery policy: 5-7 business days.",
                    "category": "Shipping",
                    "score": 0.95,
                }
            ],
        )
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
