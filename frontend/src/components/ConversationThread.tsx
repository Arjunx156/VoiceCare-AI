"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Mic } from "lucide-react";
import ResponsePanel from "@/components/ResponsePanel";
import { useI18n } from "@/lib/i18n/I18nProvider";
import type { ConversationTurn, RestoredTurn } from "@/hooks/useVoiceInteraction";

/** Customer speech bubble (shared by live and restored turns). */
function CustomerBubble({ text, listeningLabel }: { text: string; listeningLabel: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "flex-end" }}>
      <div
        style={{
          maxWidth: "85%",
          padding: "10px 14px",
          borderRadius: "14px 14px 4px 14px",
          background: "rgba(255,90,43,0.10)",
          border: "1px solid rgba(255,90,43,0.25)",
          fontSize: 14,
          lineHeight: 1.5,
          color: "var(--text-primary)",
        }}
      >
        {text?.trim() || (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <Mic size={13} strokeWidth={1.75} aria-hidden="true" />
            {listeningLabel}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * The full visible conversation for the current session: each completed turn
 * shows what the customer said followed by the assistant's response. Stays on
 * screen across mic presses so customers can see the ongoing conversation.
 * Turns restored from server memory after a reload render as plain bubbles
 * (their full response objects aren't persisted).
 */
export default function ConversationThread({
  turns,
  restoredTurns = [],
}: {
  turns: ConversationTurn[];
  restoredTurns?: RestoredTurn[];
}) {
  const { t } = useI18n();
  const endRef = useRef<HTMLDivElement>(null);

  // Bring each newly completed turn into view so the conversation reads
  // like a chat that scrolls as it grows.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length]);

  if (turns.length === 0 && restoredTurns.length === 0) return null;

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 16, marginTop: 16 }}>
      {restoredTurns.length > 0 && (
        <div
          role="separator"
          style={{ display: "flex", alignItems: "center", gap: 12 }}
        >
          <div className="divider" style={{ flex: 1 }} />
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              color: "var(--text-muted)",
              whiteSpace: "nowrap",
            }}
          >
            {t("voice.restored")}
          </span>
          <div className="divider" style={{ flex: 1 }} />
        </div>
      )}
      {restoredTurns.map((turn, i) => (
        <div key={`restored-${i}`} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <CustomerBubble text={turn.customer} listeningLabel={t("voice.eyebrow.listening")} />
          {turn.aiText && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div
                style={{
                  maxWidth: "85%",
                  padding: "10px 14px",
                  borderRadius: "14px 14px 14px 4px",
                  background: "var(--bg-panel)",
                  border: "1px solid var(--border-subtle)",
                  fontSize: 14,
                  lineHeight: 1.5,
                  color: "var(--text-primary)",
                }}
              >
                {turn.aiText}
              </div>
            </div>
          )}
        </div>
      ))}
      {restoredTurns.length > 0 && turns.length > 0 && (
        <div className="divider" aria-hidden="true" />
      )}
      {turns.map((turn, i) => (
        <div key={i} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          >
            <CustomerBubble text={turn.customer} listeningLabel={t("voice.eyebrow.listening")} />
          </motion.div>
          <ResponsePanel response={turn.ai} animateText={i === turns.length - 1} />
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
