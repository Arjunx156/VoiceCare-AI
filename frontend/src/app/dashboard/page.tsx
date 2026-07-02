"use client";

/**
 * Dashboard overview — asymmetric two-column analytics, eyebrow labels,
 * editorial escalation list-rows.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import { getAnalytics, getEscalations, type AnalyticsOverview, type TicketSummary } from "@/lib/api";
import { useMotionSafe } from "@/lib/motion";
import { Button, EmptyState, LoadingBlock, PriorityBadge, StatCard } from "@/components/ui";

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
    return <LoadingBlock label="Loading dashboard" />;
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

  const stats = [
    { label: "TOTAL",      value: total,                            hint: "all time" },
    { label: "OPEN",       value: analytics.open_tickets || 0,      hint: "awaiting resolution" },
    { label: "ESCALATED",  value: analytics.escalated_tickets || 0, hint: "needs human" },
    { label: "RESOLVED",   value: analytics.resolved_tickets || 0,  hint: "closed" },
    { label: "RESOLUTION", value: analytics.resolution_rate || 0, suffix: "%", hint: "resolution rate", accent: true },
    { label: "ESCALATION", value: analytics.escalation_rate || 0, suffix: "%", hint: "escalation rate" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      {/* Page header */}
      <motion.div {...entry()}>
        <span className="eyebrow">OVERVIEW</span>
        <h1 className="display-h1" style={{ color: "var(--text-primary)" }}>
          Support Operations
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 6 }}>
          Live view of {process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI"} customer support activity
        </p>
      </motion.div>

      {/* Stats — 4 primary + 2 rate */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 12 }}>
        {stats.map((s, i) => (
          <motion.div key={s.label} {...entry(i * 0.06)}>
            <StatCard {...s} />
          </motion.div>
        ))}
      </div>

      {/* Asymmetric two-column: large chart block + smaller stat cards */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
        {/* Ticket volume by language — the larger block */}
        <motion.div {...entry(0.36)} className="panel-elevated" style={{ padding: "24px 28px" }}>
          <span className="eyebrow">TICKET VOLUME</span>
          <h2 className="display-h2" style={{ color: "var(--text-primary)", marginBottom: 20 }}>
            By Language
          </h2>
          {Object.entries(analytics.tickets_by_language).length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {Object.entries(analytics.tickets_by_language)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .map(([lang, count]) => (
                  <div key={lang} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span style={{ fontSize: 13, color: "var(--text-secondary)", width: 80, flexShrink: 0 }}>
                      {lang}
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
        <motion.div {...entry(0.42)} className="panel-elevated" style={{ padding: "24px 22px" }}>
          <span className="eyebrow">BY CATEGORY</span>
          <h2 className="display-h2" style={{ color: "var(--text-primary)", marginBottom: 20 }}>
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
      <motion.div {...entry(0.5)} className="panel-elevated" style={{ padding: "24px 28px" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 20 }}>
          <span className="eyebrow" style={{ marginBottom: 0 }}>ESCALATION QUEUE</span>
          {escalations.length > 0 && (
            <span className="display" style={{ fontSize: 24, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
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
