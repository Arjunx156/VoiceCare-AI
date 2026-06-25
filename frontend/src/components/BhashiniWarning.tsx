"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n/I18nProvider";

export default function BhashiniWarning({ onClose }: { onClose: () => void }) {
  const { t } = useI18n();

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      style={{ width: "100%", maxWidth: 560, padding: "12px 24px 0" }}
    >
      <div
        style={{
          borderRadius: 12,
          padding: "12px 16px",
          fontSize: 13,
          display: "flex",
          alignItems: "flex-start",
          gap: 10,
          background: "rgba(212, 160, 23, 0.10)",
          border: "1px solid rgba(212, 160, 23, 0.3)",
          color: "#D4A017",
        }}
      >
        <span style={{ fontSize: "1rem", flexShrink: 0 }}>⚠</span>
        <span style={{ flex: 1, lineHeight: 1.5 }}>
          <strong>{t("warning.title")}</strong> {t("warning.body")}
        </span>
        <button
          onClick={onClose}
          style={{ opacity: 0.5, flexShrink: 0, background: "none", border: "none", color: "inherit", cursor: "pointer" }}
        >
          ✕
        </button>
      </div>
    </motion.div>
  );
}
