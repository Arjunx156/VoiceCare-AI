import type { ReactNode } from "react";

import { CountUp } from "./CountUp";
import { Panel } from "./Panel";

type Props = {
  label: string;
  /** Number → animated count-up; ReactNode → rendered as-is. */
  value: ReactNode | number;
  /** Appended to an animated numeric value (e.g. "%"). */
  suffix?: string;
  /** Decimal places for an animated numeric value. */
  decimals?: number;
  /** Small line under the value (trend, unit, hint). */
  hint?: ReactNode;
  /** Accent-tint the value (used for the number that matters most). */
  accent?: boolean;
};

/** KPI tile: coral eyebrow label, large tabular number (animated), optional hint. */
export function StatCard({ label, value, suffix, decimals = 0, hint, accent = false }: Props) {
  const isNumeric = typeof value === "number";
  return (
    <Panel elevated hover style={{ padding: "20px 22px" }}>
      <span className="eyebrow">{label}</span>
      <p
        className="display"
        style={{
          fontSize: 36,
          lineHeight: 1,
          color: accent ? "var(--accent)" : "var(--text-primary)",
        }}
      >
        {isNumeric ? (
          <CountUp value={value} decimals={decimals} suffix={suffix ?? ""} />
        ) : (
          value
        )}
      </p>
      {hint && <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>{hint}</p>}
    </Panel>
  );
}
