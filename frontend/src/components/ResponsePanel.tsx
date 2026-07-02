"use client";

import { motion } from "framer-motion";
import { FileText } from "lucide-react";
import { type VoiceQueryResponse } from "@/lib/api";
import { useI18n } from "@/lib/i18n/I18nProvider";
import { useTypewriter } from "@/hooks/useTypewriter";

export default function ResponsePanel({
  response,
  animateText = false,
}: {
  response: VoiceQueryResponse;
  animateText?: boolean;
}) {
  const { t } = useI18n();
  const shownText = useTypewriter(response.response_text ?? "", animateText);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="panel"
      style={{ width: "100%", marginTop: 16, padding: "20px 24px" }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <span className="eyebrow" style={{ marginBottom: 0 }}>
          {response.intent.replace(/_/g, " ")}
        </span>
        <span
          style={{
            marginLeft: "auto",
            fontSize: 11,
            fontWeight: 600,
            padding: "3px 10px",
            borderRadius: 999,
            background: response.is_escalated ? "rgba(229,57,53,0.12)" : "rgba(76,175,115,0.12)",
            color: response.is_escalated ? "var(--status-high)" : "var(--status-low)",
          }}
        >
          {response.is_escalated ? t("response.escalated") : t("response.resolved")}
        </span>
      </div>
      <div className="divider" style={{ marginBottom: 14 }} />
      <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--text-primary)" }}>
        {shownText}
      </p>
      {response.policy_reference && (
        <p
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 6,
            fontSize: 12,
            marginTop: 12,
            color: "var(--text-secondary)",
            fontStyle: "italic",
          }}
        >
          <FileText size={13} strokeWidth={1.75} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />
          <span>{response.policy_reference.substring(0, 120)}…</span>
        </p>
      )}
      <div
        style={{
          display: "flex",
          gap: 16,
          marginTop: 14,
          fontSize: 12,
          color: "var(--text-muted)",
        }}
      >
        {/* Only claim a ticket exists when this turn actually persisted one
            (ticket_created is absent on older responses — treat as created). */}
        {response.ticket_created !== false && (response.ticket_number || response.ticket_id) && (
          <span>{t("response.ticket")} {response.ticket_number ?? response.ticket_id.substring(0, 8) + "…"}</span>
        )}
        {response.confidence_score != null && (
          <span>{t("response.confidence")} {(response.confidence_score * 100).toFixed(0)}%</span>
        )}
        <span>{response.sentiment}</span>
      </div>
    </motion.div>
  );
}
