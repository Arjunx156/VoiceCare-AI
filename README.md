<div align="center">

# 🎙️ VoiceCare AI

### Voice-first multilingual customer support — powered by a 9-agent AI pipeline

**Speak in Hindi, Tamil, Telugu, Malayalam, Kannada, Bengali, Marathi, or English.**  
Get resolved instantly. No forms. No hold music. No English-only walls.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph)
[![Tests](https://img.shields.io/badge/tests-324_passing-4CAF73?style=flat-square)](#running-tests)

</div>

---

## What is this?

VoiceCare AI is a production-grade voice support platform for Indian e-commerce. A customer taps one button, speaks their problem in their native language, and receives a voice response — in the same language — in under 10 seconds.

Behind that button: a **9-agent pipeline** that transcribes speech, detects intent, queries a live database, retrieves grounded policy context, generates a resolution, checks six deterministic escalation rules, synthesises a response, converts it back to speech, and creates a support ticket — all in a single WebSocket stream.

Every one of those nine steps is recorded, and every ticket can be replayed step by step in the admin dashboard.

---

## Demo

<!-- TODO: add the demo video link and the deployed frontend URL once published -->

| | |
|---|---|
| **Video** | _(https://drive.google.com/file/d/1027ZFYcXiiB-kldM-mTLlxA0f6d0a41b/view?usp=drive_link)_ |
| **Live app** | _(https://frontend-roan-three-65.vercel.app)_ |
| **Backend health** | [`/health`](https://voicecare-backend.onrender.com/health) — first request after idle takes ~130 s, see [Deployment notes](#deployment-notes) |

**Try these after seeding.** Say your **name or order number** as well as the problem — a phone number alone is treated as a claim, not proof, so the AI will otherwise ask you to confirm your identity first.

| Language | Customer | Say… | Outcome |
|----------|----------|-------|---------|
| 🇮🇳 Hindi | Rajesh Kumar | "मेरा ऑर्डर ORD-RK24 पाँच दिन देर से आया है" | Delayed-shipment resolution |
| 🇮🇳 Malayalam | Priya Nair | Refund still pending | Auto-escalate — pending refund |
| 🇮🇳 Tamil | Muthu Selvam | Damaged product received | Replacement or refund |
| 🇮🇳 Telugu | Ananya Reddy | Payment deducted, order cancelled | Auto-escalate — payment anomaly |
| 🇮🇳 Hinglish | Amit Sharma | Wrong product — very angry | Auto-escalate — sentiment |

---

## Architecture

```
Browser (WebSocket)
       │
       ▼
  voice.py  ──────────────────────────────────────────────────────────────┐
       │                                                                    │
       ▼                                                                    │
  VoiceCarePipeline.run(state)                                             │
       │                                                                    │
  ┌────┴────────────────────────────────────┐                              │
  │  Agent 1   STT          Bhashini/Groq  │                              │
  │  Agent 2   Intent       Gemini LLM     │◄── PipelineState flows       │
  │  Agent 3   DB Lookup    SQLAlchemy      │    through all 9 agents      │
  │  Agent 4   Policy RAG   Chroma         │                              │
  │  Agent 5   Resolution   Gemini LLM     │                              │
  │  Agent 6   Escalation   Deterministic  │                              │
  │  Agent 7   Response     Gemini LLM     │                              │
  │  Agent 8   TTS          Bhashini       │                              │
  │  Agent 9   Ticket       Postgres       │                              │
  └─────────────────────────────────────────┘                              │
       │                                                                    │
       ▼                                                                    │
  { type: "response", audio, text, ticket_id, … } ──────────────────────►┘
```

Only **3 of the 9 agents** make LLM calls. The rest are deterministic — fast, auditable, and cheap.

Agents 3 and 4 run concurrently (neither depends on the other), and the reply is sent to the browser as soon as agent 7 finishes — speech synthesis and ticket persistence continue in the background so the customer isn't waiting on them.

---

## Features

### Customer Voice Interface
- **3D Audio-Reactive Orb** — GLSL shader + react-three-fiber; pulses with your voice
- **9 Indian Languages** — Hindi, Tamil, Telugu, Malayalam, Kannada, Bengali, Marathi, English, Hinglish
- **Multilingual UI** — the interface itself switches language when you pick a language pill, pipeline stage names included
- **Real-Time Stage Stream** — watch each of the 9 pipeline stages animate over WebSocket, with per-stage timings
- **Voice + Text Input** — MediaRecorder API or keyboard
- **TTS Playback** — hear the response in your chosen language (Bhashini; falls back to browser TTS after 1.2 s)
- **WS Reconnection** — 3× retry with 1s / 2s / 4s backoff on dropped connections

### AI Pipeline
- Gemini (`gemini-3.1-flash-lite` by default) — intent classification, resolution generation, response synthesis
- Policy RAG — top-3 Chroma results for every query; 1-hour result cache
- Deterministic escalation — 6 hard rules, no LLM in the decision
- Groq Whisper fallback if Bhashini STT is unavailable
- Tenacity retry (3×) on every external call

### Admin Dashboard
- **Overview** — 6 KPI cards, language volume bars, ticket-type breakdown, live escalation queue
- **Tickets** — filterable list with priority/status badges
- **Ticket Detail** — 3 tabs: Details, Agent Replay Timeline (full `agent_trace`), Handoff Note
- **Customers** — Customer 360: orders, line items, shipments, payments, sentiment timeline, ticket history
- **Escalations** — priority queue with Claim / Release workflow, auto-refreshing
- **Analytics** — Recharts bar/pie/area charts
- **JWT Auth** — 8-hour tokens, route-guarded with Next.js middleware

### Observability
- `GET /health` — DB ping + Chroma collection count
- `GET /metrics` — P50 / P95 / P99 latency from a rolling 1 000-request window
- `X-Response-Time` header on every response
- Sentry integration for both backend (FastAPI + SQLAlchemy) and frontend (browser + server) — no-ops gracefully without a DSN

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, Framer Motion |
| 3D Voice Orb | react-three-fiber, Three.js, GLSL shaders |
| Charts | Recharts |
| Backend | FastAPI, Python 3.12, uvicorn |
| AI Orchestration | LangGraph 0.4 (sequential 9-agent pipeline) |
| LLM | Google Gemini (`GEMINI_MODEL`, default `gemini-3.1-flash-lite`) |
| STT / TTS | Bhashini API (primary) · Groq Whisper (STT fallback) |
| Vector Store | Chroma (embedded, persistent to disk) |
| Database | PostgreSQL (Neon) via SQLAlchemy Async + asyncpg |
| Session Cache | Upstash Redis (multi-turn memory, rate limits, token revocation); degrades to an in-process per-worker store if unreachable |
| Migrations | Alembic |
| Error Tracking | Sentry (optional) |
| Hosting | Vercel (frontend) · Render (backend) |

---

## Quick Start

### Prerequisites
- Node.js 18+, Python 3.12+
- PostgreSQL (or a free [Neon](https://neon.tech) account)
- [Gemini API key](https://ai.google.dev)
- [Groq API key](https://console.groq.com) (free tier)
- Bhashini credentials (optional — voice falls back to browser TTS without them)
- Upstash Redis (optional — rate limiting and multi-turn memory degrade to per-worker without it)

### 1. Clone & configure

```bash
git clone https://github.com/Arjunx156/VoiceCare-AI.git
cd VoiceCare-AI
cp .env.example .env
# fill in DATABASE_URL, GEMINI_API_KEY, GROQ_API_KEY, NEXTAUTH_SECRET
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
alembic upgrade head           # run migrations
python -m app.utils.seed_db    # seed demo users, orders, shipments, payments
uvicorn main:app --reload --port 8000
```

> Seeding creates 8 customers with orders — but **no tickets**. Tickets are created by the pipeline, so run a query or two before expecting anything in the dashboard.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open

| URL | What it is |
|-----|-----------|
| http://localhost:3000 | Customer voice interface |
| http://localhost:3000/login | Admin login (`ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env`) |
| http://localhost:3000/dashboard | Admin dashboard (requires login) |
| http://localhost:3000/tests | The test suite, browsable |
| http://localhost:8000/docs | FastAPI interactive docs |
| http://localhost:8000/health | Health check (DB + Chroma) |
| http://localhost:8000/metrics | Latency percentiles (P50/P95/P99) |

---

## Security

- **Admin auth** — JWT (HS256, 8-hour expiry) on all `/api/tickets`, `/api/customers`, and `/metrics` routes; constant-time credential comparison (bcrypt); login rate-limited per IP (5 attempts / 15 min). Admin login returns **403 when default secrets are still configured** outside development, so a deploy that forgets `ENVIRONMENT` cannot run with forgeable tokens.
- **Customer identity verification** — a phone number alone is treated as a claim, not proof. Order/refund/payment details are only shared once the caller corroborates identity (an order ID belonging to the account, a matching name, or a previously verified session). Verification persists per session, so customers are challenged at most once per conversation.
- **Rate limiting** — REST voice queries: 10/min per IP (anonymous included) + 5/min per phone; voice WebSocket: Origin allowlist, 3 concurrent connections per IP, and a per-message budget sharing the REST counter; dashboard reads: 60/min per IP. If the shared store (Upstash Redis) is unreachable, limiting **degrades to an in-process per-worker counter** rather than disappearing (fail-open with fallback, not fail-secure 503 — a store blip should not take the product down).
- **Input limits** — request bodies over 15 MB rejected at Content-Length; text ≤ 5 000 chars and audio ≤ 10 MB enforced by schema on both REST and WebSocket.
- **Error hygiene** — clients never see raw exception text: voice 500s, `/health`, and WebSocket validation errors return generic or field-level messages only; real errors are logged server-side.
- **Privacy** — `ALLOW_GTTS_FALLBACK=false` disables the Google-Translate TTS fallback (which otherwise ships response text to Google when Bhashini is down); `send_default_pii: false` in Sentry.
- Security headers on every response (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `X-XSS-Protection`); CORS restricted to `FRONTEND_URL` + Vercel preview wildcard
- Soft deletes on Users, Orders, and Tickets — data never hard-deleted
- Next.js `middleware.ts` redirects logged-out visitors away from `/dashboard` (UX-only; the API enforces auth server-side)

---

## Escalation Rules

Six hard-coded triggers in `agent_escalation_check` — **no LLM makes the escalation decision**. If any rule fires, the ticket is escalated and the triggered rule names are written into the agent trace, so the reason survives into the handoff note.

| # | Trigger | Condition |
|---|---------|-----------|
| 1 | Angry / Very Angry sentiment | always |
| 2 | High-value order with negative sentiment | order > ₹5,000 |
| 3 | Refund still pending | refund status is `Pending` |
| 4 | Payment deducted but order failed or cancelled | always |
| 5 | AI confidence too low | < 0.40 |
| 6 | The resolution agent asked for a human | `recommended_action == "Escalate"` |

Rule 6 is the one place a model influences the outcome — and even then it only *requests* escalation through a value the deterministic check reads. Escalated tickets appear in the admin **Escalations** queue, where agents can Claim (lock) or Release them.

---

## Project Structure

```
VoiceCare-AI/
├── backend/
│   ├── app/
│   │   ├── agents/          # pipeline.py (9 agents) + state.py
│   │   ├── api/             # voice.py, tickets.py, customers.py, auth.py
│   │   ├── core/            # config, database, errors, constants, rate_limit
│   │   ├── db/models.py     # 15 SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response shapes
│   │   └── services/        # gemini, bhashini, chroma, memory
│   ├── data/policies/       # 12 grounded policy documents (Chroma source)
│   ├── data/seed/           # demo customers, orders, shipments, payments
│   ├── migrations/          # Alembic versions
│   ├── tests/               # 282 backend tests across 7 categories
│   └── main.py              # FastAPI entry point
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages (incl. /tests)
│   │   ├── components/      # VoiceOrb, StatusStream, VoiceView, Footer, …
│   │   ├── hooks/           # useVoiceInteraction (all voice state + WS)
│   │   └── lib/
│   │       ├── api.ts       # typed API client
│   │       ├── constants.ts # LANGUAGES, LANG_TO_BCP47, LANG_TO_LOCALE
│   │       └── i18n/        # I18nProvider + 8 language catalogs
│   ├── e2e/                 # Playwright specs
│   └── next.config.ts
├── .github/workflows/       # CI + keep-alive ping
├── render.yaml              # Render backend deploy config
└── .env.example
```

---

## Running Tests

**324 automated tests, all passing** — 282 backend (pytest), plus frontend unit (Vitest) and end-to-end (Playwright). Browse every one of them, including what each asserts, at **[/tests](http://localhost:3000/tests)** — a public page in the app itself.

```bash
cd backend
pytest                              # everything (282 backend tests)
pytest --cov                        # with coverage; floor is set in .coveragerc
pytest tests/security/test_auth.py  # a single file
```

Tests are grouped by **what they prove**, not by where the file lives. The category is applied automatically from the directory, so `-m <category>` works without hand-marking anything:

| Marker | Directory | Covers |
|---|---|---|
| `unit` | `tests/unit/` | Services and helpers in isolation |
| `integration` | `tests/integration/` | The 9-agent pipeline and dashboard API against a real DB |
| `contract` | `tests/contract/` | WebSocket frame shapes and backend↔frontend payload parity |
| `performance` | `tests/performance/` | Latency budgets, stage concurrency, query-count ceilings |
| `security` | `tests/security/` | Auth, rate limits, input caps, identity, information leaks |
| `multilingual` | `tests/multilingual/` | All 9 languages, native-script round trips |
| `resilience` | `tests/resilience/` | Behaviour when Gemini/Chroma/Bhashini/the DB fails |

```bash
pytest -m performance               # just the latency guards
pytest -m "security or resilience"  # combine categories
```

Frontend — the eighth category, end-to-end, lives here:

```bash
cd frontend
npm run test          # Vitest unit tests
npm run e2e           # Playwright browser tests
```

### Refreshing the /tests page

The page renders a committed JSON artefact, so it works on a deployed build with no test run. Regenerate it after adding or changing tests:

```bash
cd backend  && pytest -q            # writes backend/test-report.json
cd frontend && npm run test:json    # writes frontend/test-reports/vitest.json
npm run e2e                         # writes frontend/test-reports/playwright.json
npm run test:report                 # merges into src/data/test-report.json
```

Each test's description on that page comes from its own docstring, so the page cannot drift from the suite.

---

## Optional: Sentry Error Tracking

1. Create a project at [sentry.io](https://sentry.io) (free)
2. Add to `.env`:

```
SENTRY_DSN=https://xxxx@oXXX.ingest.sentry.io/YYYY          # backend
NEXT_PUBLIC_SENTRY_DSN=https://xxxx@oXXX.ingest.sentry.io/YYYY  # frontend
```

Both sides no-op gracefully without a DSN — safe to leave unset in local dev.

---

## Deployment notes

Frontend deploys to Vercel; the backend runs on Render from `backend/Dockerfile`, which runs `alembic upgrade head` on every boot.

**Free-tier cold starts.** Render spins the backend down after ~15 min idle, and waking it costs about **130 s** (container boot, migrations, then the Chroma embedder and memory-backend warmup in `main.py`'s lifespan). Warm, `/health` answers in ~2 s.

An external uptime monitor pings `https://voicecare-backend.onrender.com/health` every 5 minutes to stay under that idle window — with the alert threshold set to 3 consecutive failures, because the first check after any spin-down is *expected* to fail (monitors cap timeouts near 30 s; a cold start needs ~130 s). It still hands Render the request that starts the boot, and the next check succeeds.

`.github/workflows/keep-alive.yml` does the same ping as a secondary. Don't rely on a GitHub Actions `schedule:` alone for this — measured on this repo, a `*/10 * * * *` cron actually fired 68–211 minutes apart, so the workflow pings on its own timer inside the job rather than trusting the schedule. The full rationale is in that file's header comment.

Neither mechanism replaces the reactive handling in the frontend (`BackendWarmup.tsx`, the login page's "waking up" message) — those still cover deploys and the window before the first ping.
