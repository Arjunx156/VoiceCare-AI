# CommerceMind VoiceCare AI — UI/UX Design Brief
### Visual & Interaction Design Guide — v2

This replaces v1's open color/typography/motion questions with a locked direction, taken from a dark, single-accent, editorial reference: near-black canvas, one confident warm accent carrying every interactive moment, a small colored "eyebrow" label above every headline, pill-shaped buttons with a dot/icon motif, rounded photographic cards treated with gradient color overlays instead of flat photos, and a clean list-row pattern (label · bold title · divider · tag) for itemized content. Nothing here is a generic component-library default — every choice below is specific on purpose.

---

### Aesthetic
Dark, confident, editorial. Each section of the product should read like its own well-composed panel — one clear idea, one headline, generous breathing room — never a crowded dashboard despite the dark canvas. No glassmorphism, no default card shadows, no purple-gradient "AI product" cliché.

### Color Palette
| Token | Value | Use |
|---|---|---|
| `bg-base` | near-black, ~#0B0B0C | App background, voice screen |
| `bg-panel` | dark charcoal, ~#161616 | Cards, dashboard panels, outlined cards |
| `bg-panel-raised` | ~#1E1E1F | Hover state of panels, raised/active cards |
| `accent` | warm coral-orange, ~#FF5A2B | Brand accent only — eyebrow labels, primary buttons, the voice orb's resting glow, active nav state, dividers |
| `text-primary` | off-white, ~#F5F5F5 | Headlines |
| `text-secondary` | muted grey, ~#9A9A9A | Body copy, captions |
| `border-subtle` | ~#262626 | Card outlines, divider lines |

`accent` is reserved for brand/interactive moments only. Ticket priority and sentiment get their **own** semantic colors so they're never confused with the brand color:

| Semantic | Color |
|---|---|
| Priority: Low | muted green |
| Priority: Medium | amber/yellow |
| Priority: High | red-orange — deliberately more red/saturated than `accent`, so it reads as "alert," not "brand" |
| Priority / Status: Critical, Escalated | red |
| Sentiment: Calm, Confused | grey-blue |
| Sentiment: Angry, Very angry | red |

