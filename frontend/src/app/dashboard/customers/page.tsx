"use client";

/**
 * CommerceMind VoiceCare AI — Customers (Customer 360 directory)
 * Searchable list of customers with ticket counts and last contact.
 */

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Users } from "lucide-react";
import { getCustomers, type CustomerSummary } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useMotionSafe } from "@/lib/motion";
import { EmptyState, SkeletonList } from "@/components/ui";

const SEGMENT_COLOR: Record<string, string> = {
  Premium: "var(--status-medium)",
  Regular: "var(--text-secondary)",
  New:     "var(--status-low)",
};

export default function CustomersPage() {
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (q: string) => {
    setLoading(true);
    try {
      setCustomers(await getCustomers(q || undefined));
    } catch (err) {
      console.error("Failed to load customers:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounce the search input.
  useEffect(() => {
    const t = setTimeout(() => load(search), 300);
    return () => clearTimeout(t);
  }, [search, load]);

  const { entry } = useMotionSafe();

  return (
    <motion.div
      {...entry()}
      style={{ display: "flex", flexDirection: "column", gap: 24, maxWidth: 900 }}
    >
      <div>
        <span className="eyebrow">DIRECTORY</span>
        <h1 className="page-title">Customers</h1>
      </div>

      <input
        className="text-input"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by name, phone, or email…"
        aria-label="Search customers"
        style={{ background: "var(--bg-panel)", borderRadius: 12 }}
      />

      {loading ? (
        <SkeletonList rows={6} label="Loading customers" />
      ) : customers.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No customers found"
          hint={search ? "Try a different name, phone, or email." : "Customers appear after their first voice query."}
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {customers.map((c) => (
            <Link
              key={c.user_id}
              href={`/dashboard/customers/${c.customer_code || c.user_id}`}
              style={{
                display: "flex", alignItems: "center", gap: 16,
                padding: "14px 16px", borderRadius: 12, textDecoration: "none",
                border: "1px solid var(--border-subtle)", background: "var(--bg-panel)",
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>
                  {c.name}
                  {c.customer_code && (
                    <span style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", marginLeft: 8, fontVariantNumeric: "tabular-nums" }}>
                      {c.customer_code}
                    </span>
                  )}
                </p>
                <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  {c.phone}{c.city ? ` · ${c.city}` : ""}
                </p>
              </div>
              <span style={{ fontSize: 11, fontWeight: 600, color: SEGMENT_COLOR[c.customer_segment] || "var(--text-secondary)" }}>
                {c.customer_segment}
              </span>
              <span style={{ fontSize: 12, color: "var(--text-secondary)", width: 90, textAlign: "right" }}>
                {c.ticket_count} ticket{c.ticket_count === 1 ? "" : "s"}
              </span>
              <span style={{ fontSize: 12, color: "var(--text-muted)", width: 110, textAlign: "right" }}>
                {c.last_contact ? formatDate(c.last_contact) : "—"}
              </span>
            </Link>
          ))}
        </div>
      )}
    </motion.div>
  );
}
