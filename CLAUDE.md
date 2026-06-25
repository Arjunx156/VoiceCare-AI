# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

VoiceCare AI is a voice-first multilingual e-commerce customer support platform. Customers speak in any of 9 Indian languages; a 9-agent LangGraph pipeline processes the query through STT → intent detection → DB lookup → policy RAG → resolution → escalation check → response generation → TTS → ticket creation. Only 3 of the 9 agents make LLM calls (Gemini 2.5 Flash); the rest are deterministic code.

---

## Commands

### Backend (run from `backend/`)

```bash
# Activate virtualenv (Windows)
venv\Scripts\activate
# Activate virtualenv (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start dev server
uvicorn main:app --reload --port 8000

# Seed the database (creates demo users, orders, shipments)
python -m app.utils.seed_db

# Run all tests
pytest

# Run only unit tests (fast, no external calls)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run a single test file
pytest tests/unit/test_gemini_service.py

# Run a single test function
pytest tests/integration/test_pipeline.py::test_full_pipeline_text_query -v

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

### Frontend (run from `frontend/`)

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # Production build (also runs TypeScript check)
npm run lint       # ESLint
```

---

## Architecture

### Request Flow

```
Browser (WebSocket) ──► voice.py WS endpoint
                              │
                              ▼
                      VoiceCarePipeline.run(state)
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    Agent 1: STT        Agent 2: Intent     Agent 3: DB Lookup
    (Bhashini/Groq)     (Gemini LLM)       (SQLAlchemy async)
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    Agent 4: Policy RAG (Chroma)
                              │
                    Agent 5: Resolution (Gemini LLM)
                              │
                    Agent 6: Escalation Check (deterministic)
                              │
                    Agent 7: Response Generation (Gemini LLM)
                              │
                    Agent 8: TTS (Bhashini)
                              │
                    Agent 9: Ticket Creator (Postgres)
                              │
                    WebSocket sends { type: "response", ... }
```

The frontend also polls `POST /api/voice/query` (HTTP) as an alternate path. Both paths build a `PipelineState` and call `VoiceCarePipeline.run()`.

### Key Architectural Decisions

**`PipelineState` is the single shared state object.** It is a Pydantic model (`agents/state.py`) that accumulates data from each agent stage. Every agent reads from it, writes to it, and appends to `agent_trace`. The pipeline runs the agents sequentially (not as a LangGraph graph — `VoiceCarePipeline` calls each agent method in order directly).

**Services are singletons accessed via getter functions.** `get_gemini_service()`, `get_bhashini_service()`, `get_chroma_service()`, `get_memory_service()` — all return module-level singletons. In tests, patch these getters (see `conftest.py` → `_patch_all_services()`).

**Chroma is embedded (in-process), not a separate server.** It persists to `./chroma_data/` on disk. Policies are auto-seeded on app startup if the collection is empty. The seeding is idempotent (checks `get_collection_count() == 0`).

**Memory service is in-process dict, not Redis.** `memory_service.py` uses Python dicts (`_memory_store`, `_expiry_store`, `_list_store`) with manual TTL tracking. History is capped at 50 turns per session; a full sweep of expired keys runs on every `store_conversation_turn` write.

**Language codes live in one place.** `backend/app/core/constants.py` has `LANGUAGE_CODES` (display name → BCP-47 short code). `frontend/src/lib/constants.ts` has `LANGUAGES` (array) and `LANG_TO_BCP47` (display name → BCP-47 locale). Both must stay in sync if languages are added.

**Escalation is deterministic, not LLM-decided.** Six hard rules in the escalation agent check sentiment, order value, refund status, payment anomalies, and confidence score. If any trigger, `is_escalated=True` and a reason is appended to `escalation_rules_triggered`.

### Backend Structure

