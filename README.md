<div align="center">

# 🎙️ VoiceCare AI

### Voice-first multilingual customer support — powered by a 9-agent AI pipeline

**Speak in Hindi, Tamil, Telugu, Malayalam, Kannada, Bengali, Marathi, or English.**  
Get resolved instantly. No forms. No hold music. No English-only walls.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## What is this?

VoiceCare AI is a production-grade voice support platform for Indian e-commerce. A customer taps one button, speaks their problem in their native language, and receives a voice response — in the same language — in under 10 seconds.

Behind that button: a **9-agent LangGraph pipeline** that transcribes speech, detects intent, queries a live database, retrieves grounded policy context, generates a resolution, checks six deterministic escalation rules, synthesises a response, converts it back to speech, and creates a support ticket — all in a single WebSocket stream.

---

## Demo

| Voice Interface | Pipeline Stream | Admin Dashboard |
|:-:|:-:|:-:|
| 3D audio-reactive orb | 9 stages animate in real time | Tickets, analytics, escalation queue |
| Tap → speak → hear the answer | WebSocket streaming progress | JWT-protected, operator-facing |

**Try these demo queries after seeding:**

| Language | Customer | Say… | Outcome |
|----------|----------|-------|---------|
| 🇮🇳 Hindi | Rajesh Kumar | "मेरा ऑर्डर 5 दिन देर से आया" | ₹50 shipping credit |
| 🇮🇳 Malayalam | Priya Nair | Refund pending 12 days | Auto-escalate — SLA breach |
| 🇮🇳 Tamil | Muthu Selvam | Damaged product received | Replacement or refund |
| 🇮🇳 Telugu | Ananya Reddy | Payment deducted, order cancelled | Auto-escalate — critical |
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

---

## Features

### Customer Voice Interface
- **3D Audio-Reactive Orb** — GLSL shader + react-three-fiber; pulses with your voice
- **9 Indian Languages** — Hindi, Tamil, Telugu, Malayalam, Kannada, Bengali, Marathi, English, Hinglish
- **Multilingual UI** — the interface itself switches language when you pick a language pill
- **Real-Time Stage Stream** — watch each of the 9 pipeline stages animate over WebSocket
- **Voice + Text Input** — MediaRecorder API or keyboard
- **TTS Playback** — hear the response in your chosen language (Bhashini; falls back to browser TTS)
- **WS Reconnection** — 3× retry with 1s / 2s / 4s backoff on dropped connections

### AI Pipeline
- Gemini 2.5 Flash — intent classification, resolution generation, response synthesis
- Policy RAG — top-3 Chroma results for every query; 1-hour result cache
- Deterministic escalation — 6 hard rules (sentiment, order value, refund SLA, payment anomalies, AI confidence)
- Groq Whisper fallback if Bhashini STT is unavailable
- Tenacity retry (3×) on every external call

### Admin Dashboard
- **Overview** — 6 KPI cards, language volume bars, ticket-type breakdown, live escalation queue
- **Tickets** — filterable list with priority/status badges
- **Ticket Detail** — 3 tabs: Details, Agent Replay Timeline (full `agent_trace`), Handoff Note
- **Escalations** — priority queue with Claim / Release workflow
- **Analytics** — Recharts bar/pie/line charts
- **JWT Auth** — 24-hour tokens, route-guarded with Next.js middleware proxy

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
| LLM | Google Gemini 2.5 Flash |
| STT / TTS | Bhashini API (primary) · Groq Whisper (STT fallback) |
| Vector Store | Chroma (embedded, persistent to disk) |
| Database | PostgreSQL (Neon) via SQLAlchemy Async + asyncpg |
| Session Cache | In-process Python dict (TTL-based, 50-turn history cap) |
| Migrations | Alembic |
| Error Tracking | Sentry (optional) |
| Hosting | Vercel (frontend) · Render / Railway (backend) |

---

## Quick Start

### Prerequisites
- Node.js 18+, Python 3.12+
- PostgreSQL (or a free [Neon](https://neon.tech) account)
- [Gemini API key](https://ai.google.dev)
- [Groq API key](https://console.groq.com) (free tier)
- Bhashini credentials (optional — voice falls back to browser TTS without them)

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
python -m app.utils.seed_db    # seed demo users, orders, tickets
uvicorn main:app --reload --port 8000
```

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
| http://localhost:8000/docs | FastAPI interactive docs |
| http://localhost:8000/health | Health check (DB + Chroma) |
| http://localhost:8000/metrics | Latency percentiles (P50/P95/P99) |

---

## Security

- JWT auth (HS256, 24-hour expiry) on all admin routes
- Secrets validated at startup in production — server refuses to start with empty keys
- Security headers on every response (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `X-XSS-Protection`)
- CORS restricted to `FRONTEND_URL` + Vercel preview wildcard
- WebSocket payloads validated with Pydantic; audio size capped at 10 MB
- Rate limiting: 5 voice queries/min per session (fail-secure — 503 on limiter failure)
- Soft deletes on Users, Orders, and Tickets — data never hard-deleted
- `send_default_pii: false` in Sentry — no IP or user data sent to error tracking

---

## Escalation Rules

Six hard-coded triggers — no LLM involved:

| # | Trigger | Threshold |
|---|---------|-----------|
| 1 | Angry / Very Angry sentiment | always |
| 2 | High-value order with complaint | > ₹5,000 |
| 3 | Refund pending beyond SLA | > 10 days |
| 4 | Payment deducted, no order | always |
| 5 | AI confidence too low | < 0.60 |
| 6 | Repeated contact on same issue | 3+ tickets |

Escalated tickets appear in the admin **Escalations** queue, where agents can Claim (lock) or Release them.

---

## Project Structure

```
VoiceCare-AI/
├── backend/
│   ├── app/
│   │   ├── agents/          # pipeline.py (9 agents) + state.py
│   │   ├── api/             # voice.py, tickets.py, auth.py
│   │   ├── core/            # config, database, errors, constants
│   │   ├── db/models.py     # 15 SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response shapes
│   │   └── services/        # gemini, bhashini, chroma, memory
│   ├── data/policies/       # 12 grounded policy documents (Chroma source)
│   ├── migrations/          # Alembic versions
│   ├── tests/               # 57 unit tests (pytest + aiosqlite)
│   └── main.py              # FastAPI entry point
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # VoiceOrb, StatusStream, VoiceView, Footer, …
│   │   ├── hooks/           # useVoiceInteraction (all voice state + WS)
│   │   └── lib/
│   │       ├── api.ts       # typed API client
│   │       ├── constants.ts # LANGUAGES, LANG_TO_BCP47, LANG_TO_LOCALE
│   │       └── i18n/        # I18nProvider + 8 language catalogs
│   ├── sentry.client.config.ts
│   └── next.config.ts
├── .env.example
└── CLAUDE.md                # AI assistant context file
```

---

## Running Tests

```bash
cd backend
pytest                          # all 57 tests
pytest -m unit                  # unit only (no DB, no external calls)
pytest tests/unit/test_auth.py  # specific file
```

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

## License

MIT — build on it, learn from it, ship it.
