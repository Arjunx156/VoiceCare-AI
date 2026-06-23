"use client";

/**
 * CommerceMind VoiceCare AI — Analytics Page
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { getAnalytics, type AnalyticsOverview } from "@/lib/api";

const COLORS = ["#4F46E5", "#06B6D4", "#8B5CF6", "#10B981", "#F59E0B", "#EF4444", "#EC4899", "#3B82F6"];

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setAnalytics(await getAnalytics());
      } catch (err) {
        console.error("Failed to load analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 rounded-full"
          style={{ border: "2px solid var(--border-subtle)", borderTopColor: "var(--primary)" }}
        />
      </div>
    );
  }

  if (!analytics || analytics.total_tickets === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>Analytics</h1>
        <div className="glass-card text-center py-16">
          <p className="text-4xl mb-4">📊</p>
          <p className="text-lg font-medium" style={{ color: "var(--text-primary)" }}>No data yet</p>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Start processing voice queries to see analytics
          </p>
        </div>
      </div>
    );
  }

  const langData = Object.entries(analytics.tickets_by_language).map(([name, value]) => ({ name, value }));
  const catData = Object.entries(analytics.tickets_by_category).map(([name, value]) => ({ name, value }));
  const priData = Object.entries(analytics.tickets_by_priority).map(([name, value]) => ({ name, value }));
  const sentData = Object.entries(analytics.tickets_by_sentiment).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>Analytics</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
          Ticket insights across languages, categories, and sentiment
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Resolution Rate", value: `${analytics.resolution_rate}%`, color: "var(--success)" },
          { label: "Escalation Rate", value: `${analytics.escalation_rate}%`, color: "var(--error)" },
          { label: "Total Tickets", value: analytics.total_tickets, color: "var(--primary)" },
          { label: "Open Now", value: analytics.open_tickets, color: "var(--warning)" },
        ].map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card p-4 text-center"
          >
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>{s.label}</p>
            <p className="text-2xl font-bold mt-1" style={{ color: s.color }}>{s.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Language */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Tickets by Language
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={langData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
              <XAxis dataKey="name" tick={{ fill: "#94A3B8", fontSize: 11 }} />
              <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: "#1A1A2E", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8, color: "#F8FAFC" }}
              />
              <Bar dataKey="value" fill="#4F46E5" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* By Category (Pie) */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Tickets by Category
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={catData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
              >
                {catData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#1A1A2E", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8, color: "#F8FAFC" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* By Priority */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Tickets by Priority
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={priData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
              <XAxis type="number" tick={{ fill: "#94A3B8", fontSize: 11 }} />
              <YAxis dataKey="name" type="category" tick={{ fill: "#94A3B8", fontSize: 11 }} width={60} />
              <Tooltip
                contentStyle={{ background: "#1A1A2E", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8, color: "#F8FAFC" }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {priData.map((entry, i) => (
                  <Cell key={i} fill={
                    entry.name === "Critical" ? "#EF4444" :
                    entry.name === "High" ? "#F59E0B" :
                    entry.name === "Medium" ? "#3B82F6" : "#10B981"
                  } />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* By Sentiment */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Sentiment Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={sentData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                label
              >
                {sentData.map((entry, i) => (
                  <Cell key={i} fill={
                    entry.name === "Angry" || entry.name === "Very Angry" ? "#EF4444" :
                    entry.name === "Negative" ? "#F59E0B" : "#10B981"
                  } />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#1A1A2E", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8, color: "#F8FAFC" }}
              />
              <Legend wrapperStyle={{ color: "#94A3B8", fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
