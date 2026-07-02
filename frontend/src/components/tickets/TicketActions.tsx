"use client";

import { Button, Panel } from "@/components/ui";

type Props = {
  status: string;
  replyText: string;
  onReplyTextChange: (value: string) => void;
  acting: boolean;
  actionError: string | null;
  onReply: () => void;
  onClaim: () => void;
  onResolve: () => void;
};

/** Agent action bar: reply textarea + send / claim / resolve buttons. */
export function TicketActions({
  status,
  replyText,
  onReplyTextChange,
  acting,
  actionError,
  onReply,
  onClaim,
  onResolve,
}: Props) {
  const isResolved = status === "Resolved";

  return (
    <Panel style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 14 }}>
      <label className="eyebrow" htmlFor="agent-reply">RESPOND AS AGENT</label>
      <textarea
        id="agent-reply"
        value={replyText}
        onChange={(e) => onReplyTextChange(e.target.value)}
        placeholder="Type a reply to the customer…"
        rows={3}
        disabled={acting || isResolved}
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
        <p role="alert" style={{ fontSize: 12, color: "var(--status-high)" }}>{actionError}</p>
      )}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <Button
          size="sm"
          onClick={onReply}
          isLoading={acting}
          disabled={!replyText.trim() || isResolved}
        >
          {acting ? "Sending…" : "Send reply"}
        </Button>
        {(status === "Escalated" || status === "Open") && (
          <Button size="sm" variant="ghost" onClick={onClaim} disabled={acting}>
            Claim
          </Button>
        )}
        {!isResolved && (
          <Button
            size="sm"
            variant="ghost"
            onClick={onResolve}
            disabled={acting}
            style={{
              background: "rgba(76,175,115,0.12)",
              color: "var(--status-low)",
              border: "1px solid rgba(76,175,115,0.35)",
            }}
          >
            Mark resolved
          </Button>
        )}
      </div>
    </Panel>
  );
}
