# CommerceMind VoiceCare AI — PRD
### Product Requirements Document

Items neither source document actually specifies are marked 📌 — open decisions, not facts.

---

### App Name
CommerceMind VoiceCare AI

### Tagline
"Speak Your Language. Get Resolved Instantly."

### Problem
E-commerce platforms handle a high daily volume of repetitive support queries — order status, refund delays, returns, damaged or wrong items, payment failures, cancellations, exchanges. Most existing support tooling is English-first, text-first, and menu-driven, but a large share of Indian customers are more comfortable speaking their own language than typing in English. Text chatbots and rigid IVR menus don't understand natural spoken language or adapt to context. The result: long resolution times, customer frustration, and a high cost-per-ticket for issues that are fundamentally simple and repeatable.

### Target User
**Primary — the customer:** an e-commerce shopper in India who is more comfortable speaking Hindi, Malayalam, Tamil, Telugu, Kannada, Bengali, Marathi, or Hinglish than typing in English, with a common, recurring issue (where's my order, why is my refund late, I got the wrong item) they want resolved quickly without navigating a menu tree.

**Secondary — the support manager:** someone who needs live visibility into ticket volume and escalations, plus an auditable trace of what the AI decided and why, so they can step into complex cases with full context.

### Core Value Proposition
Genuine voice-first support across 8 Indian languages plus Hinglish (not just English + Hindi); answers strictly grounded in retrieved company policy and real order/refund/return data — never invented; explainable, rule-based escalation logic; and a system built for real production deployment (session memory, caching, retries, live cloud hosting) rather than a one-off laptop demo.

### Core Features (Must Have)
**Customer-facing**
- Natural voice query in any of 8 Indian languages, or Hinglish — no typing, no menus
- Live animated voice orb that reacts to the customer's voice in real time
- Real-time streaming status while the system works (Listening → Understanding → Checking your order → Finding the right policy → Responding)
- Multi-turn conversation memory — follow-ups are understood in context
- Grounded order / return / refund / payment status lookup against real order data
- Policy-grounded answers only, with a visible reference to the policy used — never invented
- Automatic escalation to a human agent for complex, urgent, or policy-exception cases
- Spoken response delivered back in the customer's own language

**Admin dashboard (support-manager facing)**
- Live ticket list and detail view
- Escalation queue
- Analytics: ticket volume by language, category, priority, and resolution time
- Ticket "replay" view — a step-by-step trace of what each agent decided, and why
- Auto-generated handoff notes for every escalated ticket

### Nice to Have
- Sentiment-aware response tone adaptation when a customer is frustrated
- Product-wise and courier-wise complaint analytics — present in the original concept brief but not carried into the finalized feature set 📌
- Fallback model routing surfaced as a visible reliability indicator on the dashboard (currently a backend-only safety net)
- Broader CommerceMind AI family integrations (see Out of Scope)

### Out of Scope
- A live, customer- or dashboard-facing "adversarial trick-question" panel — explicitly removed from the product surface; preserved only as an internal QA process run before each release
- Typing/chat as the primary interaction mode — voice-first is the core differentiator (the original concept used a Streamlit chat-style UI; the finalized blueprint replaces this with a Next.js voice-first interface)
- Building proprietary STT/TTS or LLM models — the system uses Bhashini (STT/TTS) and Gemini 2.5 Flash-Lite (reasoning), not custom models
- Integration with the wider CommerceMind AI family (Ops AI, Strategy AI, Recommender AI, PricePulse AI, TrustGuard AI, CampaignPilot AI) — named in the original concept as a future direction, not part of the finalized 4-week scope 📌
- Real customer data and real company policy — all seed/demo data and policy documents are fictional, pending management sign-off before any public sharing

### User Stories
- As a **customer**, I want to speak naturally in my own language so that I don't have to type or navigate a menu tree.
- As a **customer**, I want the system to check my real order, return, refund, or payment status so that I get an accurate answer instead of a generic one.
- As a **customer**, I want the AI's answer grounded in the actual company policy so that I'm never given an invented resolution.
- As a **customer**, I want to be automatically escalated to a human when my issue is complex or I'm upset so that I'm not stuck in an automated loop.
- As a **customer**, I want to hear the response spoken back in my own language so the whole interaction feels natural.
- As a **support manager**, I want a live ticket list and escalation queue so that I can prioritize urgent cases.
- As a **support manager**, I want a step-by-step replay of what each agent decided so that I can audit any resolution.
- As a **support manager**, I want an auto-generated handoff note on every escalated ticket so a human agent has full context instantly.

### Success Metrics
**Build checkpoints** (from the 4-week plan):
- Week 1: a typed English query produces a full, grounded, ticketed response via the API
- Week 2: speaking in a supported language produces live animated progress, a natural voice response, and a created ticket
- Week 3: all 8 languages work end-to-end and the dashboard is fully functional
- Week 4: a live, publicly reachable product, with a full demo rehearsal and a backup recorded video ready

**Quality metrics** (from the original evaluation plan): STT accuracy, language-detection accuracy, intent accuracy, policy-retrieval accuracy, resolution accuracy, escalation accuracy, response quality, voice (TTS) quality, ticket-creation accuracy.

**Reliability target:** the pipeline survives a live, multi-person demo (concurrent voice sessions) without tripping Gemini's rate limit, via the paid tier + backoff + throttling + caching stack.
