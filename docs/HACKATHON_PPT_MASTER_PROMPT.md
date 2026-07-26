# VoiceCare AI — Hackathon Pitch Deck: Master Prompt

Paste the block below into any AI slide generator (Gamma, Tome, Canva Magic Design, Beautiful.ai,
ChatGPT + a slides plugin, or Claude/GPT itself if you want raw HTML/PPTX). It is self-contained —
the tool does not need any other context about the project.

---

## PROMPT

You are a senior pitch-deck designer creating a **6-slide, awards-caliber hackathon deck** for a
project called **VoiceCare AI**. Design quality matters as much as content — this deck needs to look
like it came from a funded startup's investor deck, not a student template. Judges see dozens of
decks; this one needs to visually stop them.

### Design direction (non-negotiable)
- **Style**: dark editorial / tech-forward — deep charcoal or near-black background (`#0B0D12`
  range), one confident accent color (electric violet/indigo `#6C5CE7` or teal `#22D3B8` — pick one
  and use it consistently), warm off-white text. No default "clean minimal white slide with blue
  bullet points" look — that reads as a template.
- **Typography**: one strong display font for headlines (geometric sans like Space Grotesk, Sora, or
  Clash Display), one clean workhorse font for body (Inter or similar). Big scale contrast — headlines
  should be dramatically larger than body copy, not a uniform size step.
- **Layout**: break the grid. Avoid centered-title + bullet-list on every slide. Use asymmetric
  composition, generous negative space, at least one full-bleed visual moment, and a repeating
  diagram motif for the "how it works" slide (a pipeline / flow, not a screenshot dump).
- **Hierarchy**: every slide has ONE dominant idea rendered large, with supporting detail
  deliberately smaller and quieter. Never let two elements compete for attention.
- **Motion (if the tool supports it)**: subtle entrance animation on key numbers/diagram nodes only —
  never decorative motion for its own sake.
- **No stock-photo clichés** (call centers, headset models, generic Indian flag imagery). Prefer
  abstract waveform / voice / language-glyph motifs, real UI screenshots of the actual product, or
  clean iconography.
- Exactly **6 slides**. No more, no less.

### The product (facts to use — do not invent stats or features beyond this)

**VoiceCare AI** is a voice-first, multilingual customer support platform for Indian e-commerce.
A customer speaks a question in their own language — Hindi, English, Malayalam, Tamil, Telugu,
Kannada, Bengali, Marathi, or Hinglish — and gets a spoken answer back in that same language,
end to end, with no typing and no human agent required for most queries.

**The problem it solves**: Indian e-commerce support is built around English-first chat and IVR
menus. Hundreds of millions of users are far more comfortable speaking than typing, and are far
more comfortable in their mother tongue than in English. That gap causes abandoned support
interactions, frustrated customers, and support queues clogged with issues a system could resolve
instantly if it just met the customer in their own language and voice.

**How it works** — a 9-agent pipeline processes every query in sequence:
1. Speech-to-Text (multilingual voice capture)
2. Intent Detection (understands what the customer actually wants — LLM-powered)
3. Database Lookup (pulls the real order/shipment/refund/payment record)
4. Policy Retrieval (RAG over the store's actual policy documents, so answers are grounded in real
   policy, not hallucinated)
5. Resolution Generation (LLM drafts the actual fix/answer)
6. Escalation Check — **deterministic, not AI-guessed**: six hard business rules (sentiment, order
   value, refund status, payment anomalies, confidence score) decide if a human needs to step in
7. Response Generation (final, natural-language answer — LLM-powered)
8. Text-to-Speech (spoken back in the customer's own language)
9. Ticket Creation (full trace of what every agent did is logged for auditability/handoff)

Only 3 of the 9 stages are LLM calls (Gemini 2.5 Flash) — the rest are deterministic code, which
keeps the system fast, auditable, and cheap to run at scale, and means escalation decisions are
never a black box.

**Who it helps**: end customers who'd rather speak than type and want an answer in their own
language; support teams who get pre-resolved tickets with a full reasoning trace instead of a raw
inbox; and businesses who can deploy multilingual voice support without hiring native speakers for
every language.

**What's built today**: end-to-end pipeline (WebSocket real-time + HTTP fallback), 9 Indian
languages, live admin dashboard (ticket queue, analytics, escalation monitoring, per-ticket agent
replay showing exactly what each of the 9 agents did), deterministic escalation engine, ticket
audit trail.

### Slide-by-slide content brief

**Slide 1 — Title / Hook**
Project name "VoiceCare AI" as the dominant visual element. One sharp one-line hook underneath
(something like: *"Support that speaks your language — literally."*). No logo-and-tagline template
feel; make this slide feel like a product launch splash screen.

**Slide 2 — The Problem**
One big, human-scale framing of the language/voice gap in Indian e-commerce support — lead with the
human cost (frustration, abandoned support, English-only friction), not a wall of market stats.
Optionally one supporting stat about India's linguistic diversity if it strengthens rather than
clutters the slide.

**Slide 3 — The Solution**
Introduce VoiceCare AI as the answer in one clear sentence, then show — visually, not as bullets —
the core loop: customer speaks in their language → AI understands and resolves → AI speaks back in
the same language. This is the "aha" slide; make the loop feel effortless.

**Slide 4 — How It Works**
The 9-agent pipeline as a clean horizontal or circular flow diagram, grouped into clear phases
(Understand → Look Up & Ground in Policy → Resolve → Decide (Escalate or Not) → Respond → Log).
Call out visually that escalation is a deterministic rule engine, not an AI guess — that's a
credibility/trust point judges should register at a glance. Don't cram all 9 as equal-weight boxes;
group them so the diagram reads in 2 seconds, not 20.

**Slide 5 — Impact & Who It's For**
Three audiences, three payoffs, laid out asymmetrically (not a 3-equal-column template):
customers (their own language, spoken, instantly), support teams (pre-resolved tickets + full
reasoning trace instead of a cold inbox), businesses (multilingual support without hiring
per-language agents). Make the differentiation land: deterministic, auditable escalation — not a
black box — is the trust story.

**Slide 6 — What's Built & What's Next**
Split the slide: left/top = what's live today (real-time voice pipeline, 9 languages, admin
dashboard with full agent replay, deterministic escalation, ticket audit trail) as a confident
"shipped" list; right/bottom = a short, credible near-term roadmap (e.g., more languages, deeper
analytics, multi-turn conversation memory). End on a single closing line that reinforces the hook
from slide 1 — bring it full circle.

### Output format
Generate the deck now using the design direction and content brief above. If the tool can export
editable slides (Figma, PPTX, Google Slides), do so; if it only renders HTML/canvas, produce a
single scrollable HTML file with one `<section>` per slide sized for a 16:9 presentation frame.

---

## Tips for using this prompt

- If your slide tool lets you set a color/font theme separately from the prompt, set the palette to
  charcoal `#0B0D12` + one accent (`#6C5CE7` violet or `#22D3B8` teal) before generating — it locks
  the look in and stops the tool from defaulting to a light template.
- Screenshot the actual login/dashboard/voice-orb UI and drop it into slide 3 or 6 if your tool
  supports image uploads — a real product shot beats any illustration for hackathon judges.
- If the tool caps you below 6 slides worth of content, cut slide 6's roadmap half before cutting
  anything from slides 3–4 — the "how it works" and "solution" slides are what judges remember.
