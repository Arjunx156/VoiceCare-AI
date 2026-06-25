"use client";

/**
 * CommerceMind VoiceCare AI — Escalations Page v2
 * Design brief: outlined panels for Low/Medium, raised card with corner badge for Critical/High.
 * Semantic colors only (never --accent for urgency).
 */

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { getEscalations, claimTicket, type TicketSummary } from "@/lib/api";

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

// "Raised" means Critical or High — needs attention now
function isRaised(priority: string) {
  return priority === "Critical" || priority === "High";
}

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<TicketSummary[]>([]);
  const [loading, setLoading]         = useState(true);
  const [claiming, setClaiming]       = useState<string | null>(null);

  const handleClaim = useCallback(async (ticketId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setClaiming(ticketId);
    try {
      await claimTicket(ticketId);
      setEscalations((prev) => prev.filter((t) => t.ticket_id !== ticketId));
    } catch (err) {
      console.error("Failed to claim ticket:", err);
    } finally {
      setClaiming(null);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    let controller = new AbortController();

    async function load() {
      controller = new AbortController();
      try {
        const data = await getEscalations(controller.signal);
        if (mounted) setEscalations(data);
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") return;
        console.error("Failed to load escalations:", err);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();

    // Poll every 5 seconds for real-time updates
    const intervalId = setInterval(load, 5000);

    return () => {
      mounted = false;
      clearInterval(intervalId);
      controller.abort();
    };
  }, []);

  if (loading && escalations.length === 0) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 256 }}>
        <div style={{
          width: 28, height: 28, borderRadius: "50%",
          border: "2px solid var(--border-subtle)", borderTopColor: "var(--accent)",
          animation: "spin 1s linear infinite",
        }} />
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="eyebrow">ESCALATION QUEUE</span>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>
          {escalations.length > 0
            ? `${escalations.length} ticket${escalations.length !== 1 ? "s" : ""} need${escalations.length === 1 ? "s" : ""} you`
            : "All clear"}
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 6 }}>
          Tickets that require human agent review
        </p>
      </motion.div>

      {escalations.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="panel"
          style={{ textAlign: "center", padding: "80px 0" }}
        >
          <p style={{ fontSize: 40, marginBottom: 12 }}>🎉</p>
          <p style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>No pending escalations</p>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 6 }}>
            All tickets are being handled by AI
          </p>
        </motion.div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 12 }}>
          {escalations.map((ticket, i) => {
            const raised = isRaised(ticket.priority);
            return (
              <motion.div
                key={ticket.ticket_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06, duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
              >
                <Link href={`/dashboard/tickets/${ticket.ticket_id}`} style={{ textDecoration: "none", display: "block" }}>
                  <div
                    className="panel-hover"
                    style={{
                      borderRadius: 18,
                      padding: "20px 22px",
                      position: "relative",
                      overflow: "hidden",
                      border: `1px solid ${raised ? PRIORITY_BG[ticket.priority] : "var(--border-subtle)"}`,
                      background: raised ? "var(--bg-panel-raised)" : "var(--bg-panel)",
                      cursor: "pointer",
                    }}
                  >
                    {/* Corner badge for raised cards */}
                    {raised && (
                      <div
                        style={{
                          position: "absolute",
                          top: 0, right: 0,
                          padding: "5px 12px",
                          borderRadius: "0 18px 0 12px",
                          fontSize: 10,
                          fontWeight: 700,
                          letterSpacing: "0.06em",
                          background: PRIORITY_BG[ticket.priority],
                          color: PRIORITY_COLOR[ticket.priority],
                          textTransform: "uppercase",
                        }}
                      >
                        {ticket.priority}
                      </div>
                    )}

                    {/* Eyebrow + name */}
                    <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--accent)", display: "block", marginBottom: 4 }}>
                      {ticket.ticket_type || "SUPPORT"}
                    </span>
                    <p style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>
                      {ticket.user_name}
                    </p>
                    <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                      {ticket.phone} · {ticket.language}
                    </p>

                    {/* Divider */}
                    <div className="divider" style={{ margin: "12px 0" }} />

                    {/* Summary */}
                    <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                      {ticket.summary || `${ticket.ticket_type} issue`}
                    </p>

                    {/* Footer */}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 14 }}>
                      <div style={{ display: "flex", gap: 8 }}>
                        {/* Priority pill — only shown if not raised (raised has corner badge) */}
                        {!raised && (
                          <span style={{
                            fontSize: 10, fontWeight: 600, padding: "3px 9px", borderRadius: 999,
                            background: PRIORITY_BG[ticket.priority] || "transparent",
                            color: PRIORITY_COLOR[ticket.priority] || "var(--text-secondary)",
                          }}>
                            {ticket.priority}
                          </span>
                        )}
                        {ticket.sentiment && (
                          <span style={{
                            fontSize: 10, fontWeight: 500, padding: "3px 9px", borderRadius: 999,
                            background: "rgba(96,125,139,0.12)",
                            color: "var(--status-calm)",
                          }}>
                            {ticket.sentiment}
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        {new Date(ticket.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                      </span>
                    </div>

                    {/* Claim button */}
                    <div style={{ marginTop: 12 }}>
                      {ticket.assigned_to ? (
                        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                          Claimed by {ticket.assigned_to}
                        </span>
                      ) : (
                        <button
                          onClick={(e) => handleClaim(ticket.ticket_id, e)}
                          disabled={claiming === ticket.ticket_id}
                          className="btn-pill"
                          style={{
                            fontSize: 11, padding: "5px 14px",
                            opacity: claiming === ticket.ticket_id ? 0.6 : 1,
                            cursor: claiming === ticket.ticket_id ? "not-allowed" : "pointer",
                          }}
                        >
                          {claiming === ticket.ticket_id ? "Claiming…" : "Claim"}
                        </button>
                      )}
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
