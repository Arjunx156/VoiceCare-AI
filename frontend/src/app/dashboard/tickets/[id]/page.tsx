"use client";

/**
 * Ticket detail — eyebrow + bold title header, accessible pill tabs, and the
 * details / agent-replay / handoff views. Composition only: the presentation
 * lives in components/tickets/*.
 */

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { SearchX } from "lucide-react";
import {
  getTicketDetail,
  getHandoffNote,
  replyToTicket,
  resolveTicket,
  claimTicket,
  type TicketDetail,
  type HandoffNote,
} from "@/lib/api";
import { useMotionSafe } from "@/lib/motion";
import { EmptyState, LoadingBlock, Tabs } from "@/components/ui";
import { TicketActions } from "@/components/tickets/TicketActions";
import { TicketConversation } from "@/components/tickets/TicketConversation";
import { TicketDetails } from "@/components/tickets/TicketDetails";
import { TicketHandoff } from "@/components/tickets/TicketHandoff";
import { TicketHeader } from "@/components/tickets/TicketHeader";
import { TicketReplay } from "@/components/tickets/TicketReplay";

export default function TicketDetailPage() {
  const params = useParams();
  const ticketId = params.id as string;
  const { entry } = useMotionSafe();

  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [handoff, setHandoff] = useState<HandoffNote | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("detail");

  const [replyText, setReplyText] = useState("");
  const [acting, setActing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(() => {
    return getTicketDetail(ticketId)
      .then(async (data) => {
        setTicket(data);
        if (data.status === "Escalated") {
          try {
            setHandoff(await getHandoffNote(ticketId));
          } catch (err) {
            console.error("Failed to load handoff note:", err);
          }
        }
      })
      .catch((err: unknown) => {
        console.error("Failed to load ticket:", err);
      })
      .finally(() => setLoading(false));
  }, [ticketId]);

  useEffect(() => {
    if (ticketId) void load();
  }, [ticketId, load]);

  async function runAction(action: () => Promise<unknown>, failureMessage: string) {
    if (acting) return;
    setActing(true);
    setActionError(null);
    try {
      await action();
      await load();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : failureMessage);
    } finally {
      setActing(false);
    }
  }

  const handleReply = () => {
    if (!replyText.trim()) return;
    void runAction(async () => {
      await replyToTicket(ticketId, replyText.trim());
      setReplyText("");
    }, "Failed to send reply.");
  };
  const handleClaim = () => void runAction(() => claimTicket(ticketId), "Failed to claim.");
  const handleResolve = () => void runAction(() => resolveTicket(ticketId), "Failed to resolve.");

  if (loading) {
    return <LoadingBlock label="Loading ticket" />;
  }

  if (!ticket) {
    return (
      <EmptyState
        icon={SearchX}
        title="Ticket not found"
        action={
          <Link href="/dashboard/tickets" style={{ fontSize: 13, color: "var(--accent)" }}>
            Back to tickets
          </Link>
        }
      />
    );
  }

  const tabs = [
    { value: "detail", label: "Details" },
    { value: "replay", label: "Agent Replay" },
    ...(ticket.status === "Escalated" && handoff ? [{ value: "handoff", label: "Handoff Note" }] : []),
  ];

  return (
    <motion.div {...entry()} style={{ display: "flex", flexDirection: "column", gap: 24, maxWidth: 820 }}>
      <TicketHeader ticket={ticket} ticketId={ticketId} />

      <Tabs tabs={tabs} value={activeTab} onChange={setActiveTab}>
        {activeTab === "detail" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <TicketDetails ticket={ticket} />
            <TicketConversation messages={ticket.messages} />
            <TicketActions
              status={ticket.status}
              replyText={replyText}
              onReplyTextChange={setReplyText}
              acting={acting}
              actionError={actionError}
              onReply={handleReply}
              onClaim={handleClaim}
              onResolve={handleResolve}
            />
          </div>
        )}
        {activeTab === "replay" && <TicketReplay trace={ticket.agent_trace} />}
        {activeTab === "handoff" && handoff && <TicketHandoff handoff={handoff} />}
      </Tabs>
    </motion.div>
  );
}
