import type { ReactNode } from "react";

import { Panel } from "./Panel";

type Tone = "default" | "accent" | "danger";

type Props = {
  label: string;
  value: ReactNode;
  /** Small line under the value (trend, unit, hint). */
  hint?: ReactNode;
  /** Accent-tint the value (used for the number that matters most). */
  accent?: boolean;
  /** Semantic color for the value: accent = brand focus, danger = urgency. */
  tone?: Tone;
  /** Larger tile for the one or two numbers an operator checks first. */
  featured?: boolean;
};

const TONE_COLOR: Record<Tone, string> = {
  default: "var(--text-primary)",
  accent: "var(--accent)",
  danger: "var(--status-high)",
};

/** KPI tile: coral eyebrow label, large tabular number, optional hint. */
export function StatCard({ label, value, hint, accent = false, tone, featured = false }: Props) {
  const color = TONE_COLOR[tone ?? (accent ? "accent" : "default")];
  return (
    <Panel hover style={{ padding: featured ? "26px 28px" : "20px 22px" }}>
      <span className="eyebrow">{label}</span>
      <p
        style={{
          fontSize: featured ? 48 : 34,
          fontWeight: 800,
          lineHeight: 1,
          fontVariantNumeric: "tabular-nums",
          letterSpacing: "-0.02em",
          color,
        }}
      >
        {value}
      </p>
      {hint && (
        <p style={{ fontSize: featured ? 13 : 12, color: "var(--text-muted)", marginTop: featured ? 8 : 6 }}>
          {hint}
        </p>
      )}
    </Panel>
  );
}
