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
  Angry:        meta("var(--status-angry)",  "rgba(229,57,53,0.12)"),
  "Very Angry": meta("var(--status-critical)", "rgba(198,40,40,0.12)"),
};

export function priorityMeta(priority: string | null | undefined): BadgeMeta {
  return (priority && PRIORITY_META[priority]) || FALLBACK;
}

export function statusMeta(status: string | null | undefined): BadgeMeta {
  return (status && STATUS_META[status]) || FALLBACK;
}

export function sentimentMeta(sentiment: string | null | undefined): BadgeMeta {
  return (sentiment && SENTIMENT_META[sentiment]) || FALLBACK;
}

/** Categorical palette for charts (accent-led, then semantic hues). */
export const CHART_COLORS = [
  "#FF5A2B", "#D4A017", "#4CAF73", "#607D8B",
  "#E53935", "#8D6E63", "#42A5F5", "#AB47BC",
] as const;

/** Recharts hex values for priority bars (Recharts can't resolve CSS vars). */
export const PRIORITY_HEX: Record<string, string> = {
  Critical: "#C62828",
  High:     "#E53935",
  Medium:   "#D4A017",
  Low:      "#4CAF73",
};

export function sentimentHex(name: string): string {
  if (name === "Angry" || name === "Very Angry") return "#E53935";
  if (name === "Negative") return "#D4A017";
  if (name === "Calm" || name === "Confused" || name === "Neutral") return "#607D8B";
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
