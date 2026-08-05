"use client";

/**
 * Dashboard overview — one stat cluster, ruled section heads, and an
 * escalation queue drawn as list rows rather than cards.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getAnalytics, getEscalations, type AnalyticsOverview, type TicketSummary } from "@/lib/api";
import { chartTooltipStyle } from "@/lib/theme";
import { useMotionSafe } from "@/lib/motion";
import { Button, EmptyState, LanguageLabel, PriorityBadge, StatCard, StatCluster } from "@/components/ui";

type FetchResult =
  | { key: number; analytics: AnalyticsOverview; escalations: TicketSummary[] }
  | { key: number; error: string };

export default function DashboardPage() {
  const [retryCount, setRetryCount] = useState(0);
  const [result, setResult] = useState<FetchResult | null>(null);
  const { entry } = useMotionSafe();

  useEffect(() => {
    let cancelled = false;
    Promise.all([getAnalytics(), getEscalations()])
      .then(([analytics, escalations]) => {
        if (!cancelled) setResult({ key: retryCount, analytics, escalations });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setResult({
            key: retryCount,
            error: err instanceof Error ? err.message : "Failed to load dashboard data",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [retryCount]);

  const current = result?.key === retryCount ? result : null;

  if (!current) {
    // Skeleton mirrors the real layout (header → uniform stat row) so
    // content doesn't jump when data lands.
    const bar = (w: number | string, h: number, mb = 0): React.CSSProperties => ({
      display: "block", width: w, height: h, marginBottom: mb,
    });
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 32 }} role="status" aria-label="Loading dashboard">
        <div>
          <span className="skeleton" style={bar(90, 10, 12)} />
          <span className="skeleton" style={bar(280, 26)} />
        </div>
        <div className="stat-cluster">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="stat-cell">
              <span className="skeleton" style={bar(64, 8, 14)} />
              <span className="skeleton" style={bar(56, 26)} />
            </div>
          ))}
        </div>
        <span className="sr-only">Loading dashboard</span>
      </div>
    );
  }

  if ("error" in current) {
    return (
      <div
        style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", height: "100%", gap: 12,
        }}
      >
        <p style={{ fontSize: 14, fontWeight: 600, color: "var(--error)" }}>Unable to load dashboard</p>
        <p style={{ fontSize: 12, color: "var(--text-muted)", maxWidth: 300, textAlign: "center" }}>{current.error}</p>
        <Button size="sm" onClick={() => setRetryCount((c) => c + 1)}>
          Retry
        </Button>
      </div>
    );
  }

  const { analytics, escalations } = current;
  const total = analytics.total_tickets || 0;

  const fmt = (n: number) => (n || 0).toLocaleString();

  const stats = [
    { label: "TOTAL",      value: fmt(total),                       hint: "all time" },
    { label: "OPEN",       value: fmt(analytics.open_tickets),      hint: "awaiting resolution" },
    { label: "ESCALATED",  value: fmt(analytics.escalated_tickets), hint: "needs human" },
    { label: "RESOLVED",   value: fmt(analytics.resolved_tickets),  hint: "closed" },
    { label: "RESOLUTION", value: `${analytics.resolution_rate || 0}%`, hint: "resolution rate" },
    { label: "ESCALATION", value: `${analytics.escalation_rate || 0}%`, hint: "escalation rate" },
  ];

  const trend = analytics.tickets_over_time || [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      {/* Page header. The eyebrow carries the record count rather than the
          word "OVERVIEW" — a label that repeats the heading below it is
          decoration, and this slot can hold something true instead. */}
      <motion.div {...entry()}>
        <span className="eyebrow">
          {total.toLocaleString()} tickets on record
        </span>
        <h1 className="page-title">Support operations</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 10, maxWidth: "58ch" }}>
          Everything the voice pipeline has handled, and everything it has handed back to you.
        </p>
      </motion.div>

      {/* Six readings, one instrument. Animated as a single unit — a
          per-tile stagger across six equal numbers implies an order that
          isn't there. */}
      <motion.div {...entry(0.06)}>
        <StatCluster>
          {stats.map((s) => (
            <StatCard key={s.label} {...s} />
          ))}
        </StatCluster>
      </motion.div>

      {/* Ticket volume trend — the pipeline's heartbeat over time */}
      {trend.length > 1 && (
        <motion.div {...entry(0.12)} className="panel" style={{ padding: "22px 26px 8px" }}>
          <div className="rule-head">
            <h2 className="section-title">Tickets over time</h2>
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <AreaChart data={trend} margin={{ left: -24, right: 4, top: 4 }}>
              <defs>
                <linearGradient id="volumeFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#FF5A2B" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#FF5A2B" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                tick={{ fill: "#8A8A8A", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: "#8A8A8A", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
                width={32}
              />
              <Tooltip {...chartTooltipStyle} />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#FF5A2B"
                strokeWidth={2}
                fill="url(#volumeFill)"
                dot={false}
                activeDot={{ r: 3, fill: "#FF5A2B", strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Asymmetric two-column: large chart block + smaller stat cards
          (collapses to one column under 900px — .grid-main-side) */}
      <div className="grid-main-side">
        {/* Ticket volume by language — the larger block */}
        <motion.div {...entry(0.16)} className="panel" style={{ padding: "22px 26px" }}>
          <div className="rule-head">
            <h2 className="section-title">Volume by language</h2>
          </div>
          {Object.entries(analytics.tickets_by_language).length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {Object.entries(analytics.tickets_by_language)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .map(([lang, count]) => (
                  <div key={lang} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span style={{ fontSize: 13, color: "var(--text-secondary)", width: 88, flexShrink: 0 }}>
                      <LanguageLabel language={lang} />
                    </span>
                    <div
                      aria-hidden="true"
                      style={{
                        flex: 1, height: 6, borderRadius: 999,
                        background: "var(--border-subtle)",
                        overflow: "hidden",
                      }}
                    >
                      <motion.div
                        style={{
                          height: "100%", borderRadius: 999,
                          background: "var(--accent)",
                          transformOrigin: "left",
                        }}
                        initial={{ scaleX: 0 }}
                        animate={{ scaleX: (count as number) / (total || 1) }}
                        transition={{ duration: 0.8, ease: "easeOut", delay: 0.5 }}
                      />
                    </div>
                    <span
                      style={{
                        fontSize: 13, fontWeight: 700,
                        color: "var(--text-primary)",
                        width: 28, textAlign: "right",
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {count as number}
                    </span>
                  </div>
                ))}
            </div>
          ) : (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No data yet</p>
          )}
        </motion.div>

        {/* Right column: category breakdown */}
        <motion.div {...entry(0.16)} className="panel" style={{ padding: "22px 24px" }}>
          <div className="rule-head">
            <h2 className="section-title">Ticket types</h2>
          </div>
          {Object.entries(analytics.tickets_by_category).length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {Object.entries(analytics.tickets_by_category).map(([cat, count]) => (
                <div
                  key={cat}
                  style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
                >
                  <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                    {cat.replace(/_/g, " ")}
                  </span>
                  <span
                    style={{
                      fontSize: 13, fontWeight: 700,
                      color: "var(--text-primary)",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {count as number}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No data yet</p>
          )}
        </motion.div>
      </div>

      {/* Escalation Queue — editorial list rows */}
      <motion.div {...entry(0.22)} className="panel" style={{ padding: "22px 26px" }}>
        <div className="rule-head">
          <h2 className="section-title">Escalation queue</h2>
          {escalations.length > 0 && (
            <span
              className="eyebrow rule-tail"
              style={{ color: "var(--text-secondary)" }}
            >
              {escalations.length} waiting on you
            </span>
          )}
        </div>

        {escalations.length > 0 ? (
          /* Rows bleed to the panel edge (negative margin + matching padding)
             so the hover highlight covers a full band instead of a floating
             inset strip. Rows brighten and grow an edge marker; they never
             lift — a row is part of a continuous surface. */
          <div style={{ margin: "0 -26px" }}>
            {escalations.slice(0, 6).map((ticket, i) => (
              <Link
                key={ticket.ticket_id}
                href={`/dashboard/tickets/${ticket.ticket_id}`}
                className="row-hover"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  padding: "13px 26px",
                  textDecoration: "none",
                  borderBottom:
                    i < Math.min(escalations.length, 6) - 1
                      ? "1px solid var(--border-hairline)"
                      : "none",
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <span className="eyebrow" style={{ marginBottom: 4 }}>
                    {ticket.ticket_type || "support"}
                  </span>
                  <p style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {ticket.user_name}
                  </p>
                  {ticket.summary && (
                    <p style={{ fontSize: 12, color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", marginTop: 2 }}>
                      {ticket.summary}
                    </p>
                  )}
                </div>

                <PriorityBadge priority={ticket.priority} />
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState icon={CheckCircle2} title="No pending escalations" hint="The pipeline is resolving everything on its own right now." />
        )}
      </motion.div>
    </div>
  );
}
