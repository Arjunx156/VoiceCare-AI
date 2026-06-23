# CommerceMind VoiceCare AI — UI/UX Design Brief
### Visual & Interaction Design Guide

Items neither source document actually specifies are marked 📌 — open decisions, not facts.

---

### Aesthetic
Production-grade and motion-rich — explicitly "clean, fully custom design, not generic defaults," built around an animated, audio-reactive voice orb as the centerpiece rather than a static form-based UI.

### Primary / Background / Text / Accent Color
📌 Not specified in either source — pick a palette before Week 2 (voice + visual layer), since the orb and status-stream animations will need it.

### Font
📌 Not specified — a clean sans-serif consistent with shadcn/ui defaults (e.g. Inter) is a reasonable starting point, but this is a suggestion, not a sourced requirement.

### Border Radius / Shadows
📌 Not specified — will likely follow shadcn/ui defaults given that's the component library in use, unless overridden.

### Dark / Light Mode
📌 Not specified.

### Reference Apps
📌 Not specified.

### Key UI Patterns (these *are* specified)
- An animated, audio-reactive "voice orb" (react-three-fiber/Canvas) as the central customer-facing element
- A live status stream during processing — Listening → Understanding → Checking your order → Finding the right policy → Responding — via Framer Motion + WebSockets
- Lottie micro-animations for loading/thinking/success states
- Dashboard analytics charts (Tremor/Recharts)
- Ticket list/detail views, an escalation queue, and a step-by-step ticket "replay" trace view

### Mobile
📌 Not explicitly addressed, but worth prioritizing on its own merits: people instinctively reach for their phone when they want to talk through a problem rather than type, so mobile responsiveness for the voice interface matters even though the source docs don't call it out directly.

### Accessibility
📌 Not explicitly addressed, but it's arguably baked into the product's whole premise — it exists specifically for customers less comfortable typing in English. Worth treating high-contrast visuals and clear, glanceable status feedback (for anyone following the status stream visually, not just by ear) as a priority.
