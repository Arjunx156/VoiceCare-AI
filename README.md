# 🎙️ CommerceMind VoiceCare AI

**Voice-first multilingual e-commerce customer support powered by AI.**

Speak in Hindi, Tamil, Telugu, Malayalam, Kannada, Bengali, Marathi, or English — get resolved instantly. A 9-agent LangGraph pipeline processes every query through intent detection, policy-grounded RAG, deterministic escalation, and auto-generated handoff notes.

---

## ✨ Features

### Customer Voice Interface
- **3D Audio-Reactive Orb** — GLSL shader-based voice orb (react-three-fiber) that responds to audio input in real-time
- **9-Language Support** — Hindi, English, Tamil, Telugu, Malayalam, Kannada, Bengali, Marathi (+ Hinglish)
- **Real-Time Pipeline Stream** — Watch each stage animate as your query moves through the 9-agent pipeline
- **Voice + Text Input** — Record audio via MediaRecorder API or type in any language
- **TTS Response Playback** — Hear the AI response in your chosen language

### AI Pipeline (9 Agents)
| # | Agent | Type | Purpose |
|---|-------|------|---------|
| 1 | STT Agent | Bhashini API | Speech-to-text in 8 languages |
| 2 | Intent & Sentiment | Gemini LLM | Classify intent + detect sentiment |
| 3 | Data Retrieval | Database | Fetch order, shipment, return data |
| 4 | Policy RAG | Chroma (embedded) | Retrieve relevant policy sections |
| 5 | Resolution | Gemini LLM | Generate policy-grounded resolution |
| 6 | Escalation Check | Deterministic | 5 rule-based escalation triggers |
| 7 | Response Generator | Gemini LLM | Natural language response |
| 8 | TTS Agent | Bhashini API | Text-to-speech in customer's language |
| 9 | Ticket Creator | Database | Persist ticket + resolution + trace |

### Admin Dashboard
- **Overview** — Stats grid, escalation queue, language/category breakdown
- **Tickets** — Filterable table with priority/status badges
- **Ticket Detail** — 3-tab view: Details, Agent Replay Timeline, Handoff Note
- **Escalations** — Priority-sorted queue for human review
- **Analytics** — Recharts bar/pie charts across all dimensions

### Policy RAG
- **12 fictional policy documents** with concrete numbers (SLAs, amounts, timelines)
- **Chroma embedded** — runs inside the Python process, zero setup, zero cost
- Top-3 policy retrieval with similarity scoring

### Escalation Rules (Deterministic)
1. 😠 Angry/Very Angry sentiment → Auto-escalate
2. 💰 High-value order (>₹5,000) with complaint → Auto-escalate
3. ⏰ Refund pending beyond 10-day SLA → Auto-escalate
4. 💳 Payment deducted but order not created → Auto-escalate
5. 🤖 AI confidence < 0.6 → Auto-escalate

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS, Framer Motion |
| **3D Voice Orb** | react-three-fiber, Three.js, GLSL shaders |
| **Charts** | Recharts |
| **Backend** | FastAPI, Python 3.12 |
| **AI Orchestrator** | LangGraph (9-agent pipeline) |
| **LLM** | Google Gemini 2.5 Flash-Lite |
| **STT/TTS** | Bhashini API (8 Indian languages) |
| **Vector Store** | Chroma (embedded, persistent) |
| **Database** | PostgreSQL (Neon) via SQLAlchemy Async |
| **Cache/Memory** | In-process Python dict (TTL-based, 50-turn history cap) |
| **Hosting** | Vercel (FE), Railway/Render (BE) |

---

## 📂 Project Structure

```
VoiceCare-AI/
├── backend/
│   ├── app/
│   │   ├── agents/          # 9-agent LangGraph pipeline
│   │   │   ├── pipeline.py  # Full orchestration (640 lines)
│   │   │   └── state.py     # PipelineState schema
│   │   ├── api/             # FastAPI routes
│   │   │   ├── voice.py     # POST /api/voice/query + WebSocket
│   │   │   └── tickets.py   # GET tickets, analytics, handoff
│   │   ├── core/            # Config, database, security
│   │   ├── db/models.py     # 15 SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Gemini, Bhashini, Chroma, Redis
│   │   └── utils/           # Seed script
│   ├── data/
│   │   ├── policies/        # 12 fictional policy documents
│   │   └── seed/            # Demo seed data (5 scenarios)
│   ├── main.py              # FastAPI entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Voice interface (orb + recording)
│   │   │   └── dashboard/
│   │   │       ├── page.tsx          # Overview
│   │   │       ├── tickets/page.tsx  # Ticket list
│   │   │       ├── tickets/[id]/     # Ticket detail + replay
│   │   │       ├── escalations/      # Escalation queue
│   │   │       └── analytics/        # Charts
│   │   ├── components/
│   │   │   ├── VoiceOrb.tsx          # 3D GLSL orb
│   │   │   └── StatusStream.tsx      # Pipeline status animation
│   │   └── lib/api.ts               # Type-safe API client
│   └── package.json
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.12+
- PostgreSQL (or Neon account)
- Redis (or Upstash account)
- Bhashini API credentials
- Google Gemini API key

### 1. Clone & Configure

```bash
git clone https://github.com/Arjunx156/VoiceCare-AI.git
cd VoiceCare-AI
cp .env.example .env
# Fill in your real API keys in .env
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# Seed the database + ingest policies into Chroma
python -m app.utils.seed_db

# Start the server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cp ../.env.example .env.local  # Edit NEXT_PUBLIC_BACKEND_URL
npm run dev
```

### 4. Open

- **Voice Interface**: http://localhost:3000
- **Admin Login**: http://localhost:3000/login (email + password from `.env`)
- **Admin Dashboard**: http://localhost:3000/dashboard (redirects to login if not authenticated)
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🔒 Security & Auth

- All API keys, secrets, and `.env` files are in `.gitignore`
- `.env.example` contains only placeholder values
- CORS restricted to frontend URL + Vercel preview domains
- Security headers on every response: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`

### Admin Authentication

The dashboard is protected by JWT auth. Set credentials in `.env`:

```
ADMIN_EMAIL=admin@voicecare.ai
ADMIN_PASSWORD=your_secure_password
NEXTAUTH_SECRET=your_jwt_signing_secret
```

- `POST /api/auth/login` — returns a 24-hour JWT (HS256)
- All `/api/tickets/*` routes require `Authorization: Bearer <token>`
- Frontend stores token in `localStorage`; `vc_logged_in` cookie gates the Next.js route proxy
- Navigating to `/dashboard` without a valid session redirects to `/login`
- Any `401` response from the API clears the token and redirects to `/login` automatically

---

## 📊 Demo Scenarios

The seed data includes 5 pre-built scenarios to demonstrate the pipeline:

| # | Customer | Language | Scenario | Expected Outcome |
|---|----------|----------|----------|-----------------|
| 1 | Rajesh Kumar | Hindi | Delayed delivery (5 days overdue) | ₹50 shipping credit |
| 2 | Priya Nair | Malayalam | Refund pending >10 days | Auto-escalate (SLA breach) |
| 3 | Muthu Selvam | Tamil | Damaged product received | Replacement or refund |
| 4 | Ananya Reddy | Telugu | Payment deducted, order cancelled | Auto-escalate (critical) |
| 5 | Amit Sharma | Hinglish | Wrong product + angry | Auto-escalate (sentiment) |

---

## 📜 License

MIT
