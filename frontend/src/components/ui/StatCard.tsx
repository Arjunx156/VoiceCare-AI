import type { ReactNode } from "react";

import { Panel } from "./Panel";

type Props = {
  label: string;
  value: ReactNode;
  /** Small line under the value (trend, unit, hint). */
  hint?: ReactNode;
  /** Accent-tint the value (used for the number that matters most). */
  accent?: boolean;
};

/** KPI tile: coral eyebrow label, large tabular number, optional hint. */
export function StatCard({ label, value, hint, accent = false }: Props) {
  return (
    <Panel hover style={{ padding: "20px 22px" }}>
      <span className="eyebrow">{label}</span>
      <p
        style={{
          fontSize: 34,
          fontWeight: 800,
          lineHeight: 1,
          fontVariantNumeric: "tabular-nums",
          letterSpacing: "-0.02em",
          color: accent ? "var(--accent)" : "var(--text-primary)",
        }}
      >
        {value}
      </p>
      {hint && (
        <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>{hint}</p>
      )}
    </Panel>
  );
}
