"use client";

import { Panel } from "@/components/ui";
import type { TicketDetail } from "@/lib/api";

type Message = TicketDetail["messages"][number];

function bubbleStyle(senderType: string): React.CSSProperties {
  if (senderType === "Customer") {
    return {
      borderRadius: "4px 18px 18px 18px",
      background: "var(--bg-panel-raised)",
      border: "1px solid var(--border-subtle)",
    };
  }
  if (senderType === "Human") {
    return {
      borderRadius: "18px 4px 18px 18px",
      background: "rgba(76,175,115,0.10)",
      border: "1px solid rgba(76,175,115,0.35)",
    };
  }
  return {
    borderRadius: "18px 4px 18px 18px",
    background: "var(--accent-dim)",
    border: "1px solid var(--accent-border)",
  };
}

/** Customer / AI / human-agent conversation transcript. */
export function TicketConversation({ messages }: { messages: Message[] }) {
  if (messages.length === 0) return null;

  return (
    <Panel style={{ padding: 24 }}>
      <span className="eyebrow">CONVERSATION</span>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {messages.map((msg, i) => (
          <div
            key={msg.message_id || i}
            style={{
              display: "flex",
              justifyContent: msg.sender_type === "Customer" ? "flex-start" : "flex-end",
            }}
          >
            <div style={{ maxWidth: "78%", padding: "10px 14px", ...bubbleStyle(msg.sender_type) }}>
              <p
                style={{
                  fontSize: 10,
                  fontWeight: 600,
                  letterSpacing: "0.06em",
                  marginBottom: 4,
                  color: msg.sender_type === "Human" ? "var(--status-low)" : "var(--text-muted)",
                }}
              >
                {msg.sender_type === "Human" ? "AGENT (YOU)" : msg.sender_type.toUpperCase()}
              </p>
              <p style={{ fontSize: 13, color: "var(--text-primary)", lineHeight: 1.5 }}>{msg.message_text}</p>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