```
backend/
├── main.py                        # FastAPI app, CORS, lifespan (seeds Chroma)
├── app/
│   ├── agents/
│   │   ├── pipeline.py            # VoiceCarePipeline — 9 agent methods in sequence
│   │   └── state.py               # PipelineState (Pydantic) — flows through all agents
│   ├── api/
│   │   ├── voice.py               # POST /api/voice/query + WS /api/voice/ws/{session_id}
│   │   └── tickets.py             # GET /api/tickets, /analytics, /escalations, /{id}, /{id}/handoff
│   ├── core/
│   │   ├── config.py              # Settings (Pydantic), loaded once via @lru_cache
│   │   ├── constants.py           # LANGUAGE_CODES — single source of truth
│   │   ├── database.py            # Async SQLAlchemy engine + get_db dependency
│   │   └── errors.py              # Custom exception hierarchy (VoiceCareError subclasses)
│   ├── db/models.py               # 15 SQLAlchemy models (User, Order, SupportTicket, etc.)
│   ├── schemas/schemas.py         # Pydantic request/response models for API
│   └── services/
│       ├── gemini_service.py      # 3 methods: analyze_intent, generate_resolution, generate_response
│       ├── bhashini_service.py    # speech_to_text, text_to_speech (Groq Whisper as primary STT)
│       ├── chroma_service.py      # query_policies, ingest_policies
│       └── memory_service.py      # In-memory session cache + rate limiting counters
```

### Frontend Structure

```
frontend/src/
├── app/
│   ├── page.tsx                   # Voice interface (orb + recording + response display)
│   └── dashboard/
│       ├── layout.tsx             # Sidebar nav + DashboardErrorBoundary
│       ├── page.tsx               # Overview (KPIs + escalation preview)
│       ├── analytics/page.tsx     # Recharts charts
│       ├── escalations/page.tsx   # 5s polling queue (AbortController on unmount)
│       └── tickets/
│           ├── page.tsx           # Filterable ticket list
│           └── [id]/page.tsx      # Detail: 3 tabs (details, agent replay, handoff)
├── components/
│   ├── VoiceOrb.tsx               # Three.js / react-three-fiber 3D orb (SSR disabled)
│   ├── StatusStream.tsx           # Pipeline stage progress (stages 1-9)
│   ├── ResponsePanel.tsx          # Final response display
│   ├── Footer.tsx                 # Record button + language selector pills
│   ├── Header.tsx                 # App header
│   └── BhashiniWarning.tsx        # Dismissible banner when STT/TTS unavailable
├── hooks/
│   └── useVoiceInteraction.ts     # All voice state: recording, WS streaming, TTS playback
│                                  # WS reconnects up to 3× with 1s/2s/4s backoff
└── lib/
    ├── api.ts                     # fetch wrapper + all API function exports
    └── constants.ts               # LANGUAGES array + LANG_TO_BCP47 mapping
```

### Testing

Tests use **in-memory SQLite** (via `aiosqlite`) with a session-scoped engine and per-test transaction rollback. All three external services (Gemini, Bhashini, Chroma) are mocked via `unittest.mock`. The `conftest.py` at `tests/conftest.py` provides shared fixtures for mocked services, sample data, and the ASGI test client.

To add a new integration test for the pipeline, patch all services using `_patch_all_services()` from `tests/integration/test_pipeline.py` and pass a `PipelineState` directly to `VoiceCarePipeline(db=mock_db).run(state)`.

### Environment Variables

All config is loaded by `app/core/config.py` (`Settings` class, `pydantic-settings`). The `.env` file at repo root is picked up automatically. Required keys:

| Key | Purpose |
|-----|---------|
| `DATABASE_URL` | `postgresql+asyncpg://...` (async engine) |
| `DATABASE_URL_SYNC` | `postgresql://...` (Alembic migrations) |
| `GEMINI_API_KEY` | Google Gemini 2.5 Flash |
| `GROQ_API_KEY` | Groq Whisper (STT fallback) |
| `BHASHINI_USER_ID` / `BHASHINI_API_KEY` | Bhashini TTS |
| `FRONTEND_URL` | CORS origin |
| `ENVIRONMENT` | `development` or `production` |

Settings singleton is cached with `@lru_cache`. In tests, call `get_settings.cache_clear()` if you need to reload settings between tests.

### Database Models (key relationships)

```
User ──< Order ──< OrderItem >── Product
              │──< Shipment
              │──< Return ──< Refund
              │──< Payment
              └──< SupportTicket ──< SupportMessage
                         │──── SupportResolution (agent_trace stored as JSON)
                         └──< CustomerSentiment

VoiceSession ──< SupportMessage
```

All UUIDs use `uuid6` package. Audit fields (`created_by`, `updated_by`) are string labels (e.g., `"system"`, `"ai"`). Migrations live in `backend/migrations/versions/`.
