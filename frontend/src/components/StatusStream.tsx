"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n/I18nProvider";
import type { MessageKey } from "@/lib/i18n/messages/en";

const STAGE_KEYS: MessageKey[] = [
  "status.stage1",
  "status.stage2",
  "status.stage3",
  "status.stage4",
  "status.stage5",
  "status.stage6",
  "status.stage7",
  "status.stage8",
  "status.stage9",
];

interface StatusStreamProps {
  currentStage: number;
  isComplete: boolean;
  isProcessing: boolean;
  message?: string;
}

function Checkmark() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
      <polyline
        points="2,7 6,11 12,3"
        stroke="#4CAF73"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="check-draw"
      />
    </svg>
  );
}

export default function StatusStream({ currentStage, isComplete, isProcessing, message }: StatusStreamProps) {
  const { t } = useI18n();

  // The status stream is purely a live, in-flight indicator. Once the turn
  // finishes (isProcessing flips false) the completed Q&A lives in the chat
  // transcript instead, so the stream disappears rather than lingering.
  if (!isProcessing) return null;

  return (
    <div className="w-full panel" style={{ padding: "20px 24px" }}>
      <span className="eyebrow">
        {isComplete ? t("status.complete") : t("status.processing")}
      </span>

      <ol style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "10px" }}>
        {STAGE_KEYS.map((key, idx) => {
          const stepNum = idx + 1;
          const isActive = stepNum === currentStage && !isComplete;
          const isDone   = stepNum < currentStage || isComplete;
          const isFuture = !isActive && !isDone;

          return (
            <li
              key={stepNum}
              style={{ display: "flex", alignItems: "center", gap: "12px" }}
            >
              <motion.span
                animate={{
                  color: isDone
                    ? "#4CAF73"
                    : isActive
                    ? "#FF5A2B"
                    : "#3A3A3A",
                }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  fontVariantNumeric: "tabular-nums",
                  width: "24px",
                  flexShrink: 0,
                  letterSpacing: "0.02em",
                }}
              >
                {isDone ? <Checkmark /> : String(stepNum).padStart(2, "0")}
              </motion.span>

              <motion.span
                animate={{
                  opacity: isFuture ? 0.28 : 1,
                  color: isActive ? "#F5F5F5" : isDone ? "#9A9A9A" : "#3A3A3A",
                }}
                transition={{ duration: 0.08, ease: "easeOut", delay: isActive ? 0.08 : 0 }}
                style={{ fontSize: "13px", fontWeight: isActive ? 500 : 400 }}
              >
                {isActive && message ? message : t(key)}
              </motion.span>

              {isActive && (
                <motion.span
                  initial={{ opacity: 0, scaleX: 0 }}
                  animate={{ opacity: 1, scaleX: 1 }}
                  style={{
                    marginLeft: "auto",
                    height: "3px",
                    width: "32px",
                    borderRadius: "999px",
                    background: "#FF5A2B",
                    display: "block",
                    transformOrigin: "left",
                  }}
                />
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