### Typography
- **Headlines:** bold, tight line-height, geometric sans (Inter at 700/800, or General Sans / Söhne if available) — large sizes (40–64px on desktop dashboard headers and the voice screen's main prompt), left-aligned, never small-and-centered
- **Body:** same family, regular/medium weight, 15–17px, `text-secondary`
- **Eyebrow/label:** same family, semibold, 12–13px, uppercase, letter-spacing ~0.08em, set in `accent` — every section or card gets one above its heading (e.g. "ESCALATION QUEUE" above "3 tickets need you")
- **Numerals** (pipeline steps, ticket counts, live stats) use a tabular/monospaced numeral setting so live-updating numbers don't jitter or reflow

### Shape
- Cards/panels: 16–20px radius
- Buttons: fully pill-shaped (`border-radius: 999px`) — the *only* button shape in the product, used for every CTA, the record button, and dashboard filter chips
- Images and thumbnails (ticket attachments, replay-step cards): 12px rounded-rect

### Depth
No drop shadows anywhere. Depth comes from color contrast (`bg-base` vs `bg-panel` vs `bg-panel-raised`) plus a 1px `border-subtle` outline. This is what keeps it reading as production-grade instead of a default UI kit.

### Dark / Light Mode
Dark only, by design — it suits a live voice + animated-status interface where glowing elements need real contrast to read well. No light mode for v1.

---

### Component Patterns

**Voice screen (customer-facing)**
- `bg-base` background. A small `accent` eyebrow ("LISTENING" / "VOICE SUPPORT") sits above the large instruction headline, same eyebrow-then-headline pattern used everywhere else in the product
- The voice orb: a 3D gradient sphere (react-three-fiber) — `accent` coral-orange core blending to black at the edges, the same warm duotone treatment as the reference's gradient-toned photography
- Record button: pill, `accent`-filled, small white mic/dot icon inside
- Below the orb: a horizontal row of small muted-grey language pills (Hindi · Tamil · Telugu · Bengali · Marathi · Kannada · Malayalam · Hinglish) — a trust-bar pattern repurposed to say "here's what I understand" instead of "brands we've worked with"

**Status stream (the 9-step agent pipeline)**
- Rendered as a live numbered list (01–09): each row is a numeral + label that shifts from muted grey to `text-primary` + `accent` numeral the instant the pipeline reaches that stage, with a thin pill-shaped progress indicator trailing behind

**Admin dashboard — ticket list**
- An editorial list-row pattern: a small `accent` eyebrow (ticket type, e.g. "REFUND") above a bold ticket title/customer name, a thin `border-subtle` divider between rows, and a small status pill on the right (Open / In Progress / Escalated)

**Escalation queue / priority cards**
- Outlined `bg-panel` cards for Low/Medium priority; one visually "raised" card style (filled background, corner badge) for whatever needs attention right now — using the semantic alert color, never `accent`, so urgency never looks like a marketing CTA

**Analytics**
- Asymmetric two-column block layout rather than a uniform grid: the most important chart (ticket volume) gets a larger block; smaller stat cards (avg. resolution time, language split) sit beside it

**Ticket replay view**
- Each of the 9 pipeline steps as its own rounded card with a small pill "View reasoning" button that expands the step's detail on click

---

### Motion — Specific, Not Vague
Framer Motion (UI) + react-three-fiber (the voice orb) + Lottie (micro-states), per the TRD.

**Page/section load**
Fade up + 16px translateY, staggered 60–80ms per child (eyebrow → headline → body → CTA). Easing `cubic-bezier(0.16, 1, 0.3, 1)` — fast-out, gentle-settle, the curve that makes a reveal feel premium rather than bouncy. Duration 500–600ms.

**Voice orb states**
- *Idle:* slow continuous breathing scale, 1.0 → 1.04 → 1.0 over 4s, `ease-in-out`, looping
- *Listening:* gradient turbulence amplitude driven frame-by-frame by live mic input volume — no fixed easing, it's audio-reactive
- *Thinking* (between STT and TTS): tighter, faster pulse (1.5s loop) plus a thin rotating ring — visually distinct from "listening"
- *Speaking:* orb pulses in sync with the outgoing TTS audio's amplitude envelope

**Status stream**
Each step: numeral color-shifts over 250ms `ease-out` the instant its stage starts; label opacity fades in 80ms behind the numeral (a deliberate stagger, not simultaneous). Completed steps get a quick checkmark draw-on (SVG `stroke-dashoffset`, 300ms).

**Buttons (every pill CTA, including record)**
- *Hover:* scale 1.0 → 1.02, background brightens one step, 150ms `ease-out` — brightness only, never a hue shift, so it never reads as a different button
- *Press:* scale to 0.98, 80ms — snappy, not springy
- *Recording (active state):* a soft outward-expanding `accent`-colored ring — radial scale 1 → 1.4, opacity 0.4 → 0, 1.2s loop — the same "radiating" language a live waveform would use

**Ticket list rows**
- *Hover:* background steps `bg-base` → `bg-panel`, 120ms, no movement — keeps a dense list calm
- *New ticket via WebSocket:* row slides in from above (translateY −12px → 0, opacity 0 → 1, 300ms `ease-out`) with a one-time `accent` left-border flash that fades over 1.5s — noticeable, never jarring

**Cards (analytics, escalation, replay)**
- *Hover:* lift 2px (translateY −2px) + border brightens `border-subtle` → lighter grey, 150ms — no shadow, consistent with the no-drop-shadow rule above

**What never animates**
No word-by-word or letter-by-letter text reveals (a common "AI slop" tell) — text blocks animate in as a single unit at most. No gradient text. No glassmorphism/blur panels. No rotating-3D-card-on-hover gimmicks. Every animation here exists to communicate *state* — loading, arriving, succeeding — never to decorate for its own sake.

---

### Mobile
Two-column block sections stack to single-column, same order as desktop (eyebrow → headline → supporting content). The voice orb and record button stay full-width-centered — this is the screen most customers will actually use on a phone, so it gets first-class treatment, not an afterthought breakpoint.

### Accessibility
- Verify `text-primary` on `bg-base` and `accent` text on `bg-base` against WCAG AA before lock — dark theme + single accent makes this easy to get wrong
- Status colors (priority/sentiment) are separated from the brand accent specifically so color-blind users still get distinguishable signal — pair every status color with a text label, never color alone
- All status-stream and orb animations must respect `prefers-reduced-motion`: fall back to instant state-changes, no stagger, no breathing loop