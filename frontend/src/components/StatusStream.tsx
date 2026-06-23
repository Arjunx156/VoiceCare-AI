"use client";

/**
 * CommerceMind VoiceCare AI — Status Stream v2
 * Design brief: numbered list 01–09, muted → accent numeral on active,
 * staggered label fade, checkmark draw on complete.
 */

import { motion, AnimatePresence } from "framer-motion";

const STAGES: { label: string }[] = [
  { label: "Receiving audio" },
  { label: "Understanding intent" },
  { label: "Looking up order" },
  { label: "Retrieving policy" },
  { label: "Determining resolution" },
  { label: "Checking escalation" },
  { label: "Composing response" },
  { label: "Converting to speech" },
  { label: "Creating ticket" },
];

interface StatusStreamProps {
  currentStage: number;
  isComplete: boolean;
  message?: string;
}

// SVG checkmark draw-on
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

export default function StatusStream({ currentStage, isComplete, message }: StatusStreamProps) {
  if (currentStage === 0 && !isComplete) return null;

  return (
    <div className="w-full panel" style={{ padding: "20px 24px" }}>
      {/* Eyebrow */}
      <span className="eyebrow">
        {isComplete ? "COMPLETE" : "PROCESSING"}
      </span>

      {/* Step list */}
      <ol style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "10px" }}>
        {STAGES.map((stage, idx) => {
          const stepNum = idx + 1;
          const isActive = stepNum === currentStage && !isComplete;
          const isDone   = stepNum < currentStage || isComplete;
          const isFuture = !isActive && !isDone;

          return (
            <li
              key={stepNum}
              style={{ display: "flex", alignItems: "center", gap: "12px" }}
            >
              {/* Numeral */}
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

              {/* Label — fades in 80ms after numeral shift */}
              <motion.span
                animate={{
                  opacity: isFuture ? 0.28 : 1,
                  color: isActive ? "#F5F5F5" : isDone ? "#9A9A9A" : "#3A3A3A",
                }}
                transition={{ duration: 0.08, ease: "easeOut", delay: isActive ? 0.08 : 0 }}
                style={{ fontSize: "13px", fontWeight: isActive ? 500 : 400 }}
              >
                {isActive && message ? message : stage.label}
              </motion.span>

              {/* Active pill progress indicator */}
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
