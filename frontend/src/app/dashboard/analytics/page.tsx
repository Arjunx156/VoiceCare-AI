"use client";

/**
 * Analytics — asymmetric two-column, eyebrow labels, editorial panels.
 * Charts use recharts with the shared design-system palette (lib/theme).
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { BarChart3 } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { getAnalytics, type AnalyticsOverview } from "@/lib/api";
import { CHART_COLORS, PRIORITY_HEX, chartTooltipStyle, sentimentHex } from "@/lib/theme";
import { useMotionSafe } from "@/lib/motion";
import { EmptyState, LoadingBlock, Panel, StatCard } from "@/components/ui";

const AXIS_TICK = { fill: "#8A8A8A", fontSize: 11 };

type FetchResult =
  | { analytics: AnalyticsOverview }
  | { error: string };

export default function AnalyticsPage() {
  const [result, setResult] = useState<FetchResult | null>(null);
  const { entry } = useMotionSafe();

  useEffect(() => {
    let cancelled = false;
    getAnalytics()
      .then((analytics) => {
        if (!cancelled) setResult({ analytics });
      })
      .catch((err: unknown) => {
        console.error("Analytics load failed:", err);
        if (!cancelled) {
          setResult({ error: err instanceof Error ? err.message : "Failed to load analytics" });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!result) {
    return <LoadingBlock label="Loading analytics" />;
  }

  const analytics = "analytics" in result ? result.analytics : null;

  if (!analytics || analytics.total_tickets === 0) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
        <div>
          <span className="eyebrow">ANALYTICS</span>
          <h1 className="page-title">Insights</h1>
        </div>
        <Panel>
          <EmptyState
            icon={BarChart3}
            title={"error" in result ? "Unable to load analytics" : "No data yet"}
            hint={"error" in result ? result.error : "Start processing voice queries to see analytics"}
          />
        </Panel>
      </div>
    );
  }

  const langData = Object.entries(analytics.tickets_by_language).map(([name, value]) => ({ name, value }));
  const catData  = Object.entries(analytics.tickets_by_category).map(([name, value]) => ({ name, value }));
  const priData  = Object.entries(analytics.tickets_by_priority).map(([name, value]) => ({ name, value }));
  const sentData = Object.entries(analytics.tickets_by_sentiment).map(([name, value]) => ({ name, value }));

  const kpis = [
    { label: "RESOLUTION RATE", value: `${analytics.resolution_rate}%` },
    { label: "ESCALATION RATE", value: `${analytics.escalation_rate}%` },
    { label: "TOTAL TICKETS",   value: analytics.total_tickets },
    { label: "OPEN NOW",        value: analytics.open_tickets },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      {/* Header */}
      <motion.div {...entry()}>
        <span className="eyebrow">ANALYTICS</span>
        <h1 className="page-title">Ticket Insights</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 6 }}>
          Language distribution, category breakdown, priority and sentiment analysis
        </p>
      </motion.div>

      {/* KPI strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        {kpis.map((s, i) => (
          <motion.div key={s.label} {...entry(i * 0.06)}>
            <StatCard label={s.label} value={s.value} />
          </motion.div>
        ))}
      </div>

      {/* Asymmetric two-column: large language bar + smaller category donut
          (collapses to one column under 900px — .grid-main-side) */}
      <div className="grid-main-side">
        {/* Ticket Volume by Language — larger block */}
        <motion.div {...entry(0.28)} className="panel" style={{ padding: "24px 24px 16px" }}>
          <span className="eyebrow">TICKET VOLUME</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 20 }}>
            By Language
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={langData} margin={{ left: -16, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
              <XAxis dataKey="name" tick={AXIS_TICK} axisLine={false} tickLine={false} />
              <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} />
              <Tooltip {...chartTooltipStyle} />
              <Bar dataKey="value" fill="#FF5A2B" radius={[4, 4, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* By Category — smaller, donut */}
        <motion.div {...entry(0.34)} className="panel" style={{ padding: "24px 20px 16px" }}>
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
              <Tooltip {...chartTooltipStyle} />
              <Legend wrapperStyle={{ color: "#9A9A9A", fontSize: 10, paddingTop: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Priority + Sentiment side by side (stacks under 900px — .grid-half) */}
      <div className="grid-half">
        {/* By Priority */}
        <motion.div {...entry(0.42)} className="panel" style={{ padding: "24px 24px 16px" }}>
          <span className="eyebrow">PRIORITY</span>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", marginBottom: 20 }}>
            Distribution
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={priData} layout="vertical" margin={{ left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" horizontal={false} />
              <XAxis type="number" tick={AXIS_TICK} axisLine={false} tickLine={false} />
              <YAxis dataKey="name" type="category" tick={{ fill: "#9A9A9A", fontSize: 11 }} axisLine={false} tickLine={false} width={60} />
              <Tooltip {...chartTooltipStyle} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={20}>
                {priData.map((priority, i) => (
                  <Cell key={i} fill={PRIORITY_HEX[priority.name] || "#9A9A9A"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* By Sentiment */}
        <motion.div {...entry(0.48)} className="panel" style={{ padding: "24px 24px 16px" }}>
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
                {sentData.map((sentiment, i) => (
                  <Cell key={i} fill={sentimentHex(sentiment.name)} />
                ))}
              </Pie>
              <Tooltip {...chartTooltipStyle} />
              <Legend wrapperStyle={{ color: "#9A9A9A", fontSize: 10 }} />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </div>
  );
}
