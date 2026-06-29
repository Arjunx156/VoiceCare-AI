"use client";

/**
 * CommerceMind VoiceCare AI — Ticket Detail v2
 * Design brief: eyebrow + bold title header, pill tabs, inline panels,
 * no glassmorphism, semantic status colors only, agent replay as numbered
 * vertical timeline matching the 01-09 pipeline aesthetic.
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  getTicketDetail,
  getHandoffNote,
  replyToTicket,
  resolveTicket,
  claimTicket,
  type TicketDetail,
  type HandoffNote,
} from "@/lib/api";

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
  Escalated: "var(--status-high)",
  Resolved:  "var(--status-low)",
  Open:      "var(--status-calm)",
  "In Progress": "var(--status-medium)",
  Closed:    "var(--text-muted)",
};

export default function TicketDetailPage() {
  const params   = useParams();
  const ticketId = params.id as string;

  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [handoff, setHandoff] = useState<HandoffNote | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"detail" | "replay" | "handoff">("detail");

  const [replyText, setReplyText] = useState("");
  const [acting, setActing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  async function load() {
    try {
      const data = await getTicketDetail(ticketId);
      setTicket(data);
      if (data.status === "Escalated") {
        try { setHandoff(await getHandoffNote(ticketId)); } catch {}
      }
    } catch (err) {
      console.error("Failed to load ticket:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (ticketId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticketId]);

  async function handleSendReply() {
    if (!replyText.trim() || acting) return;
    setActing(true);
    setActionError(null);
    try {
      await replyToTicket(ticketId, replyText.trim());
      setReplyText("");
      await load();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to send reply.");
    } finally {
      setActing(false);
    }
  }

  async function handleResolve() {
    if (acting) return;
    setActing(true);
    setActionError(null);
    try {
      await resolveTicket(ticketId);
      await load();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to resolve.");
    } finally {
      setActing(false);
    }
  }

  async function handleClaim() {
    if (acting) return;
    setActing(true);
    setActionError(null);
    try {
      await claimTicket(ticketId);
      await load();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to claim.");
    } finally {
      setActing(false);
    }
  }

  if (loading) {
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

  if (!ticket) {
    return (
      <div style={{ textAlign: "center", padding: "80px 0" }}>
        <p style={{ fontSize: 40, marginBottom: 12 }}>🔍</p>
        <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Ticket not found</p>
        <Link href="/dashboard/tickets" style={{ fontSize: 13, color: "var(--accent)", marginTop: 8, display: "inline-block" }}>
          Back to tickets
        </Link>
      </div>
    );
  }

  const tabs = [
    { key: "detail",  label: "Details"      },
    { key: "replay",  label: "Agent Replay"  },
    ...(ticket.status === "Escalated" ? [{ key: "handoff", label: "Handoff Note" }] : []),
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      style={{ display: "flex", flexDirection: "column", gap: 24, maxWidth: 820 }}
    >
      {/* Breadcrumb */}
      <nav style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-muted)" }}>
        <Link href="/dashboard" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Dashboard</Link>
        <span>›</span>
        <Link href="/dashboard/tickets" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Tickets</Link>
        <span>›</span>
        <span style={{ color: "var(--text-secondary)" }}>{ticket.ticket_number ?? ticketId.substring(0, 8) + "…"}</span>
      </nav>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
        <div>
          <span className="eyebrow">{ticket.ticket_type || "SUPPORT"}</span>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>
            {ticket.user_name}
          </h1>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
            {ticket.phone} · {ticket.language}
          </p>
        </div>
        {/* Status + priority badges */}
        <div style={{ display: "flex", gap: 8, flexShrink: 0, paddingTop: 4 }}>
          <span style={{
            fontSize: 12, fontWeight: 600, padding: "5px 12px", borderRadius: 999,
            background: PRIORITY_BG[ticket.priority] || "rgba(90,90,90,0.12)",
            color: PRIORITY_COLOR[ticket.priority] || "var(--text-secondary)",
          }}>
            {ticket.priority}
          </span>
          <span style={{
            fontSize: 12, fontWeight: 600, padding: "5px 12px", borderRadius: 999,
            background: "rgba(96,125,139,0.12)",
            color: STATUS_COLOR[ticket.status] || "var(--text-secondary)",
          }}>
            {ticket.status}
          </span>
        </div>
      </div>

      {/* Tab strip */}
      <div style={{
        display: "flex",
        gap: 2,
        background: "var(--bg-panel)",
        border: "1px solid var(--border-subtle)",
        padding: 4,
        borderRadius: 999,
        width: "fit-content",
      }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as typeof activeTab)}
            style={{
              padding: "7px 18px",
              borderRadius: 999,
              fontSize: 12,
              fontWeight: activeTab === tab.key ? 600 : 400,
              background: activeTab === tab.key ? "var(--accent)" : "transparent",
              color: activeTab === tab.key ? "#fff" : "var(--text-secondary)",
              border: "none",
              cursor: "pointer",
              fontFamily: "var(--font-sans)",
              transition: "background 140ms, color 140ms",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ─── Details Tab ─── */}
      {activeTab === "detail" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Info grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
            {[
              { eyebrow: "TYPE",       value: ticket.ticket_type },
              { eyebrow: "PRIORITY",   value: ticket.priority },
              { eyebrow: "SENTIMENT",  value: ticket.sentiment || "N/A" },
              { eyebrow: "CONFIDENCE", value: ticket.confidence_score ? `${(ticket.confidence_score * 100).toFixed(0)}%` : "N/A" },
            ].map((item) => (
              <div key={item.eyebrow} className="panel" style={{ padding: "14px 16px" }}>
                <span className="eyebrow">{item.eyebrow}</span>
                <p style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>{item.value}</p>
              </div>
            ))}
          </div>

          {/* Summary + AI response */}
          <div className="panel" style={{ padding: "24px 24px", display: "flex", flexDirection: "column", gap: 20 }}>
            <div>
              <span className="eyebrow">ISSUE SUMMARY</span>
              <p style={{ fontSize: 14, color: "var(--text-primary)", lineHeight: 1.6 }}>
                {ticket.summary || "No summary available"}
              </p>
            </div>
            {ticket.response_text && (
              <>
                <div className="divider" />
                <div>
                  <span className="eyebrow">AI RESPONSE</span>
                  <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                    {ticket.response_text}
                  </p>
                </div>
              </>
            )}
            {ticket.policy_reference && (
              <>
                <div className="divider" />
                <div>
                  <span className="eyebrow">POLICY REFERENCED</span>
                  <p style={{ fontSize: 13, fontStyle: "italic", color: "var(--text-muted)" }}>
                    {ticket.policy_reference}
                  </p>
                </div>
              </>
            )}
          </div>

          {/* Conversation */}
          {ticket.messages.length > 0 && (
            <div className="panel" style={{ padding: "24px" }}>
              <span className="eyebrow">CONVERSATION</span>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {ticket.messages.map((msg, i) => (
                  <div
                    key={msg.message_id || i}
                    style={{
                      display: "flex",
                      justifyContent: msg.sender_type === "Customer" ? "flex-start" : "flex-end",
                    }}
                  >
                    <div
                      style={{
                        maxWidth: "78%",
                        padding: "10px 14px",
                        borderRadius: msg.sender_type === "Customer" ? "4px 18px 18px 18px" : "18px 4px 18px 18px",
                        background:
                          msg.sender_type === "Customer" ? "var(--bg-panel-raised)"
                          : msg.sender_type === "Human" ? "rgba(76,175,115,0.10)"
                          : "var(--accent-dim)",
                        border:
                          msg.sender_type === "Customer" ? "1px solid var(--border-subtle)"
                          : msg.sender_type === "Human" ? "1px solid rgba(76,175,115,0.35)"
                          : "1px solid var(--accent-border)",
                      }}
                    >
                      <p style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.06em", marginBottom: 4, color: msg.sender_type === "Human" ? "var(--status-low)" : "var(--text-muted)" }}>
                        {msg.sender_type === "Human" ? "AGENT (YOU)" : msg.sender_type.toUpperCase()}
                      </p>
                      <p style={{ fontSize: 13, color: "var(--text-primary)", lineHeight: 1.5 }}>{msg.message_text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Agent action bar: reply + resolve */}
          <div className="panel" style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 14 }}>
            <span className="eyebrow">RESPOND AS AGENT</span>
            <textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Type a reply to the customer…"
              rows={3}
              disabled={acting || ticket.status === "Resolved"}
              style={{
                width: "100%",
                resize: "vertical",
                padding: "12px 14px",
                borderRadius: 12,
                fontSize: 14,
                fontFamily: "var(--font-sans)",
                background: "var(--bg-panel-raised)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-primary)",
                lineHeight: 1.5,
              }}
            />
            {actionError && (
              <p style={{ fontSize: 12, color: "var(--status-high)" }}>{actionError}</p>
            )}
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button
                onClick={handleSendReply}
                disabled={acting || !replyText.trim() || ticket.status === "Resolved"}
                style={{
                  padding: "9px 20px", borderRadius: 999, border: "none",
                  fontSize: 13, fontWeight: 600, cursor: acting || !replyText.trim() ? "not-allowed" : "pointer",
                  background: "var(--accent)", color: "#fff", opacity: acting || !replyText.trim() || ticket.status === "Resolved" ? 0.5 : 1,
                  fontFamily: "var(--font-sans)",
                }}
              >
                {acting ? "Sending…" : "Send reply"}
              </button>
              {(ticket.status === "Escalated" || ticket.status === "Open") && (
                <button
                  onClick={handleClaim}
                  disabled={acting}
                  style={{
                    padding: "9px 20px", borderRadius: 999, fontSize: 13, fontWeight: 600,
                    cursor: acting ? "not-allowed" : "pointer", fontFamily: "var(--font-sans)",
                    background: "transparent", color: "var(--text-secondary)",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  Claim
                </button>
              )}
              {ticket.status !== "Resolved" && (
                <button
                  onClick={handleResolve}
                  disabled={acting}
                  style={{
                    padding: "9px 20px", borderRadius: 999, fontSize: 13, fontWeight: 600,
                    cursor: acting ? "not-allowed" : "pointer", fontFamily: "var(--font-sans)",
                    background: "rgba(76,175,115,0.12)", color: "var(--status-low)",
                    border: "1px solid rgba(76,175,115,0.35)",
                  }}
                >
                  Mark resolved
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ─── Agent Replay Tab ─── */}
      {activeTab === "replay" && (
        <div className="panel" style={{ padding: "24px" }}>
          <span className="eyebrow">AGENT DECISION REPLAY</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 24 }}>
            Pipeline Trace
          </h2>
          {ticket.agent_trace.length > 0 ? (
            <div>
              {ticket.agent_trace.map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.07 }}
                  style={{ display: "flex", gap: 16, paddingBottom: 24, position: "relative" }}
                >
                  {/* Vertical line */}
                  {i < ticket.agent_trace.length - 1 && (
                    <div
                      style={{
                        position: "absolute",
                        left: 15, top: 32,
                        width: 1,
                        bottom: 0,
                        background: "var(--border-subtle)",
                      }}
                    />
                  )}

                  {/* Step number bubble */}
                  <div
                    style={{
                      width: 32, height: 32, borderRadius: "50%",
                      background: "var(--bg-panel-raised)",
                      border: "1px solid var(--border-raised)",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      flexShrink: 0,
                      fontSize: 11, fontWeight: 700, fontVariantNumeric: "tabular-nums",
                      color: "var(--accent)",
                    }}
                  >
                    {String(step.stage_number).padStart(2, "0")}
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
                      {step.agent_name}
                    </p>
                    {step.decision && (
                      <p style={{ fontSize: 12, color: "var(--accent)", marginTop: 3 }}>
                        Decision: {step.decision}
                      </p>
                    )}
                    {step.reasoning && (
                      <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 3, lineHeight: 1.5 }}>
                        {step.reasoning}
                      </p>
                    )}
                    <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4, lineHeight: 1.5 }}>
                      {step.output_summary}
                    </p>
                    {step.duration_ms && (
                      <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, fontVariantNumeric: "tabular-nums" }}>
                        {step.duration_ms.toFixed(0)} ms
                      </p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: 13, textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
              No agent trace available for this ticket
            </p>
          )}
        </div>
      )}

      {/* ─── Handoff Note Tab ─── */}
      {activeTab === "handoff" && handoff && (
        <div className="panel" style={{ padding: "24px" }}>
          <span className="eyebrow">AUTO-GENERATED HANDOFF NOTE</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 24 }}>
            Escalation Brief
          </h2>

          {/* Quick facts */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 20 }}>
            {[
              { label: "Customer",  value: handoff.customer_name },
              { label: "Phone",     value: handoff.customer_phone },
              { label: "Language",  value: handoff.language },
              { label: "Sentiment", value: handoff.sentiment, warn: true },
            ].map((r) => (
              <div key={r.label} style={{ background: "var(--bg-panel-raised)", borderRadius: 12, padding: "12px 14px" }}>
                <span className="eyebrow" style={{ marginBottom: 4 }}>{r.label.toUpperCase()}</span>
                <p style={{ fontSize: 14, fontWeight: 600, color: r.warn ? "var(--status-high)" : "var(--text-primary)" }}>
                  {r.value}
                </p>
              </div>
            ))}
          </div>

          {/* Text fields */}
          {[
            { label: "ISSUE SUMMARY",           value: handoff.issue_summary,               accent: false },
            { label: "ESCALATION REASON",        value: handoff.escalation_reason,           accent: false, warn: true },
            { label: "AI ATTEMPTED RESOLUTION",  value: handoff.ai_attempted_resolution,     accent: false },
            { label: "RECOMMENDED NEXT STEPS",   value: handoff.recommended_next_steps,      accent: true  },
          ].map((section, i) => (
            <div key={section.label}>
              {i > 0 && <div className="divider" style={{ margin: "16px 0" }} />}
              <span className="eyebrow">{section.label}</span>
              <p style={{
                fontSize: 14,
                lineHeight: 1.6,
                color: section.warn ? "var(--status-high)" : section.accent ? "var(--accent)" : "var(--text-secondary)",
              }}>
                {section.value}
              </p>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
