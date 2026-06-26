"use client";

/**
 * CommerceMind VoiceCare AI — Dashboard Overview v2
 * Design brief: asymmetric two-column analytics, eyebrow labels,
 * editorial escalation list-rows, no glassmorphism.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { getAnalytics, getEscalations, type AnalyticsOverview, type TicketSummary } from "@/lib/api";

// Priority semantic colors (never --accent)
const PRIORITY_COLOR: Record<string, string> = {
  Critical: "var(--status-critical)",
  High:     "var(--status-high)",
  Medium:   "var(--status-medium)",
  Low:      "var(--status-low)",
};
const PRIORITY_BG: Record<string, string> = {
  Critical: "rgba(198,40,40,0.12)",
  High:     "rgba(229,57,53,0.12)",
  Medium:   "rgba(212,160,23,0.12)",
  Low:      "rgba(76,175,115,0.12)",
};

function StatCard({ eyebrow, value, sub }: { eyebrow: string; value: string | number; sub?: string }) {
  return (
    <div
      className="panel panel-hover"
      style={{ padding: "20px 22px" }}
    >
      <span className="eyebrow">{eyebrow}</span>
      <p
        style={{
          fontSize: 36,
          fontWeight: 800,
          color: "var(--text-primary)",
          lineHeight: 1,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </p>
      {sub && (
        <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>{sub}</p>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const [analytics, setAnalytics]     = useState<AnalyticsOverview | null>(null);
  const [escalations, setEscalations] = useState<TicketSummary[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);
  const [retryCount, setRetryCount]   = useState(0);

  useEffect(() => {
    setLoading(true);
    setError(null);
    async function load() {
      try {
        const [a, e] = await Promise.all([getAnalytics(), getEscalations()]);
        setAnalytics(a);
        setEscalations(e);
      } catch (err) {
        console.error("Dashboard load failed:", err);
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [retryCount]);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
        <div
          style={{
            width: 28, height: 28, borderRadius: "50%",
            border: "2px solid var(--border-subtle)",
            borderTopColor: "var(--accent)",
            animation: "spin 1s linear infinite",
          }}
        />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", height: "100%", gap: 12,
        }}
      >
        <p style={{ fontSize: 14, fontWeight: 600, color: "var(--error)" }}>Unable to load dashboard</p>
        <p style={{ fontSize: 12, color: "var(--text-muted)", maxWidth: 300, textAlign: "center" }}>{error}</p>
        <button
          onClick={() => setRetryCount(c => c + 1)}
          className="btn-pill btn-pill-accent"
          style={{ padding: "8px 20px", fontSize: 13 }}
        >
          Retry
        </button>
      </div>
    );
  }

  const total    = analytics?.total_tickets || 0;
  const open     = analytics?.open_tickets || 0;
  const escalated= analytics?.escalated_tickets || 0;
  const resolved = analytics?.resolved_tickets || 0;
  const resRate  = analytics?.resolution_rate || 0;
  const escRate  = analytics?.escalation_rate || 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="eyebrow">OVERVIEW</span>
        <h1 style={{ fontSize: 32, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>
          Support Operations
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 6 }}>
          Live view of {process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI"} customer support activity
        </p>
      </motion.div>

      {/* Stats — 4 primary + 2 rate */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 12 }}>
        {[
          { eyebrow: "TOTAL",      value: total,               sub: "all time" },
          { eyebrow: "OPEN",       value: open,                sub: "awaiting resolution" },
          { eyebrow: "ESCALATED",  value: escalated,           sub: "needs human" },
          { eyebrow: "RESOLVED",   value: resolved,            sub: "closed" },
          { eyebrow: "RESOLUTION", value: `${resRate}%`,       sub: "resolution rate" },
          { eyebrow: "ESCALATION", value: `${escRate}%`,       sub: "escalation rate" },
        ].map((s, i) => (
          <motion.div
            key={s.eyebrow}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          >
            <StatCard {...s} />
          </motion.div>
        ))}
      </div>

      {/* Asymmetric two-column: large chart block + smaller stat cards */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>

        {/* Ticket volume by language — the larger block */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.36, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="panel"
          style={{ padding: "24px 28px" }}
        >
          <span className="eyebrow">TICKET VOLUME</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 20 }}>
            By Language
          </h2>
          {analytics && Object.entries(analytics.tickets_by_language).length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {Object.entries(analytics.tickets_by_language)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .map(([lang, count]) => (
                  <div key={lang} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span style={{ fontSize: 13, color: "var(--text-secondary)", width: 80, flexShrink: 0 }}>
                      {lang}
                    </span>
                    <div
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
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.42, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="panel"
          style={{ padding: "24px 22px" }}
        >
          <span className="eyebrow">BY CATEGORY</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 20 }}>
            Ticket Types
          </h2>
          {analytics && Object.entries(analytics.tickets_by_category).length > 0 ? (
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
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="panel"
        style={{ padding: "24px 28px" }}
      >
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
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.55 + i * 0.05 }}
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

                  {/* Priority tag */}
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: "4px 10px",
                      borderRadius: 999,
                      background: PRIORITY_BG[ticket.priority] || "transparent",
                      color: PRIORITY_COLOR[ticket.priority] || "var(--text-secondary)",
                      flexShrink: 0,
                    }}
                  >
                    {ticket.priority}
                  </span>
                </motion.div>
              </Link>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "32px 0" }}>
            <p style={{ fontSize: 32, marginBottom: 8 }}>🎉</p>
            <p style={{ fontSize: 14, color: "var(--text-muted)" }}>No pending escalations</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
