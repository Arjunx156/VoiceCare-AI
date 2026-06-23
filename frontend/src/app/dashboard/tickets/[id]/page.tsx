"use client";

/**
 * CommerceMind VoiceCare AI — Ticket Detail + Replay View
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { getTicketDetail, getHandoffNote, type TicketDetail, type HandoffNote } from "@/lib/api";

export default function TicketDetailPage() {
  const params = useParams();
  const ticketId = params.id as string;
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [handoff, setHandoff] = useState<HandoffNote | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"detail" | "replay" | "handoff">("detail");

  useEffect(() => {
    async function load() {
      try {
        const data = await getTicketDetail(ticketId);
        setTicket(data);
        if (data.status === "Escalated") {
          try {
            const h = await getHandoffNote(ticketId);
            setHandoff(h);
          } catch {}
        }
      } catch (err) {
        console.error("Failed to load ticket:", err);
      } finally {
        setLoading(false);
      }
    }
    if (ticketId) load();
  }, [ticketId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 rounded-full"
          style={{ border: "2px solid var(--border-subtle)", borderTopColor: "var(--primary)" }}
        />
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="text-center py-20">
        <p className="text-2xl mb-2">🔍</p>
        <p style={{ color: "var(--text-muted)" }}>Ticket not found</p>
      </div>
    );
  }

  const tabs = [
    { key: "detail", label: "Details" },
    { key: "replay", label: "Agent Replay" },
    ...(ticket.status === "Escalated" ? [{ key: "handoff", label: "Handoff Note" }] : []),
  ];

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
        <Link href="/dashboard/tickets" className="hover:opacity-80">Tickets</Link>
        <span>→</span>
        <span style={{ color: "var(--text-secondary)" }}>{ticketId.substring(0, 8)}...</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            {ticket.user_name}
          </h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>{ticket.phone}</span>
            <span className="text-xs px-2 py-0.5 rounded-full" style={{
              background: ticket.status === "Escalated" ? "rgba(239,68,68,0.15)" : "rgba(16,185,129,0.15)",
              color: ticket.status === "Escalated" ? "var(--error)" : "var(--success)",
            }}>{ticket.status}</span>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>{ticket.language}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-lg" style={{ background: "var(--bg-card)" }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as typeof activeTab)}
            className="flex-1 px-4 py-2 text-sm rounded-md transition-all"
            style={{
              background: activeTab === tab.key ? "var(--primary)" : "transparent",
              color: activeTab === tab.key ? "#fff" : "var(--text-secondary)",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "detail" && (
        <div className="space-y-4">
          {/* Info Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Type", value: ticket.ticket_type },
              { label: "Priority", value: ticket.priority },
              { label: "Sentiment", value: ticket.sentiment || "N/A" },
              { label: "Confidence", value: ticket.confidence_score ? `${(ticket.confidence_score * 100).toFixed(0)}%` : "N/A" },
            ].map((item) => (
              <div key={item.label} className="glass-card p-3">
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>{item.label}</p>
                <p className="text-sm font-medium mt-1" style={{ color: "var(--text-primary)" }}>{item.value}</p>
              </div>
            ))}
          </div>

          {/* Summary & Resolution */}
          <div className="glass-card p-5 space-y-4">
            <div>
              <h3 className="text-xs font-semibold mb-1" style={{ color: "var(--text-muted)" }}>Issue Summary</h3>
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>{ticket.summary || "No summary"}</p>
            </div>
            {ticket.response_text && (
              <div>
                <h3 className="text-xs font-semibold mb-1" style={{ color: "var(--text-muted)" }}>AI Response</h3>
                <p className="text-sm" style={{ color: "var(--text-primary)" }}>{ticket.response_text}</p>
              </div>
            )}
            {ticket.policy_reference && (
              <div>
                <h3 className="text-xs font-semibold mb-1" style={{ color: "var(--text-muted)" }}>Policy Referenced</h3>
                <p className="text-sm italic" style={{ color: "var(--text-secondary)" }}>{ticket.policy_reference}</p>
              </div>
            )}
          </div>

          {/* Messages */}
          {ticket.messages.length > 0 && (
            <div className="glass-card p-5">
              <h3 className="text-xs font-semibold mb-3" style={{ color: "var(--text-muted)" }}>Conversation</h3>
              <div className="space-y-3">
                {ticket.messages.map((msg, i) => (
                  <div
                    key={msg.message_id || i}
                    className={`flex ${msg.sender_type === "Customer" ? "justify-start" : "justify-end"}`}
                  >
                    <div
                      className="max-w-[80%] px-4 py-2 rounded-2xl text-sm"
                      style={{
                        background: msg.sender_type === "Customer" ? "var(--bg-card)" : "var(--primary)",
                        color: msg.sender_type === "Customer" ? "var(--text-primary)" : "#fff",
                      }}
                    >
                      <p className="text-[10px] font-medium mb-1 opacity-60">{msg.sender_type}</p>
                      <p>{msg.message_text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "replay" && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            🔄 Agent Decision Replay
          </h3>
          {ticket.agent_trace.length > 0 ? (
            <div className="space-y-4">
              {ticket.agent_trace.map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex gap-4"
                >
                  {/* Timeline dot */}
                  <div className="flex flex-col items-center">
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                      style={{ background: "var(--primary)", color: "#fff" }}
                    >
                      {step.stage_number}
                    </div>
                    {i < ticket.agent_trace.length - 1 && (
                      <div className="w-0.5 flex-1 mt-2" style={{ background: "var(--border-subtle)" }} />
                    )}
                  </div>
                  {/* Content */}
                  <div className="flex-1 pb-4">
                    <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      {step.agent_name}
                    </p>
                    {step.decision && (
                      <p className="text-xs mt-1" style={{ color: "var(--accent)" }}>
                        Decision: {step.decision}
                      </p>
                    )}
                    {step.reasoning && (
                      <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                        {step.reasoning}
                      </p>
                    )}
                    <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                      {step.output_summary}
                    </p>
                    {step.duration_ms && (
                      <p className="text-[10px] mt-1" style={{ color: "var(--text-muted)" }}>
                        ⏱️ {step.duration_ms.toFixed(0)}ms
                      </p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-center py-8" style={{ color: "var(--text-muted)" }}>
              No agent trace available for this ticket
            </p>
          )}
        </div>
      )}

      {activeTab === "handoff" && handoff && (
        <div className="glass-card p-5 space-y-4">
          <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            📋 Auto-Generated Handoff Note
          </h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span style={{ color: "var(--text-muted)" }}>Customer:</span> <span style={{ color: "var(--text-primary)" }}>{handoff.customer_name}</span></div>
            <div><span style={{ color: "var(--text-muted)" }}>Phone:</span> <span style={{ color: "var(--text-primary)" }}>{handoff.customer_phone}</span></div>
            <div><span style={{ color: "var(--text-muted)" }}>Language:</span> <span style={{ color: "var(--text-primary)" }}>{handoff.language}</span></div>
            <div><span style={{ color: "var(--text-muted)" }}>Sentiment:</span> <span style={{ color: "var(--error)" }}>{handoff.sentiment}</span></div>
          </div>
          <div>
            <p className="text-xs font-semibold mb-1" style={{ color: "var(--text-muted)" }}>Issue Summary</p>
            <p className="text-sm" style={{ color: "var(--text-primary)" }}>{handoff.issue_summary}</p>
          </div>
          <div>
            <p className="text-xs font-semibold mb-1" style={{ color: "var(--text-muted)" }}>Escalation Reason</p>
            <p className="text-sm" style={{ color: "var(--error)" }}>{handoff.escalation_reason}</p>
          </div>
          <div>
            <p className="text-xs font-semibold mb-1" style={{ color: "var(--text-muted)" }}>AI Attempted Resolution</p>
            <p className="text-sm" style={{ color: "var(--text-primary)" }}>{handoff.ai_attempted_resolution}</p>
          </div>
          <div>
            <p className="text-xs font-semibold mb-1" style={{ color: "var(--text-muted)" }}>Recommended Next Steps</p>
            <p className="text-sm" style={{ color: "var(--accent)" }}>{handoff.recommended_next_steps}</p>
          </div>
        </div>
      )}
    </div>
  );
}
