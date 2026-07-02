"use client";

import Link from "next/link";
import { PriorityBadge, StatusBadge } from "@/components/ui";
import type { TicketDetail } from "@/lib/api";

const crumbLink: React.CSSProperties = { color: "var(--text-muted)", textDecoration: "none" };

/** Breadcrumb + eyebrow/title header + priority/status badges. */
export function TicketHeader({ ticket, ticketId }: { ticket: TicketDetail; ticketId: string }) {
  return (
    <>
      <nav aria-label="Breadcrumb" style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-muted)" }}>
        <Link href="/dashboard" style={crumbLink}>Dashboard</Link>
        <span aria-hidden="true">›</span>
        <Link href="/dashboard/tickets" style={crumbLink}>Tickets</Link>
        <span aria-hidden="true">›</span>
        <span style={{ color: "var(--text-secondary)" }} aria-current="page">
          {ticket.ticket_number ?? ticketId.substring(0, 8) + "…"}
        </span>
      </nav>

      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
        <div>
          <span className="eyebrow">{ticket.ticket_type || "SUPPORT"}</span>
          <h1 className="page-title">{ticket.user_name}</h1>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
            {ticket.phone} · {ticket.language}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, flexShrink: 0, paddingTop: 4 }}>
          <PriorityBadge priority={ticket.priority} />
          <StatusBadge status={ticket.status} />
        </div>
      </div>
    </>
  );
}
