"use client";

import { motion } from "framer-motion";
import ResponsePanel from "@/components/ResponsePanel";
import { useI18n } from "@/lib/i18n/I18nProvider";
import type { ConversationTurn } from "@/hooks/useVoiceInteraction";

/**
 * The full visible conversation for the current session: each completed turn
 * shows what the customer said followed by the assistant's response. Stays on
 * screen across mic presses so customers can see the ongoing conversation.
 */
export default function ConversationThread({ turns }: { turns: ConversationTurn[] }) {
  const { t } = useI18n();
  if (turns.length === 0) return null;

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 16, marginTop: 16 }}>
      {turns.map((turn, i) => (
        <div key={i} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            style={{ display: "flex", justifyContent: "flex-end" }}
          >
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
              {turn.customer?.trim() || `🎤 ${t("voice.eyebrow.listening")}`}
            </div>
          </motion.div>
          <ResponsePanel response={turn.ai} />
        </div>
      ))}
    </div>
  );
}
