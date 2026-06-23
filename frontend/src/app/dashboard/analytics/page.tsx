"use client";

/**
 * CommerceMind VoiceCare AI — Analytics Page v2
 * Design brief: asymmetric two-column, eyebrow labels, editorial panels.
 * Charts use recharts with the new design system palette.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { getAnalytics, type AnalyticsOverview } from "@/lib/api";

// Semantic color palette for charts (separate from brand accent)
const CHART_COLORS = [
  "#FF5A2B", "#D4A017", "#4CAF73", "#607D8B",
  "#E53935", "#8D6E63", "#42A5F5", "#AB47BC",
];

// Priority semantic bar colors
const PRI_COLOR: Record<string, string> = {
  Critical: "#C62828", High: "#E53935", Medium: "#D4A017", Low: "#4CAF73",
};

// Sentiment colors
function sentColor(name: string) {
  if (name === "Angry" || name === "Very Angry") return "#E53935";
  if (name === "Negative") return "#D4A017";
  if (name === "Calm" || name === "Confused") return "#607D8B";
  return "#4CAF73";
}

// Shared tooltip style
const tooltipStyle = {
  contentStyle: {
    background: "#161616",
    border: "1px solid #262626",
    borderRadius: 10,
    color: "#F5F5F5",
    fontSize: 12,
  },
  cursor: { fill: "rgba(255,255,255,0.04)" },
};

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    async function load() {
      try { setAnalytics(await getAnalytics()); }
      catch (err) { console.error("Analytics load failed:", err); }
      finally { setLoading(false); }
    }
    load();
  }, []);

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

  if (!analytics || analytics.total_tickets === 0) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
        <div>
          <span className="eyebrow">ANALYTICS</span>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)" }}>Insights</h1>
        </div>
        <div className="panel" style={{ textAlign: "center", padding: "80px 0" }}>
          <p style={{ fontSize: 40, marginBottom: 12 }}>📊</p>
          <p style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>No data yet</p>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 6 }}>
            Start processing voice queries to see analytics
          </p>
        </div>
      </div>
    );
  }

  const langData = Object.entries(analytics.tickets_by_language).map(([name, value]) => ({ name, value }));
  const catData  = Object.entries(analytics.tickets_by_category).map(([name, value]) => ({ name, value }));
  const priData  = Object.entries(analytics.tickets_by_priority).map(([name, value]) => ({ name, value }));
  const sentData = Object.entries(analytics.tickets_by_sentiment).map(([name, value]) => ({ name, value }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="eyebrow">ANALYTICS</span>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>
          Ticket Insights
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 6 }}>
          Language distribution, category breakdown, priority and sentiment analysis
        </p>
      </motion.div>

      {/* KPI strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        {[
          { eyebrow: "RESOLUTION RATE", value: `${analytics.resolution_rate}%` },
          { eyebrow: "ESCALATION RATE", value: `${analytics.escalation_rate}%` },
          { eyebrow: "TOTAL TICKETS",   value: analytics.total_tickets },
          { eyebrow: "OPEN NOW",        value: analytics.open_tickets },
        ].map((s, i) => (
          <motion.div
            key={s.eyebrow}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="panel panel-hover"
            style={{ padding: "18px 20px" }}
          >
            <span className="eyebrow">{s.eyebrow}</span>
            <p style={{ fontSize: 30, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>
              {s.value}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Asymmetric two-column: large language bar + smaller category donut */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
        {/* Ticket Volume by Language — larger block */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.28, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="panel"
          style={{ padding: "24px 24px 16px" }}
        >
          <span className="eyebrow">TICKET VOLUME</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 20 }}>
            By Language
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={langData} margin={{ left: -16, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "#5A5A5A", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#5A5A5A", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="value" fill="#FF5A2B" radius={[4, 4, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* By Category — smaller, donut */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.34, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="panel"
          style={{ padding: "24px 20px 16px" }}
        >
          <span className="eyebrow">CATEGORY</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 12 }}>
            Breakdown
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={catData}
                dataKey="value"
                nameKey="name"
                cx="50%" cy="45%"
                innerRadius={50} outerRadius={80}
              >
                {catData.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend wrapperStyle={{ color: "#9A9A9A", fontSize: 10, paddingTop: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Priority + Sentiment side by side */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* By Priority */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.42, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="panel"
          style={{ padding: "24px 24px 16px" }}
        >
          <span className="eyebrow">PRIORITY</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 20 }}>
            Distribution
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={priData} layout="vertical" margin={{ left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" horizontal={false} />
              <XAxis type="number" tick={{ fill: "#5A5A5A", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis dataKey="name" type="category" tick={{ fill: "#9A9A9A", fontSize: 11 }} axisLine={false} tickLine={false} width={60} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={20}>
                {priData.map((entry, i) => (
                  <Cell key={i} fill={PRI_COLOR[entry.name] || "#9A9A9A"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* By Sentiment */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.48, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="panel"
          style={{ padding: "24px 24px 16px" }}
        >
          <span className="eyebrow">SENTIMENT</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 12 }}>
            Customer Mood
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={sentData}
                dataKey="value"
                nameKey="name"
                cx="50%" cy="50%"
                innerRadius={45} outerRadius={70}
              >
                {sentData.map((entry, i) => (
                  <Cell key={i} fill={sentColor(entry.name)} />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend wrapperStyle={{ color: "#9A9A9A", fontSize: 10 }} />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </div>
  );
}
