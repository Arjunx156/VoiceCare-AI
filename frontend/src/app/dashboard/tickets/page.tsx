"use client";

/**
 * Tickets list — editorial list-row pattern: eyebrow (ticket type) above a
 * bold title, thin dividers between rows, dot+text status pills on the right.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Inbox } from "lucide-react";
import { getTickets, type TicketSummary } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useMotionSafe } from "@/lib/motion";
import { EmptyState, LoadingBlock, PageHeader, PriorityBadge, StatusBadge } from "@/components/ui";

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
  background: "var(--bg-panel)",
  border: "1px solid var(--border-subtle)",
  color: "var(--text-secondary)",
  cursor: "pointer",
  appearance: "none",
  WebkitAppearance: "none",
};

type FetchResult =
  | { key: string; tickets: TicketSummary[] }
  | { key: string; error: string };

export default function TicketsPage() {
  const [filter, setFilter] = useState({ status: "", priority: "" });
  const [result, setResult] = useState<FetchResult | null>(null);
  const { entry } = useMotionSafe();

  const filterKey = `${filter.status}|${filter.priority}`;

  useEffect(() => {
    let cancelled = false;
    const [status, priority] = filterKey.split("|");
    getTickets({ status: status || undefined, priority: priority || undefined })
      .then((tickets) => {
        if (!cancelled) setResult({ key: filterKey, tickets });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setResult({
            key: filterKey,
            error: err instanceof Error ? err.message : "Failed to load tickets",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [filterKey]);

  // Only trust a result produced by the current filter (race-safe).
  const current = result?.key === filterKey ? result : null;
  const loading = current === null;
  const error = current && "error" in current ? current.error : null;
  const tickets = current && "tickets" in current ? current.tickets : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      <PageHeader
        eyebrow="SUPPORT TICKETS"
        title={loading ? "Loading…" : error ? "Error" : `${tickets.length} ticket${tickets.length !== 1 ? "s" : ""}`}
        subtitle={error ?? undefined}
        actions={
          <>
            <select
              value={filter.status}
              onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}
              aria-label="Filter by status"
              style={selectStyle}
            >
              {FILTER_OPTIONS.status.map((s) => (
                <option key={s} value={s}>{s || "All Status"}</option>
              ))}
            </select>
            <select
              value={filter.priority}
              onChange={(e) => setFilter((f) => ({ ...f, priority: e.target.value }))}
              aria-label="Filter by priority"
              style={selectStyle}
            >
              {FILTER_OPTIONS.priority.map((p) => (
                <option key={p} value={p}>{p || "All Priority"}</option>
              ))}
            </select>
          </>
        }
      />

      {/* Ticket list — editorial list-row pattern */}
      <motion.div {...entry(0.1)} className="panel" style={{ overflow: "hidden" }}>
        {loading ? (
          <LoadingBlock label="Loading tickets" />
        ) : tickets.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No tickets found"
            hint={filter.status || filter.priority ? "Try clearing the filters." : "New voice queries will appear here."}
          />
        ) : (
          tickets.map((ticket, i) => (
            <Link
              key={ticket.ticket_id}
              href={`/dashboard/tickets/${ticket.ticket_id}`}
              style={{ textDecoration: "none", display: "block" }}
            >
              <motion.div
                {...entry(Math.min(i * 0.03, 0.3))}
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
                  <p
                    style={{
                      fontSize: 14, fontWeight: 600,
                      color: "var(--text-primary)",
                      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                    }}
                  >
                    {ticket.user_name}
                  </p>
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
                  <PriorityBadge priority={ticket.priority} />
                  <StatusBadge status={ticket.status} />
                </div>

                {/* Date */}
                <span
                  style={{ fontSize: 11, color: "var(--text-muted)", flexShrink: 0, minWidth: 70, textAlign: "right" }}
                >
                  {formatDate(ticket.created_at)}
                </span>
              </motion.div>
            </Link>
          ))
        )}
      </motion.div>
    </div>
  );
}
