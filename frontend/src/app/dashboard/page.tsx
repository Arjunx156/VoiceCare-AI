"use client";

/**
 * CommerceMind VoiceCare AI — Dashboard Overview Page
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getAnalytics, getEscalations, type AnalyticsOverview, type TicketSummary } from "@/lib/api";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [escalations, setEscalations] = useState<TicketSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [analyticsData, escalationsData] = await Promise.all([
          getAnalytics(),
          getEscalations(),
        ]);
        setAnalytics(analyticsData);
        setEscalations(escalationsData);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 rounded-full"
          style={{ border: "2px solid var(--border-subtle)", borderTopColor: "var(--primary)" }}
        />
      </div>
    );
  }

  const stats = [
    { label: "Total Tickets", value: analytics?.total_tickets || 0, icon: "🎫", color: "var(--primary)" },
    { label: "Open", value: analytics?.open_tickets || 0, icon: "📂", color: "var(--info)" },
    { label: "Escalated", value: analytics?.escalated_tickets || 0, icon: "🚨", color: "var(--error)" },
    { label: "Resolved", value: analytics?.resolved_tickets || 0, icon: "✅", color: "var(--success)" },
    { label: "Resolution Rate", value: `${analytics?.resolution_rate || 0}%`, icon: "📊", color: "var(--accent)" },
    { label: "Escalation Rate", value: `${analytics?.escalation_rate || 0}%`, icon: "⚠️", color: "var(--warning)" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Dashboard
        </h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
          Live overview of VoiceCare AI support operations
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{stat.icon}</span>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {stat.label}
              </span>
            </div>
            <p className="text-2xl font-bold" style={{ color: stat.color }}>
              {stat.value}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Language */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Tickets by Language
          </h3>
          {analytics && Object.entries(analytics.tickets_by_language).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(analytics.tickets_by_language).map(([lang, count]) => (
                <div key={lang} className="flex items-center gap-3">
                  <span className="text-xs w-20" style={{ color: "var(--text-secondary)" }}>
                    {lang}
                  </span>
                  <div className="flex-1 h-2 rounded-full" style={{ background: "var(--border-subtle)" }}>
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: "var(--primary)" }}
                      initial={{ width: 0 }}
                      animate={{
                        width: `${(count / (analytics.total_tickets || 1)) * 100}%`,
                      }}
                      transition={{ duration: 0.8 }}
                    />
                  </div>
                  <span className="text-xs font-medium w-8 text-right" style={{ color: "var(--text-primary)" }}>
                    {count}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>No data yet</p>
          )}
        </div>

        {/* Escalation Queue */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            🚨 Escalation Queue ({escalations.length})
          </h3>
          {escalations.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {escalations.slice(0, 5).map((ticket) => (
                <div
                  key={ticket.ticket_id}
                  className="flex items-center gap-3 p-3 rounded-lg transition-all hover:opacity-80"
                  style={{ background: "var(--bg-card)" }}
                >
                  <span className="status-dot escalated" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate" style={{ color: "var(--text-primary)" }}>
                      {ticket.user_name}
                    </p>
                    <p className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
                      {ticket.summary || ticket.ticket_type}
                    </p>
                  </div>
                  <span
                    className="text-xs px-2 py-1 rounded-full"
                    style={{
                      background: ticket.priority === "Critical" ? "rgba(239,68,68,0.15)" : "rgba(245,158,11,0.15)",
                      color: ticket.priority === "Critical" ? "var(--error)" : "var(--warning)",
                    }}
                  >
                    {ticket.priority}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-2xl mb-2">🎉</p>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                No pending escalations
              </p>
            </div>
          )}
        </div>
      </div>

      {/* By Category */}
      {analytics && Object.entries(analytics.tickets_by_category).length > 0 && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Tickets by Category
          </h3>
          <div className="flex flex-wrap gap-3">
            {Object.entries(analytics.tickets_by_category).map(([cat, count]) => (
              <div
                key={cat}
                className="px-4 py-3 rounded-xl text-center"
                style={{ background: "var(--bg-card)" }}
              >
                <p className="text-lg font-bold" style={{ color: "var(--accent)" }}>
                  {count}
                </p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {cat}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
