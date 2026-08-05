import type { ReactNode } from "react";

type Props = {
  label: string;
  value: ReactNode;
  /** Small line under the value (trend, unit, hint). */
  hint?: ReactNode;
  /** Accent-tint the value (used for the number that matters most). */
  accent?: boolean;
};

/**
 * One reading inside a {@link StatCluster}. Not a card — it carries no border
 * and no radius of its own; the cluster draws the hairlines between cells.
 * A row of separately-boxed KPI tiles is the stock dashboard shape, and it
 * gives six equal numbers six competing frames.
 */
export function StatCard({ label, value, hint, accent = false }: Props) {
  return (
    <div className="stat-cell">
      <span className="eyebrow">{label}</span>
      <p className="stat-value" style={accent ? { color: "var(--accent)" } : undefined}>
        {value}
      </p>
      {hint && (
        <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 7 }}>{hint}</p>
      )}
    </div>
  );
}

/** The bounded surface that joins a row of {@link StatCard} readings. */
export function StatCluster({ children }: { children: ReactNode }) {
  return <div className="stat-cluster">{children}</div>;
}
