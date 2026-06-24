# CommerceMind VoiceCare AI — App Flow
### Navigation & User Journey Map

Items neither source document actually specifies are marked 📌 — open decisions, not facts.

---

### Pages List
- `/` — the voice interface: record button + animated, audio-reactive voice orb (no menu tree)
- In-page session state — live status stream and response playback during an active voice session
- `/dashboard` — admin home
- `/dashboard/tickets` — live ticket list and detail view
- `/dashboard/escalations` — escalation queue
- `/dashboard/analytics` — ticket volume by language, category, priority, resolution time
- `/dashboard/tickets/[id]/replay` — step-by-step trace of what each agent decided, and why
- `/dashboard/tickets/[id]/handoff` — auto-generated handoff note for an escalated ticket

📌 Exact page boundaries (e.g. whether replay and handoff are separate routes or drawers within the ticket detail view) aren't specified — pick whichever reads better once the dashboard is being built.

### Navigation Type
Customer side: a single-page, voice-first interface — deliberately no menu tree. Admin side: sidebar navigation across Tickets, Escalations, and Analytics within the dashboard.

### First Screen
A customer lands on a simple voice interface: a record button and an animated voice orb that reacts to their voice in real time — nothing to click through first.

### Auth Flow
📌 Not specified. For customers, the system appears to identify the caller during the Order/Transaction Lookup step rather than through a traditional signup flow — decide whether phone-based verification belongs before that lookup. For support managers, the dashboard needs a login gate before Week 3 — method not yet chosen.

### Core User Journey 1 — Voice Support Resolution (Customer)
Customer opens the app → taps record → speaks naturally (e.g. *"Mera order abhi tak deliver nahi hua"*) → sees a live status stream while the pipeline runs:

```
CUSTOMER VOICE
  → [1] Voice intake (Bhashini STT + language tag)              — code
  → [2] Intent + sentiment + priority                            — 1 LLM call
  → [3] Order / return / refund lookup (Postgres)                — code
  → [4] Policy RAG retrieval (Chroma, top-3)                     — code
  → [5] Resolution decision                                      — 1 LLM call
  → [6] Escalation check (deterministic rule conditions)         — code
  → [7] Response generation (final reply, target language)       — 1 LLM call
  → [8] Text-to-speech (Bhashini TTS)                            — code
  → [9] Ticket + handoff note written to DB                      — code
CUSTOMER HEARS RESPONSE / TICKET APPEARS ON DASHBOARD
```

→ customer hears the spoken response in their own language → a support ticket is created and appears live on the dashboard, with no further action needed from the customer.

*(9 conceptual agents, mapped to only 3 real LLM calls — Intent+Sentiment+Priority, Resolution, and Response — with everything else handled as deterministic code: DB lookups, vector search, and rule checks. Resolution and Response are deliberately kept as two separate calls rather than merged, since that's where policy-groundedness matters most.)*

### Core User Journey 2 — Ticket Review & Escalation (Support Manager)
Manager logs in → sees the live ticket list and escalation queue → opens a specific ticket → reviews the replay trace of exactly what each agent decided and why → if escalated, reads the auto-generated handoff note for full context → takes over the case.

### Empty States
- No tickets yet → empty state on the ticket list
- No pending escalations → empty state on the escalation queue

### Error States
- Bhashini STT/TTS timeout or low quality → timeout + retry, then a graceful fallback message to the customer
- Gemini rate-limit or transient error → automatic retry with exponential backoff (1s, 2s, 4s) using the identical prompt — never a fabricated fallback answer
- Still unavailable after retries → route the identical prompt and context to a backup model
- Live demo network/API failure → fall back to the pre-recorded backup demo video

### Redirects
- Completed voice interaction → ticket appears live on the dashboard via WebSocket, no redirect needed
- Escalation triggered → ticket automatically moves into the escalation queue
