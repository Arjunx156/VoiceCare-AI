"use client";

import { motion } from "framer-motion";
import { ListX } from "lucide-react";
import { EmptyState, Panel } from "@/components/ui";
import { useMotionSafe } from "@/lib/motion";
import type { AgentTraceStep } from "@/lib/api";

/** Numbered vertical timeline of the 9-agent pipeline decisions. */
export function TicketReplay({ trace }: { trace: AgentTraceStep[] }) {
  const { entry } = useMotionSafe();

  return (
    <Panel style={{ padding: 24 }}>
      <span className="eyebrow">AGENT DECISION REPLAY</span>
      <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 24 }}>
        Pipeline Trace
      </h2>
      {trace.length > 0 ? (
        <ol style={{ listStyle: "none" }}>
          {trace.map((step, i) => (
            <motion.li
              key={i}
              {...entry(Math.min(i * 0.07, 0.6))}
              style={{ display: "flex", gap: 16, paddingBottom: 24, position: "relative" }}
            >
              {i < trace.length - 1 && (
                <div
                  aria-hidden="true"
                  style={{
                    position: "absolute",
                    left: 15,
                    top: 32,
                    width: 1,
                    bottom: 0,
                    background: "var(--border-subtle)",
                  }}
                />
              )}

              <div
                aria-hidden="true"
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: "var(--bg-panel-raised)",
                  border: "1px solid var(--border-raised)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  fontSize: 11,
                  fontWeight: 700,
                  fontVariantNumeric: "tabular-nums",
                  color: "var(--accent)",
                }}
              >
                {String(step.stage_number).padStart(2, "0")}
              </div>

              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
                  {step.agent_name}
                </p>
                {step.decision && (
                  <p style={{ fontSize: 12, color: "var(--accent)", marginTop: 3 }}>
                    Decision: {step.decision}
                  </p>
                )}
                {step.reasoning && (
                  <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 3, lineHeight: 1.5 }}>
                    {step.reasoning}
                  </p>
                )}
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4, lineHeight: 1.5 }}>
                  {step.output_summary}
                </p>
                {step.duration_ms && (
                  <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, fontVariantNumeric: "tabular-nums" }}>
                    {step.duration_ms.toFixed(0)} ms
                  </p>
                )}
              </div>
            </motion.li>
          ))}
        </ol>
      ) : (
        <EmptyState icon={ListX} title="No agent trace available" hint="This ticket predates trace recording." />
      )}
    </Panel>
  );
}
