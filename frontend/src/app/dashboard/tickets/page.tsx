"use client";

/**
 * CommerceMind VoiceCare AI — Tickets List Page
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { getTickets, type TicketSummary } from "@/lib/api";

const PRIORITY_COLORS: Record<string, { bg: string; text: string }> = {
  Critical: { bg: "rgba(239,68,68,0.15)", text: "var(--error)" },
  High: { bg: "rgba(245,158,11,0.15)", text: "var(--warning)" },
  Medium: { bg: "rgba(59,130,246,0.15)", text: "var(--info)" },
  Low: { bg: "rgba(16,185,129,0.15)", text: "var(--success)" },
};

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  Open: { bg: "rgba(59,130,246,0.15)", text: "var(--info)" },
  "In Progress": { bg: "rgba(245,158,11,0.15)", text: "var(--warning)" },
  Resolved: { bg: "rgba(16,185,129,0.15)", text: "var(--success)" },
  Escalated: { bg: "rgba(239,68,68,0.15)", text: "var(--error)" },
  Closed: { bg: "rgba(100,116,139,0.15)", text: "var(--text-muted)" },
};

export default function TicketsPage() {
  const [tickets, setTickets] = useState<TicketSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ status: "", priority: "" });

  useEffect(() => {
    async function load() {
      try {
        const data = await getTickets({
          status: filter.status || undefined,
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Support Tickets
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            {tickets.length} tickets found
          </p>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          <select
            value={filter.status}
            onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}
            className="px-3 py-2 text-xs rounded-lg outline-none"
            style={{
              background: "var(--glass-bg)",
              border: "1px solid var(--glass-border)",
              color: "var(--text-secondary)",
            }}
          >
            <option value="">All Status</option>
            <option value="Open">Open</option>
            <option value="Escalated">Escalated</option>
            <option value="Resolved">Resolved</option>
          </select>
          <select
            value={filter.priority}
            onChange={(e) => setFilter((f) => ({ ...f, priority: e.target.value }))}
            className="px-3 py-2 text-xs rounded-lg outline-none"
            style={{
              background: "var(--glass-bg)",
              border: "1px solid var(--glass-border)",
              color: "var(--text-secondary)",
            }}
          >
            <option value="">All Priority</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
      </div>

      {/* Ticket Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                {["Customer", "Type", "Priority", "Status", "Language", "Sentiment", "Created"].map((h) => (
                  <th
                    key={h}
                    className="text-left text-xs font-medium px-4 py-3"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-12">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-6 h-6 rounded-full mx-auto"
                      style={{ border: "2px solid var(--border-subtle)", borderTopColor: "var(--primary)" }}
                    />
                  </td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12">
                    <p className="text-2xl mb-2">📭</p>
                    <p className="text-sm" style={{ color: "var(--text-muted)" }}>No tickets found</p>
                  </td>
                </tr>
              ) : (
                tickets.map((ticket, i) => (
                  <motion.tr
                    key={ticket.ticket_id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="transition-all hover:cursor-pointer"
                    style={{ borderBottom: "1px solid var(--border-subtle)" }}
                  >
                    <td className="px-4 py-3">
                      <Link href={`/dashboard/tickets/${ticket.ticket_id}`} className="block">
                        <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                          {ticket.user_name}
                        </p>
                        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                          {ticket.phone}
                        </p>
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: "var(--text-secondary)" }}>
                      {ticket.ticket_type}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="text-xs px-2 py-1 rounded-full"
                        style={{
                          background: PRIORITY_COLORS[ticket.priority]?.bg || "transparent",
                          color: PRIORITY_COLORS[ticket.priority]?.text || "var(--text-secondary)",
                        }}
                      >
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="text-xs px-2 py-1 rounded-full"
                        style={{
                          background: STATUS_COLORS[ticket.status]?.bg || "transparent",
                          color: STATUS_COLORS[ticket.status]?.text || "var(--text-secondary)",
                        }}
                      >
                        {ticket.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: "var(--text-secondary)" }}>
                      {ticket.language}
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: "var(--text-secondary)" }}>
                      {ticket.sentiment || "—"}
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: "var(--text-muted)" }}>
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
