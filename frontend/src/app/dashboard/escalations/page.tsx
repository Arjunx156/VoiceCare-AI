"use client";

/**
 * Escalation queue — outlined panels for Low/Medium, raised card with a
 * corner badge for Critical/High. Semantic colors only (never --accent for
 * urgency). Polls on an interval with exponential backoff to 60s on errors.
 */

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import { getEscalations, claimTicket, type TicketSummary } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useMotionSafe } from "@/lib/motion";
import { priorityMeta, sentimentMeta } from "@/lib/theme";
import { Badge, Button, EmptyState, LanguageLabel, LoadingBlock, Panel, PriorityBadge } from "@/components/ui";

const POLL_INTERVAL_MS = 20_000;

// "Raised" means Critical or High — needs attention now
function isRaised(priority: string) {
  return priority === "Critical" || priority === "High";
}

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<TicketSummary[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);
  const [claiming, setClaiming]       = useState<string | null>(null);
  const { entry } = useMotionSafe();

  const handleClaim = useCallback(async (ticketId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setClaiming(ticketId);
    try {
      await claimTicket(ticketId);
      setEscalations((prev) => prev.filter((t) => t.ticket_id !== ticketId));
    } catch (err) {
      console.error("Failed to claim ticket:", err);
    } finally {
      setClaiming(null);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    let controller = new AbortController();
    // 20 s baseline. At 5 s this queue was the heaviest continuous load on a
    // single-worker backend and slowed down every other tab the admin opened.
    let pollDelay = POLL_INTERVAL_MS; // backs off to 60 s on errors
    let timeoutId: ReturnType<typeof setTimeout>;
    let hasLoadedOnce = false;

    async function load() {
      if (!mounted) return;
      controller = new AbortController();
      try {
        const data = await getEscalations(hasLoadedOnce ? controller.signal : undefined);
        if (mounted) {
          setEscalations(data);
          setError(null);
          pollDelay = POLL_INTERVAL_MS; // reset backoff on success
          hasLoadedOnce = true;
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") return;
        console.error("Failed to load escalations:", err);
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load escalations");
          pollDelay = Math.min(pollDelay * 2, 60_000); // back off up to 60 s
          hasLoadedOnce = true;
        }
      } finally {
        if (mounted) {
          setLoading(false);
          // Schedule next poll with current (possibly backed-off) delay
          timeoutId = setTimeout(load, pollDelay);
        }
      }
    }
    load();

    return () => {
      mounted = false;
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, []);

  if (loading && escalations.length === 0) {
    return <LoadingBlock label="Loading escalations" />;
  }

  if (error && escalations.length === 0) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: 256, gap: 10 }}>
        <p style={{ fontSize: 14, fontWeight: 600, color: "var(--error)" }}>Unable to load escalations</p>
        <p style={{ fontSize: 12, color: "var(--text-muted)", maxWidth: 300, textAlign: "center" }}>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      {/* Header */}
      <motion.div {...entry()}>
        <span className="eyebrow">Escalation queue</span>
        <h1 className="page-title">
          {escalations.length > 0
            ? `${escalations.length} ticket${escalations.length !== 1 ? "s" : ""} need${escalations.length === 1 ? "s" : ""} you`
            : "All clear"}
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 10, maxWidth: "58ch" }}>
          Tickets the pipeline stopped on and handed to a human. Claim one to take it off the queue.
        </p>
      </motion.div>

      {escalations.length === 0 ? (
        <Panel>
          <EmptyState
            icon={CheckCircle2}
            title="No pending escalations"
            hint="The pipeline is resolving everything on its own right now."
          />
        </Panel>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 12 }}>
          {escalations.map((ticket, i) => {
            const raised = isRaised(ticket.priority);
            const meta = priorityMeta(ticket.priority);
            return (
              <motion.div key={ticket.ticket_id} {...entry(Math.min(i * 0.03, 0.18))}>
                <Link href={`/dashboard/tickets/${ticket.ticket_id}`} style={{ textDecoration: "none", display: "block" }}>
                  <div
                    className="panel-hover"
                    style={{
                      borderRadius: "var(--radius-container)",
                      padding: "20px 22px",
                      position: "relative",
                      overflow: "hidden",
                      border: `1px solid ${raised ? meta.bg : "var(--border-subtle)"}`,
                      background: raised ? "var(--bg-panel-raised)" : "var(--bg-panel)",
                      cursor: "pointer",
                    }}
                  >
                    {/* Corner badge for raised cards */}
                    {raised && (
                      <div
                        style={{
                          position: "absolute",
                          top: 0, right: 0,
                          padding: "5px 11px",
                          borderRadius: "0 12px 0 10px",
                          fontFamily: "var(--font-mono)",
                          fontSize: 10,
                          fontWeight: 500,
                          letterSpacing: "0.08em",
                          background: meta.bg,
                          color: meta.fg,
                          textTransform: "uppercase",
                        }}
                      >
                        {ticket.priority}
                      </div>
                    )}

                    {/* Eyebrow + name */}
                    <span className="eyebrow" style={{ marginBottom: 5 }}>
                      {ticket.ticket_type || "support"}
                    </span>
                    <p style={{ fontSize: 16, fontWeight: 600, letterSpacing: "-0.015em", color: "var(--text-primary)" }}>
                      {ticket.user_name}
                    </p>
                    <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                      {ticket.phone} · <LanguageLabel language={ticket.language} />
                    </p>

                    <div style={{ height: 1, background: "var(--border-hairline)", margin: "14px 0" }} />

                    <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                      {ticket.summary || `${ticket.ticket_type} issue`}
                    </p>

                    {/* Footer */}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 14 }}>
                      <div style={{ display: "flex", gap: 8 }}>
                        {/* Priority pill — raised cards already carry the corner badge */}
                        {!raised && <PriorityBadge priority={ticket.priority} />}
                        {ticket.sentiment && (
                          <Badge meta={sentimentMeta(ticket.sentiment)}>{ticket.sentiment}</Badge>
                        )}
                      </div>
                      <span className="mono" style={{ fontSize: 10, color: "var(--text-muted)" }}>
                        {formatDate(ticket.created_at)}
                      </span>
                    </div>

                    {/* Claim button */}
                    <div style={{ marginTop: 12 }}>
                      {ticket.assigned_to ? (
                        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                          Claimed by {ticket.assigned_to}
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => handleClaim(ticket.ticket_id, e)}
                          isLoading={claiming === ticket.ticket_id}
                          style={{ fontSize: 11, padding: "5px 14px" }}
                        >
                          {claiming === ticket.ticket_id ? "Claiming…" : "Claim"}
                        </Button>
                      )}
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
