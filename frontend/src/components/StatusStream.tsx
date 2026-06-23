"use client";

/**
 * CommerceMind VoiceCare AI — Pipeline Status Stream
 * Animated real-time status display during pipeline processing.
 */

import { motion, AnimatePresence } from "framer-motion";

const STAGE_LABELS: Record<number, { label: string; icon: string }> = {
  1: { label: "Listening...", icon: "🎙️" },
  2: { label: "Understanding your issue...", icon: "🧠" },
  3: { label: "Checking your order...", icon: "📦" },
  4: { label: "Finding the right policy...", icon: "📋" },
  5: { label: "Determining resolution...", icon: "⚖️" },
  6: { label: "Checking escalation rules...", icon: "🔍" },
  7: { label: "Preparing response...", icon: "💬" },
  8: { label: "Converting to speech...", icon: "🔊" },
  9: { label: "Creating your ticket...", icon: "🎫" },
};

interface StatusStreamProps {
  currentStage: number;
  isComplete: boolean;
  message?: string;
}

export default function StatusStream({
  currentStage,
  isComplete,
  message,
}: StatusStreamProps) {
  return (
    <div className="w-full max-w-md mx-auto">
      <AnimatePresence mode="wait">
        {!isComplete && currentStage > 0 && (
          <motion.div
            key={currentStage}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="glass-card px-6 py-4"
          >
            <div className="flex items-center gap-4">
              {/* Animated spinner */}
              <div className="relative w-10 h-10 flex-shrink-0">
                <motion.div
                  className="absolute inset-0 rounded-full"
                  style={{
                    border: "2px solid rgba(99, 102, 241, 0.2)",
                    borderTopColor: "#6366F1",
                  }}
                  animate={{ rotate: 360 }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                />
                <span className="absolute inset-0 flex items-center justify-center text-lg">
                  {STAGE_LABELS[currentStage]?.icon || "⏳"}
                </span>
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                  {message || STAGE_LABELS[currentStage]?.label || "Processing..."}
                </p>
                <div className="mt-2 flex gap-1.5">
                  {Array.from({ length: 9 }, (_, i) => (
                    <motion.div
                      key={i}
                      className="h-1 rounded-full flex-1"
                      style={{
                        background:
                          i + 1 <= currentStage
                            ? "var(--primary)"
                            : "var(--border-subtle)",
                      }}
                      initial={i + 1 === currentStage ? { scaleX: 0 } : {}}
                      animate={i + 1 === currentStage ? { scaleX: 1 } : {}}
                      transition={{ duration: 0.5 }}
                    />
                  ))}
                </div>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                  Step {currentStage} of 9
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {isComplete && (
          <motion.div
            key="complete"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card px-6 py-4 text-center"
            style={{ borderColor: "rgba(16, 185, 129, 0.3)" }}
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 200 }}
              className="text-3xl mb-2"
            >
              ✅
            </motion.div>
            <p className="text-sm font-medium" style={{ color: "var(--success)" }}>
              Response ready!
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
