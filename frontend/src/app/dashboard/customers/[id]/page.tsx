"use client";

/**
 * CommerceMind VoiceCare AI — Customer 360 profile
 * Header + orders, ticket history, and a sentiment timeline strip.
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { getCustomerProfile, type CustomerProfile } from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  Escalated: "var(--status-high)",
  Resolved:  "var(--status-low)",
  Open:      "var(--status-calm)",
  "In Progress": "var(--status-medium)",
  Closed:    "var(--text-muted)",
};

const SENTIMENT_COLOR: Record<string, string> = {
  Calm: "var(--status-low)",
  Confused: "var(--status-medium)",
  Dissatisfied: "var(--status-medium)",
  Angry: "var(--status-high)",
  "Very Angry": "var(--status-critical)",
  "High-risk Escalation": "var(--status-critical)",
};

export default function CustomerProfilePage() {
  const params = useParams();
  const customerId = params.id as string;

  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setProfile(await getCustomerProfile(customerId));
      } catch (err) {
        console.error("Failed to load customer:", err);
      } finally {
        setLoading(false);
      }
    }
    if (customerId) load();
  }, [customerId]);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 256 }}>
        <div style={{
          width: 28, height: 28, borderRadius: "50%",
          border: "2px solid var(--border-subtle)", borderTopColor: "var(--accent)",
          animation: "spin 1s linear infinite",
        }} />
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      </div>
    );
  }

  if (!profile) {
    return (
      <div style={{ textAlign: "center", padding: "80px 0" }}>
        <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Customer not found</p>
        <Link href="/dashboard/customers" style={{ fontSize: 13, color: "var(--accent)", marginTop: 8, display: "inline-block" }}>
          Back to customers
        </Link>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      style={{ display: "flex", flexDirection: "column", gap: 24, maxWidth: 860 }}
    >
      {/* Breadcrumb */}
      <nav style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-muted)" }}>
        <Link href="/dashboard/customers" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Customers</Link>
        <span>›</span>
        <span style={{ color: "var(--text-secondary)" }}>{profile.name}</span>
      </nav>

      {/* Header */}
      <div>
        <span className="eyebrow">
          {profile.customer_segment.toUpperCase()} · {profile.preferred_language}
          {profile.customer_code ? ` · ${profile.customer_code}` : ""}
        </span>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>
          {profile.name}
        </h1>
        <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
          {profile.phone}{profile.email ? ` · ${profile.email}` : ""}{profile.city ? ` · ${profile.city}` : ""}
        </p>
      </div>

      {/* Sentiment timeline */}
      {profile.sentiment_timeline.length > 0 && (
        <div className="panel" style={{ padding: "20px 24px" }}>
          <span className="eyebrow">SENTIMENT TIMELINE</span>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
            {profile.sentiment_timeline.map((s, i) => (
              <span
                key={i}
                title={new Date(s.recorded_at).toLocaleString()}
                style={{
                  fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 999,
                  background: "var(--bg-panel-raised)",
                  color: SENTIMENT_COLOR[s.label] || "var(--text-secondary)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                {s.label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Orders */}
      <div className="panel" style={{ padding: "20px 24px" }}>
        <span className="eyebrow">ORDERS ({profile.orders.length})</span>
        {profile.orders.length === 0 ? (
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>No orders on record.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
            {profile.orders.map((o) => (
              <div key={o.order_id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 0", borderBottom: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: 12, color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>
                  {new Date(o.order_date).toLocaleDateString()}
                </span>
                {o.order_number && (
                  <span style={{ fontSize: 12, fontWeight: 600, color: "var(--accent)", fontVariantNumeric: "tabular-nums" }}>
                    {o.order_number}
                  </span>
                )}
                <span style={{ fontSize: 13, color: "var(--text-primary)", flex: 1 }}>{o.status}</span>
                {o.shipment && (
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{o.shipment.status}</span>
                )}
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                  ₹{o.total_amount.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tickets */}
      <div className="panel" style={{ padding: "20px 24px" }}>
        <span className="eyebrow">TICKET HISTORY ({profile.tickets.length})</span>
        {profile.tickets.length === 0 ? (
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>No tickets yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 8 }}>
            {profile.tickets.map((t) => (
              <Link
                key={t.ticket_id}
                href={`/dashboard/tickets/${t.ticket_id}`}
                style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", textDecoration: "none", borderBottom: "1px solid var(--border-subtle)" }}
              >
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{t.ticket_type}</span>
                <span style={{ fontSize: 13, color: "var(--text-primary)", flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {t.summary || "—"}
                </span>
                <span style={{ fontSize: 11, fontWeight: 600, color: STATUS_COLOR[t.status] || "var(--text-secondary)" }}>
                  {t.status}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
