"use client";

import { motion } from "framer-motion";
import { type VoiceQueryResponse } from "@/lib/api";
import { useI18n } from "@/lib/i18n/I18nProvider";

export default function ResponsePanel({ response }: { response: VoiceQueryResponse }) {
  const { t } = useI18n();

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
        {response.response_text}
      </p>
      {response.policy_reference && (
        <p style={{ fontSize: 12, marginTop: 12, color: "var(--text-secondary)", fontStyle: "italic" }}>
          📋 {response.policy_reference.substring(0, 120)}…
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
        <span>{t("response.ticket")} {response.ticket_id?.substring(0, 8)}…</span>
        <span>{t("response.confidence")} {(response.confidence_score * 100).toFixed(0)}%</span>
        <span>{response.sentiment}</span>
      </div>
    </motion.div>
  );
}
