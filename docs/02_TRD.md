# CommerceMind VoiceCare AI — TRD
### Technical Requirements Document

Items neither source document actually specifies are marked 📌 — open decisions, not facts.

---

### Frontend
Next.js 14 + TypeScript · Tailwind CSS + shadcn/ui (clean, fully custom — not generic component defaults) · Framer Motion for transitions and live status animations · react-three-fiber / Canvas for the audio-reactive voice orb · Lottie for loading/thinking/success micro-animations · Tremor / Recharts for dashboard analytics · WebSockets for streaming agent progress to the UI in real time.

*(The original concept specified a Streamlit frontend — the finalized blueprint supersedes this with the stack above.)*

### Backend
FastAPI for REST + WebSocket endpoints · LangGraph for multi-agent state-machine orchestration · LangChain for policy-retrieval (RAG) plumbing · Chroma as the embedded, zero-cost vector store for policy embeddings · PostgreSQL (Neon or Supabase) as the production data store for the 15-table schema · Redis (Upstash) for conversation memory, response caching, and throttle bookkeeping.

### Database
PostgreSQL via Neon, with Supabase as an alternative — see the Backend Schema document for the full 15-table design.

### Auth
📌 Not specified in either source. The customer flow appears to identify customers via phone/order lookup rather than a full account system — decide before Week 1 whether a lightweight verification step (e.g. phone OTP) belongs before exposing real order data. The admin dashboard needs authenticated login for support managers — method (Supabase Auth, NextAuth, etc.) not yet chosen.

### Hosting
Vercel for the Next.js frontend (instant deploys) · Railway or Render for the Docker-packaged FastAPI backend · Neon for Postgres · Upstash for Redis — a live, public URL by Week 4, not just local Docker.

### Third-Party APIs
| Service | Purpose | Tier |
|---|---|---|
| Bhashini | Speech-to-Text and Text-to-Speech across all 8 target languages | Free, government-hosted — apply early, approval has lead time |
| Gemini 2.5 Flash-Lite | Reasoning / structured-output LLM calls | Must move to pay-as-you-go before Week 2 — the free tier's rate ceiling caused dev failures |
| Chroma | Policy embeddings / vector search | Free, embedded |

### Key Libraries
LangGraph, LangChain, Framer Motion, react-three-fiber, Lottie, Tremor or Recharts, shadcn/ui.

### Environment Variables
Bhashini API credentials · Gemini API key (paid tier) · Neon Postgres connection string · Upstash Redis URL/token · Chroma persistence path · session/auth secret 📌 (once an auth method is chosen) · Vercel and Railway/Render deployment tokens.

### Constraints
- Must support 8 Indian languages + Hinglish — the core differentiator, not an optional extra
- Must be off the Gemini free tier before voice work begins in Week 2 — the rate limit is a hard ceiling, not something prompting can work around
- Session/cache state must live in Redis, never an in-memory Python dictionary, so it survives multiple backend instances behind a load balancer
- Retries on rate-limit or transient errors must reuse the identical prompt and never fall back to a fabricated answer
- Hosting budget: mostly free-tier, with a $10–$25/month buffer to avoid cold-starts during a live demo
- A pre-recorded backup demo video must exist in case the live demo's network or APIs fail
- All policy documents and seed/demo data must be entirely fictional — no real company policy, no real customer PII — confirmed before any public sharing
