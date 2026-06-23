"use client";

/**
 * CommerceMind VoiceCare AI — Escalations Page
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { getEscalations, type TicketSummary } from "@/lib/api";

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<TicketSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setEscalations(await getEscalations());
      } catch (err) {
        console.error("Failed to load escalations:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 rounded-full"
          style={{ border: "2px solid var(--border-subtle)", borderTopColor: "var(--primary)" }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          🚨 Escalation Queue
        </h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
          {escalations.length} tickets awaiting human review
        </p>
      </div>

      {escalations.length === 0 ? (
        <div className="glass-card text-center py-16">
          <p className="text-4xl mb-4">🎉</p>
          <p className="text-lg font-medium" style={{ color: "var(--text-primary)" }}>
            No pending escalations
          </p>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            All tickets are being handled by AI
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {escalations.map((ticket, i) => (
            <motion.div
              key={ticket.ticket_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Link href={`/dashboard/tickets/${ticket.ticket_id}`}>
                <div className="glass-card p-5 hover:cursor-pointer transition-all" style={{ borderColor: "rgba(239,68,68,0.2)" }}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <span className="status-dot escalated" />
                      <div>
                        <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                          {ticket.user_name}
                        </p>
                        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                          {ticket.phone} • {ticket.language}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs px-2 py-1 rounded-full" style={{
                        background: ticket.priority === "Critical" ? "rgba(239,68,68,0.15)" : "rgba(245,158,11,0.15)",
                        color: ticket.priority === "Critical" ? "var(--error)" : "var(--warning)",
                      }}>
                        {ticket.priority}
                      </span>
                      <p className="text-[10px] mt-1" style={{ color: "var(--text-muted)" }}>
                        {new Date(ticket.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm mt-3" style={{ color: "var(--text-secondary)" }}>
                    {ticket.summary || `${ticket.ticket_type} issue`}
                  </p>
                  <div className="flex items-center gap-4 mt-3">
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                      Type: {ticket.ticket_type}
                    </span>
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                      Sentiment: {ticket.sentiment || "N/A"}
                    </span>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
