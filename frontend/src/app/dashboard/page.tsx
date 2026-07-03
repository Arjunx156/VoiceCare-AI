"use client";

/**
 * Dashboard overview — asymmetric two-column analytics, eyebrow labels,
 * editorial escalation list-rows.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getAnalytics, getEscalations, type AnalyticsOverview, type TicketSummary } from "@/lib/api";
import { chartTooltipStyle } from "@/lib/theme";
import { useMotionSafe } from "@/lib/motion";
import { Button, EmptyState, LanguageLabel, PriorityBadge, StatCard } from "@/components/ui";

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
    // Skeleton mirrors the real layout (header → featured pair → stat row)
    // so content doesn't jump when data lands.
    const bar = (w: number | string, h: number, mb = 0): React.CSSProperties => ({
      display: "block", width: w, height: h, marginBottom: mb,
    });
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 32 }} role="status" aria-label="Loading dashboard">
        <div>
          <span className="skeleton" style={bar(90, 10, 12)} />
          <span className="skeleton" style={bar(280, 26)} />
        </div>
        <div className="grid-half">
          {[0, 1].map((i) => (
            <div key={i} className="panel" style={{ padding: "26px 28px" }}>
              <span className="skeleton" style={bar(80, 9, 14)} />
              <span className="skeleton" style={bar(120, 40)} />
            </div>
          ))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 12 }}>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="panel" style={{ padding: "20px 22px" }}>
              <span className="skeleton" style={bar(70, 8, 12)} />
              <span className="skeleton" style={bar(60, 28)} />
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

  const escalatedCount = analytics.escalated_tickets || 0;

  // The two numbers an operator checks first, at featured size; the rest compact.
  const compactStats = [
    { label: "TOTAL",      value: total,                                hint: "all time" },
    { label: "RESOLVED",   value: analytics.resolved_tickets || 0,      hint: "closed" },
    { label: "RESOLUTION", value: `${analytics.resolution_rate || 0}%`, hint: "resolution rate" },
    { label: "ESCALATION", value: `${analytics.escalation_rate || 0}%`, hint: "escalation rate" },
  ];

  const trend = analytics.tickets_over_time || [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      {/* Page header */}
      <motion.div {...entry()}>
        <span className="eyebrow">OVERVIEW</span>
        <h1 className="page-title">Support Operations</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 6 }}>
          Live view of {process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI"} customer support activity
        </p>
      </motion.div>

      {/* Featured pair — what needs attention right now */}
      <div className="grid-half">
        <motion.div {...entry(0.05)}>
          <StatCard
            featured
            label="OPEN NOW"
            value={analytics.open_tickets || 0}
            hint="awaiting resolution"
          />
        </motion.div>
        <motion.div {...entry(0.1)}>
          <StatCard
            featured
            label="ESCALATED"
            value={escalatedCount}
            tone={escalatedCount > 0 ? "danger" : "default"}
            hint={escalatedCount > 0 ? "need a human now" : "queue is clear"}
          />
        </motion.div>
      </div>

      {/* Compact stat row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 12 }}>
        {compactStats.map((s, i) => (
          <motion.div key={s.label} {...entry(0.15 + i * 0.05)}>
            <StatCard {...s} />
          </motion.div>
        ))}
      </div>

      {/* Ticket volume trend — the pipeline's heartbeat over time */}
      {trend.length > 1 && (
        <motion.div {...entry(0.3)} className="panel" style={{ padding: "24px 28px 10px" }}>
          <span className="eyebrow">VOLUME</span>
          <h2 className="section-title" style={{ marginBottom: 16 }}>
            Tickets Over Time
          </h2>
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
        <motion.div {...entry(0.36)} className="panel" style={{ padding: "24px 28px" }}>
          <span className="eyebrow">TICKET VOLUME</span>
          <h2 className="section-title" style={{ marginBottom: 20 }}>
            By Language
          </h2>
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
        <motion.div {...entry(0.42)} className="panel" style={{ padding: "24px 22px" }}>
          <span className="eyebrow">BY CATEGORY</span>
          <h2 className="section-title" style={{ marginBottom: 20 }}>
            Ticket Types
          </h2>
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
      <motion.div {...entry(0.5)} className="panel" style={{ padding: "24px 28px" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 20 }}>
          <span className="eyebrow" style={{ marginBottom: 0 }}>ESCALATION QUEUE</span>
          {escalations.length > 0 && (
            <span style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
              {escalations.length} ticket{escalations.length !== 1 ? "s" : ""} need{escalations.length === 1 ? "s" : ""} you
            </span>
          )}
        </div>

        {escalations.length > 0 ? (
          <div>
            {escalations.slice(0, 6).map((ticket, i) => (
              <Link key={ticket.ticket_id} href={`/dashboard/tickets/${ticket.ticket_id}`} style={{ textDecoration: "none" }}>
                <motion.div
                  {...entry(0.55 + i * 0.05)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 16,
                    padding: "14px 0",
                    borderBottom: i < Math.min(escalations.length, 6) - 1 ? "1px solid var(--border-subtle)" : "none",
                    cursor: "pointer",
                  }}
                  className="panel-hover"
                >
                  {/* Eyebrow + title */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--accent)", display: "block", marginBottom: 2 }}>
                      {ticket.ticket_type || "SUPPORT"}
                    </span>
                    <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {ticket.user_name}
                    </p>
                    {ticket.summary && (
                      <p style={{ fontSize: 12, color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {ticket.summary}
                      </p>
                    )}
                  </div>

                  <PriorityBadge priority={ticket.priority} />
                </motion.div>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState icon={CheckCircle2} title="No pending escalations" hint="The AI is handling everything right now." />
        )}
      </motion.div>
    </div>
  );
}
