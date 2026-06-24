# CommerceMind VoiceCare AI — Implementation Plan
### Step-by-Step Build Sequence

Items neither source document actually specifies are marked 📌 — open decisions, not facts.

---

### Dependencies & Approvals Needed (before Phase 1)
| Ask | Why | Urgency |
|---|---|---|
| Bhashini API access | Free but government-hosted — approval has lead time | Apply today |
| Gemini pay-as-you-go billing | Removes the free-tier rate ceiling that caused dev failures | Critical, before Phase 2 |
| Hosting budget | Mostly free-tier; a small buffer avoids cold-starts during a live demo | $10–$25/month |
| Sign-off: policy docs are fictional | The team is authoring its own shipping/refund/return policies, not real company policy | Before public sharing |
| Sign-off: seed/demo data is fictional | No real customer names, phone numbers, or addresses anywhere | Before public sharing |
| Team role allocation (if not solo) | Suggested split: backend/agents, frontend/motion design, DB+DevOps+QA | Phase 1 |

### Phase 1 (Week 1) — Foundation
- Repo setup; Postgres (Neon) schema migration; Redis (Upstash) connected; Next.js skeleton deployed to Vercel from day one
- Write all 12 policy documents with concrete, quotable numbers (timelines, eligibility windows — vague policy text is the single biggest cause of weak RAG retrieval); ingest into Chroma
- Build the text-only pipeline: Intent+Sentiment+Priority call → Lookup → Policy RAG → Resolution call
- Add the escalation rule-check (code, not LLM) and the response-generation call; persist a ticket for every run
- Lock the shared pipeline state schema by the end of this phase — treat later changes as deliberate, reviewed decisions
- **Done when:** a typed English query produces a full, grounded, ticketed response via the API

### Phase 2 (Week 2) — Voice + Visual Layer
- Wire Bhashini STT and TTS behind a provider-abstraction interface, across the first 2–3 languages
- Build the Next.js voice UI: record button, audio-reactive voice orb, Framer Motion status stream, response playback
- Connect the WebSocket pipeline end-to-end; get the order-delay and refund-delay demo scenarios fully working in voice
- **Done when:** speaking in any supported language shows live animated progress, produces a natural voice response, and creates a ticket

### Phase 3 (Week 3) — Full Language Coverage + Dashboard
- Extend voice intake/response to all remaining languages; recruit native-speaker review for each
- Build the admin dashboard (ticket list, escalation queue, analytics charts)
- Build the ticket "replay" view and the auto-generated escalation handoff note
- Add Redis-backed multi-turn memory and response caching
- **Done when:** all 8 languages work end-to-end, the dashboard is fully functional, and all demo scenarios are covered

### Phase 4 (Week 4) — Hardening, Production Deployment & Submission
- Internal QA pass: run the policy-groundedness trick-question test set against every language; fix any gaps found
- Add retry/backoff and client-side throttling around every Gemini call
- Deploy for real: Vercel (frontend), Railway/Render (backend), Neon (DB), Upstash (Redis) — a live public URL, not just local Docker
- Record the demo video; finalize the README and architecture diagram; write the final report
- **Done when:** the product is live and publicly reachable, with a full demo rehearsal completed and a backup recorded video ready

### Demo Scenarios to Validate Before Submission
1. Order delay in Hindi
2. Refund delay in Malayalam
3. Damaged product in Tamil
4. Payment failed but money deducted
5. Angry, repeat-complaint customer → human escalation

### Key Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Bhashini latency/quality varies by language | Timeout + retry + graceful fallback message; native-speaker review per language |
| Live demo depends on venue network/APIs | Always have a pre-recorded backup demo video ready |
| Concurrent sessions colliding | State lives in Redis/Postgres, never a bare in-memory dictionary |
| Multilingual RAG retrieval drift | Translate the customer query to English before vector search |
| Quality blind spots in languages the team doesn't speak | Line up native-speaker testers before Phase 3 |
| Mid-project schema changes silently breaking the pipeline | Lock the shared pipeline state schema by the end of Phase 1 |
| API quota exhaustion during a live demo | Paid tier + backoff + throttling + Redis caching |

### Overall Done Criteria
All 5 demo scenarios work end-to-end in voice, across all 8 languages + Hinglish; every interaction produces an auditable ticket with a traceable policy reference; the dashboard shows a live ticket list, escalation queue, and analytics; the deployment is live and publicly reachable; and a backup demo video exists.

---

### Open Decisions Checklist
A few things neither source pins down — worth deciding early enough that they don't block a phase:
- [ ] Auth method for customers (if any) and for the admin dashboard
- [ ] Color palette, font, dark/light mode default
- [ ] File storage provider for audio files
- [ ] Which 5 escalation rule conditions make the final cut (from the original 8-condition candidate pool)
- [ ] Whether to track product-wise and courier-wise complaint analytics (in the original concept, dropped from the finalized feature set)
- [ ] Whether/when to revisit the broader CommerceMind AI family integrations

### Source Documents
Based on *CommerceMind VoiceCare AI — Project Blueprint* (finalized direction, June 2026) and the original *CommerceMind VoiceCare AI* concept brief, mapped onto the 6-document AI-agent build framework (PRD → TRD → App Flow → UI/UX Brief → Backend Schema → Implementation Plan).
