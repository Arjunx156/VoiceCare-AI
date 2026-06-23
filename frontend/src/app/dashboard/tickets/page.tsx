"use client";

/**
 * CommerceMind VoiceCare AI — Tickets List v2
 * Design brief: editorial list-row pattern — eyebrow (ticket type) above bold
 * title, thin border-subtle divider between rows, pill status on right.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { getTickets, type TicketSummary } from "@/lib/api";

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

const STATUS_COLOR: Record<string, string> = {
  Open:        "#607D8B",
  "In Progress": "var(--status-medium)",
  Resolved:    "var(--status-low)",
  Escalated:   "var(--status-high)",
  Closed:      "var(--text-muted)",
};
const STATUS_BG: Record<string, string> = {
  Open:        "rgba(96,125,139,0.12)",
  "In Progress": "rgba(212,160,23,0.12)",
  Resolved:    "rgba(76,175,115,0.12)",
  Escalated:   "rgba(229,57,53,0.12)",
  Closed:      "rgba(90,90,90,0.12)",
};

const FILTER_OPTIONS = {
  status:   ["", "Open", "In Progress", "Escalated", "Resolved", "Closed"],
  priority: ["", "Critical", "High", "Medium", "Low"],
};

const selectStyle: React.CSSProperties = {
  padding: "8px 14px",
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 500,
  fontFamily: "var(--font-sans)",
  outline: "none",
  background: "var(--bg-panel)",
  border: "1px solid var(--border-subtle)",
  color: "var(--text-secondary)",
  cursor: "pointer",
  appearance: "none",
  WebkitAppearance: "none",
};

export default function TicketsPage() {
  const [tickets, setTickets] = useState<TicketSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter]   = useState({ status: "", priority: "" });

  useEffect(() => {
    async function load() {
      try {
        const data = await getTickets({
          status:   filter.status   || undefined,
          priority: filter.priority || undefined,
        });
        setTickets(data);
      } catch (err) {
        console.error("Failed to load tickets:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filter]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}
      >
        <div>
          <span className="eyebrow">SUPPORT TICKETS</span>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>
            {loading ? "Loading…" : `${tickets.length} ticket${tickets.length !== 1 ? "s" : ""}`}
          </h1>
        </div>

        {/* Filter pills */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <select
            value={filter.status}
            onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}
            style={selectStyle}
          >
            {FILTER_OPTIONS.status.map((s) => (
              <option key={s} value={s}>{s || "All Status"}</option>
            ))}
          </select>
          <select
            value={filter.priority}
            onChange={(e) => setFilter((f) => ({ ...f, priority: e.target.value }))}
            style={selectStyle}
          >
            {FILTER_OPTIONS.priority.map((p) => (
              <option key={p} value={p}>{p || "All Priority"}</option>
            ))}
          </select>
        </div>
      </motion.div>

      {/* Ticket list — editorial list-row pattern */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="panel"
        style={{ overflow: "hidden" }}
      >
        {loading ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "64px 0" }}>
            <div
              style={{
                width: 24, height: 24, borderRadius: "50%",
                border: "2px solid var(--border-subtle)",
                borderTopColor: "var(--accent)",
                animation: "spin 1s linear infinite",
              }}
            />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          </div>
        ) : tickets.length === 0 ? (
          <div style={{ textAlign: "center", padding: "64px 0" }}>
            <p style={{ fontSize: 32, marginBottom: 8 }}>📭</p>
            <p style={{ fontSize: 14, color: "var(--text-muted)" }}>No tickets found</p>
          </div>
        ) : (
          tickets.map((ticket, i) => (
            <Link
              key={ticket.ticket_id}
              href={`/dashboard/tickets/${ticket.ticket_id}`}
              style={{ textDecoration: "none", display: "block" }}
            >
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03, duration: 0.35, ease: "easeOut" }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  padding: "16px 24px",
                  borderBottom: i < tickets.length - 1 ? "1px solid var(--border-subtle)" : "none",
                  cursor: "pointer",
                  transition: "background 120ms",
                }}
                whileHover={{ backgroundColor: "var(--bg-panel-raised)" }}
              >
                {/* Left: eyebrow + bold title */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Eyebrow: ticket type */}
                  <span
                    style={{
                      fontSize: 10, fontWeight: 600,
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                      color: "var(--accent)",
                      display: "block",
                      marginBottom: 2,
                    }}
                  >
                    {ticket.ticket_type || "SUPPORT"}
                  </span>
                  {/* Bold title: customer name */}
                  <p
                    style={{
                      fontSize: 14, fontWeight: 600,
                      color: "var(--text-primary)",
                      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                    }}
                  >
                    {ticket.user_name}
                  </p>
                  {/* Sub: summary or phone */}
                  <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {ticket.summary || ticket.phone || "—"}
                  </p>
                </div>

                {/* Middle: language + sentiment */}
                <div style={{ flexShrink: 0, textAlign: "right", minWidth: 60 }}>
                  <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>{ticket.language}</p>
                  <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{ticket.sentiment || "—"}</p>
                </div>

                {/* Right: priority + status pills */}
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 5, flexShrink: 0 }}>
                  <span
                    style={{
                      fontSize: 10, fontWeight: 600, padding: "3px 9px", borderRadius: 999,
                      background: PRIORITY_BG[ticket.priority] || "transparent",
                      color: PRIORITY_COLOR[ticket.priority] || "var(--text-secondary)",
                    }}
                  >
                    {ticket.priority}
                  </span>
                  <span
                    style={{
                      fontSize: 10, fontWeight: 600, padding: "3px 9px", borderRadius: 999,
                      background: STATUS_BG[ticket.status] || "transparent",
                      color: STATUS_COLOR[ticket.status] || "var(--text-secondary)",
                    }}
                  >
                    {ticket.status}
                  </span>
                </div>

                {/* Date */}
                <span
                  style={{ fontSize: 11, color: "var(--text-muted)", flexShrink: 0, minWidth: 70, textAlign: "right" }}
                >
                  {new Date(ticket.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                </span>
              </motion.div>
            </Link>
          ))
        )}
      </motion.div>
    </div>
  );
}
