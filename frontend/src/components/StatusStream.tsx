"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n/I18nProvider";
import type { MessageKey } from "@/lib/i18n/messages/en";
import type { StageMap } from "@/hooks/useVoiceInteraction";

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
  stages: StageMap;
  isComplete: boolean;
  isProcessing: boolean;
  totalDurationMs?: number | null;
}

/** Milliseconds as a compact, readable figure: 42 ms, 380 ms, 1.24 s. */
function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
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

export default function StatusStream({
  currentStage,
  stages,
  isComplete,
  isProcessing,
  totalDurationMs,
}: StatusStreamProps) {
  const { t } = useI18n();

  // Stays mounted after the turn finishes so the per-agent timings remain
  // readable — they are the point of this panel, and unmounting on completion
  // would flash them away at the exact moment they became complete.
  if (!isProcessing && !isComplete) return null;

  const activeKey = STAGE_KEYS[Math.min(Math.max(currentStage, 1), 9) - 1];

  return (
    <div className="w-full panel" style={{ padding: "20px 24px" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
        <span className="eyebrow">
          {isComplete ? t("status.complete") : t("status.processing")}
        </span>
        {totalDurationMs != null && (
          <span
            style={{
              marginLeft: "auto",
              fontSize: 12,
              fontWeight: 600,
              color: "#4CAF73",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {formatDuration(totalDurationMs)}
          </span>
        )}
      </div>

      {/* Screen readers hear only the current stage, not every list repaint */}
      <span className="sr-only" aria-live="polite">
        {t(activeKey)}
      </span>

      <ol style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "10px" }}>
        {STAGE_KEYS.map((key, idx) => {
          const stepNum = idx + 1;
          const stage   = stages[stepNum];
          // Driven by what the server actually reported for each stage, so the
          // concurrent pair (3 and 4) can both show as running at once.
          const isActive = stage?.status === "running";
          const isDone   = stage?.status === "done";
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
                {t(key)}
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

              {/* != null, not truthiness: agent 6 is deterministic and finishes
                  in well under a millisecond, so a real 0 must still render. */}
              {isDone && stage?.durationMs != null && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.2, ease: "easeOut" }}
                  style={{
                    marginLeft: "auto",
                    fontSize: "11px",
                    color: "var(--text-muted)",
                    fontVariantNumeric: "tabular-nums",
                    flexShrink: 0,
                  }}
                >
                  {formatDuration(stage.durationMs)}
                </motion.span>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
