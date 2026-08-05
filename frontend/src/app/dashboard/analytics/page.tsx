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
import {
  CHART_COLORS,
  CHART_LABEL_COLOR,
  chartLegendStyle,
  chartTooltipStyle,
  priorityHex,
  sentimentHex,
} from "@/lib/theme";
import { useMotionSafe } from "@/lib/motion";

/** Legend labels stay neutral; the swatch beside them carries the colour. */
const legendLabel = (value: string) => (
  <span style={{ color: CHART_LABEL_COLOR }}>{value.replace(/_/g, " ")}</span>
);
import { EmptyState, LoadingBlock, Panel, StatCard, StatCluster } from "@/components/ui";

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
          <span className="eyebrow">Analytics</span>
          <h1 className="page-title">Ticket insights</h1>
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
  const catData  = Object.entries(analytics.tickets_by_category)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);
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
        <span className="eyebrow">
          {analytics.total_tickets.toLocaleString()} tickets analysed
        </span>
        <h1 className="page-title">Ticket insights</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 10, maxWidth: "58ch" }}>
          How the queue breaks down by language, category, priority and the mood customers arrived in.
        </p>
      </motion.div>

      {/* Four readings, one instrument — see StatCluster. */}
      <motion.div {...entry(0.06)}>
        <StatCluster>
          {kpis.map((s) => (
            <StatCard key={s.label} label={s.label} value={s.value} />
          ))}
        </StatCluster>
      </motion.div>

      {/* Asymmetric two-column: large language bar + smaller category donut
          (collapses to one column under 900px — .grid-main-side) */}
      <div className="grid-main-side">
        {/* Ticket Volume by Language — larger block */}
        <motion.div {...entry(0.12)} className="panel" style={{ padding: "22px 24px 14px" }}>
          <div className="rule-head">
            <h2 className="section-title">Volume by language</h2>
          </div>
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
        <motion.div {...entry(0.12)} className="panel" style={{ padding: "22px 20px 14px" }}>
          <div className="rule-head">
            <h2 className="section-title">By category</h2>
          </div>
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
              <Legend {...chartLegendStyle} formatter={legendLabel} />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Priority + Sentiment side by side (stacks under 900px — .grid-half) */}
      <div className="grid-half">
        {/* By Priority */}
        <motion.div {...entry(0.18)} className="panel" style={{ padding: "22px 24px 14px" }}>
          <div className="rule-head">
            <h2 className="section-title">By priority</h2>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={priData} layout="vertical" margin={{ left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" horizontal={false} />
              <XAxis type="number" tick={AXIS_TICK} axisLine={false} tickLine={false} />
              <YAxis dataKey="name" type="category" tick={{ fill: "#9A9A9A", fontSize: 11 }} axisLine={false} tickLine={false} width={60} />
              <Tooltip {...chartTooltipStyle} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={20}>
                {priData.map((priority, i) => (
                  <Cell key={i} fill={priorityHex(priority.name)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* By Sentiment */}
        <motion.div {...entry(0.18)} className="panel" style={{ padding: "22px 24px 14px" }}>
          <div className="rule-head">
            <h2 className="section-title">Mood on arrival</h2>
          </div>
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
              <Legend {...chartLegendStyle} formatter={legendLabel} />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </div>
  );
}
