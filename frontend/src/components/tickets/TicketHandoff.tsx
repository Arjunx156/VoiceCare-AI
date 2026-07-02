"use client";

import { Panel } from "@/components/ui";
import type { HandoffNote } from "@/lib/api";

/** Auto-generated escalation brief for human agents. */
export function TicketHandoff({ handoff }: { handoff: HandoffNote }) {
  const facts = [
    { label: "CUSTOMER",  value: handoff.customer_name },
    { label: "PHONE",     value: handoff.customer_phone },
    { label: "LANGUAGE",  value: handoff.language },
    { label: "SENTIMENT", value: handoff.sentiment, warn: true },
  ];

  const sections = [
    { label: "ISSUE SUMMARY",          value: handoff.issue_summary },
    { label: "ESCALATION REASON",      value: handoff.escalation_reason, warn: true },
    { label: "AI ATTEMPTED RESOLUTION", value: handoff.ai_attempted_resolution },
    { label: "RECOMMENDED NEXT STEPS", value: handoff.recommended_next_steps, accent: true },
  ];

  return (
    <Panel style={{ padding: 24 }}>
      <span className="eyebrow">AUTO-GENERATED HANDOFF NOTE</span>
      <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 24 }}>
        Escalation Brief
      </h2>

      <div className="grid-half" style={{ gap: 10, marginBottom: 20 }}>
        {facts.map((fact) => (
          <div key={fact.label} style={{ background: "var(--bg-panel-raised)", borderRadius: 12, padding: "12px 14px" }}>
            <span className="eyebrow" style={{ marginBottom: 4 }}>{fact.label}</span>
            <p style={{ fontSize: 14, fontWeight: 600, color: fact.warn ? "var(--status-high)" : "var(--text-primary)" }}>
              {fact.value}
            </p>
          </div>
        ))}
      </div>

      {sections.map((section, i) => (
        <div key={section.label}>
          {i > 0 && <div className="divider" style={{ margin: "16px 0" }} />}
          <span className="eyebrow">{section.label}</span>
          <p
            style={{
              fontSize: 14,
              lineHeight: 1.6,
              color: section.warn
                ? "var(--status-high)"
                : section.accent
                ? "var(--accent)"
                : "var(--text-secondary)",
            }}
          >
            {section.value}
          </p>
        </div>
      ))}
    </Panel>
  );
}
