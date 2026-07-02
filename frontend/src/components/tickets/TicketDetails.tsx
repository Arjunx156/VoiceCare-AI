"use client";

import { Panel } from "@/components/ui";
import type { TicketDetail } from "@/lib/api";

/** Info grid + issue summary / AI response / policy panels. */
export function TicketDetails({ ticket }: { ticket: TicketDetail }) {
  const facts = [
    { eyebrow: "TYPE",       value: ticket.ticket_type },
    { eyebrow: "PRIORITY",   value: ticket.priority },
    { eyebrow: "SENTIMENT",  value: ticket.sentiment || "N/A" },
    {
      eyebrow: "CONFIDENCE",
      value: ticket.confidence_score ? `${(ticket.confidence_score * 100).toFixed(0)}%` : "N/A",
    },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10 }}>
        {facts.map((item) => (
          <Panel key={item.eyebrow} style={{ padding: "14px 16px" }}>
            <span className="eyebrow">{item.eyebrow}</span>
            <p style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>{item.value}</p>
          </Panel>
        ))}
      </div>

      <Panel style={{ padding: "24px 24px", display: "flex", flexDirection: "column", gap: 20 }}>
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
      </Panel>
    </div>
  );
}
