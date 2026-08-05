/**
 * Single source of truth for status / priority / sentiment presentation.
 * Replaces the PRIORITY_COLOR / STATUS_COLOR / sentColor copies that were
 * duplicated (with divergent key sets) across the dashboard pages.
 *
 * Colors reference the CSS custom properties defined in globals.css so the
 * palette stays locked in one place.
 */

export interface BadgeMeta {
  /** Text + dot color */
  fg: string;
  /** Pill background (low-alpha tint of fg) */
  bg: string;
}

const meta = (fg: string, bg: string): BadgeMeta => ({ fg, bg });

const FALLBACK: BadgeMeta = meta("var(--text-secondary)", "rgba(154,154,154,0.10)");

export const PRIORITY_META: Record<string, BadgeMeta> = {
  Critical: meta("var(--status-critical)", "rgba(198,40,40,0.12)"),
  High:     meta("var(--status-high)",     "rgba(229,57,53,0.12)"),
  Medium:   meta("var(--status-medium)",   "rgba(212,160,23,0.12)"),
  Low:      meta("var(--status-low)",      "rgba(76,175,115,0.12)"),
};

export const STATUS_META: Record<string, BadgeMeta> = {
  Open:          meta("var(--status-calm)",   "rgba(96,125,139,0.12)"),
  "In Progress": meta("var(--status-medium)", "rgba(212,160,23,0.12)"),
  Resolved:      meta("var(--status-low)",    "rgba(76,175,115,0.12)"),
  Escalated:     meta("var(--status-high)",   "rgba(229,57,53,0.12)"),
  Closed:        meta("var(--text-muted)",    "rgba(138,138,138,0.12)"),
};

export const SENTIMENT_META: Record<string, BadgeMeta> = {
  Positive:     meta("var(--status-low)",    "rgba(76,175,115,0.12)"),
  Neutral:      meta("var(--status-calm)",   "rgba(96,125,139,0.12)"),
  Calm:         meta("var(--status-calm)",   "rgba(96,125,139,0.12)"),
  Confused:     meta("var(--status-calm)",   "rgba(96,125,139,0.12)"),
  Negative:     meta("var(--status-medium)", "rgba(212,160,23,0.12)"),
  Dissatisfied: meta("var(--status-medium)", "rgba(212,160,23,0.12)"),
  Angry:        meta("var(--status-angry)",  "rgba(229,57,53,0.12)"),
  "Very Angry": meta("var(--status-critical)", "rgba(198,40,40,0.12)"),
  "High-risk Escalation": meta("var(--status-critical)", "rgba(198,40,40,0.12)"),
};

/**
 * Look a value up regardless of the casing the API sent it in. The maps are
 * keyed in Title Case; a lowercase "critical" used to fall through to the grey
 * FALLBACK, which silently discards the meaning the colour carries.
 */
function lookup(map: Record<string, BadgeMeta>, key: string | null | undefined): BadgeMeta {
  if (!key) return FALLBACK;
  if (map[key]) return map[key];
  const wanted = key.toLowerCase();
  const found = Object.keys(map).find((k) => k.toLowerCase() === wanted);
  return found ? map[found] : FALLBACK;
}

export function priorityMeta(priority: string | null | undefined): BadgeMeta {
  return lookup(PRIORITY_META, priority);
}

export function statusMeta(status: string | null | undefined): BadgeMeta {
  return lookup(STATUS_META, status);
}

export function sentimentMeta(sentiment: string | null | undefined): BadgeMeta {
  return lookup(SENTIMENT_META, sentiment);
}

/**
 * Chart ramp for breakdowns whose slices carry no meaning of their own —
 * ticket categories, for instance. A rainbow of unrelated hues implies each
 * slice means something different and quietly reintroduces the colours the
 * design system spent effort removing. This is one hue stepped through
 * lightness instead, so size is the only thing the colour encodes. Sort the
 * data by value before applying it and the ramp reads as a scale.
 *
 * Semantic dimensions (priority, sentiment, status) do NOT use this — they use
 * PRIORITY_HEX / sentimentHex, where the hue is the meaning.
 */
export const CHART_COLORS = [
  "#FFB59A", "#FF9375", "#FF7551", "#FF5A2B",
  "#D9481F", "#A93916", "#7C2A11", "#571C0C",
] as const;

/** Recharts hex values for priority bars (Recharts can't resolve CSS vars). */
export const PRIORITY_HEX: Record<string, string> = {
  Critical: "#C62828",
  High:     "#E53935",
  Medium:   "#D4A017",
  Low:      "#4CAF73",
};

export function priorityHex(name: string): string {
  const found = Object.keys(PRIORITY_HEX).find((k) => k.toLowerCase() === name.toLowerCase());
  return found ? PRIORITY_HEX[found] : "#8A8A8A";
}

export function sentimentHex(name: string): string {
  const n = name.toLowerCase();
  if (n === "angry" || n === "very angry") return "#E53935";
  if (n === "frustrated" || n === "negative" || n === "dissatisfied") return "#D4A017";
  if (n === "calm" || n === "confused" || n === "neutral") return "#607D8B";
  return "#4CAF73";
}

/** Shared Recharts tooltip styling (dark panel, subtle border). */
export const chartTooltipStyle = {
  contentStyle: {
    background: "#161616",
    border: "1px solid #262626",
    borderRadius: 10,
    color: "#F5F5F5",
    fontSize: 12,
  },
  cursor: { fill: "rgba(255,255,255,0.04)" },
} as const;

/**
 * Legend labels stay neutral. Recharts tints each label with its series colour
 * by default, which puts small coloured text on a dark panel — poor contrast,
 * and it makes the legend compete with the chart it is explaining. The swatch
 * carries the colour; the word stays readable.
 */
export const chartLegendStyle = {
  wrapperStyle: { fontSize: 10, paddingTop: 10 },
  iconSize: 8,
  iconType: "square",
} as const;

/** Neutral text colour for legend labels — pair with `formatter` in the page. */
export const CHART_LABEL_COLOR = "#9A9A9A";
