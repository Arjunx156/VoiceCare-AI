"use client";

/**
 * CommerceMind VoiceCare AI — Customers (Customer 360 directory)
 * Searchable list of customers with ticket counts and last contact.
 */

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { getCustomers, type CustomerSummary } from "@/lib/api";

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

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      style={{ display: "flex", flexDirection: "column", gap: 24, maxWidth: 900 }}
    >
      <div>
        <span className="eyebrow">DIRECTORY</span>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>
          Customers
        </h1>
      </div>

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by name, phone, or email…"
        style={{
          width: "100%",
          padding: "11px 16px",
          borderRadius: 12,
          fontSize: 14,
          fontFamily: "var(--font-sans)",
          background: "var(--bg-panel)",
          border: "1px solid var(--border-subtle)",
          color: "var(--text-primary)",
        }}
      />

      {loading ? (
        <p style={{ fontSize: 13, color: "var(--text-muted)", padding: "32px 0", textAlign: "center" }}>
          Loading…
        </p>
      ) : customers.length === 0 ? (
        <p style={{ fontSize: 13, color: "var(--text-muted)", padding: "32px 0", textAlign: "center" }}>
          No customers found.
        </p>
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
                {c.last_contact ? new Date(c.last_contact).toLocaleDateString() : "—"}
              </span>
            </Link>
          ))}
        </div>
      )}
    </motion.div>
  );
}
