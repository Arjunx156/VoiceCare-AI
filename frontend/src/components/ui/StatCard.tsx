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

/** KPI tile: uppercase label, large tabular number, optional hint. */
export function StatCard({ label, value, hint, accent = false }: Props) {
  return (
    <Panel style={{ padding: "20px 22px" }}>
      <p
        style={{
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--text-muted)",
          marginBottom: 8,
        }}
      >
        {label}
      </p>
      <p
        style={{
          fontSize: 30,
          fontWeight: 800,
          lineHeight: 1,
          color: accent ? "var(--accent)" : "var(--text-primary)",
        }}
      >
        {value}
      </p>
      {hint && (
        <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>{hint}</p>
      )}
    </Panel>
  );
}
