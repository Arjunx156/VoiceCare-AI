"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";

import { Tabs } from "@/components/ui/Tabs";
import { CATEGORY_META, type TestRecord, type TestReport } from "./types";

/** 4.2 -> "4 ms", 1240 -> "1.24 s" */
function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

function OutcomeBadge({ outcome }: { outcome: TestRecord["outcome"] }) {
  const isPass = outcome === "passed";
  const isSkip = outcome === "skipped";
  const color = isPass
    ? "var(--status-low)"
    : isSkip
      ? "var(--text-muted)"
      : "var(--status-high)";

  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color,
        border: `1px solid ${color}`,
        borderRadius: 999,
        padding: "2px 8px",
        flexShrink: 0,
        // Never colour alone — the word carries the meaning for anyone who
        // cannot distinguish the hues.
      }}
    >
      {outcome}
    </span>
  );
}

function TestRow({ test, index }: { test: TestRecord; index: number }) {
  return (
    <motion.li
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, delay: Math.min(index * 0.012, 0.4) }}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 14,
        padding: "14px 0",
        borderTop: "1px solid var(--border-subtle)",
      }}
    >
      <span
        style={{
          fontSize: 11,
          fontWeight: 700,
          color: "var(--text-faint)",
          fontVariantNumeric: "tabular-nums",
          width: 28,
          flexShrink: 0,
          paddingTop: 2,
        }}
      >
        {String(index + 1).padStart(2, "0")}
      </span>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
          {test.group && (
            <span style={{ fontSize: 11, color: "var(--text-faint)" }}>{test.group} ›</span>
          )}
          <span style={{ fontSize: 13, fontWeight: 500, color: "var(--text-primary)" }}>
            {test.name}
          </span>
        </div>

        {test.purpose && (
          <p
            style={{
              fontSize: 12,
              color: "var(--text-muted)",
              lineHeight: 1.55,
              marginTop: 4,
            }}
          >
            {test.purpose}
          </p>
        )}

        <p style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 4 }}>{test.file}</p>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          flexShrink: 0,
          paddingTop: 1,
        }}
      >
        <span
          style={{
            fontSize: 11,
            color: "var(--text-muted)",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {formatDuration(test.duration_ms)}
        </span>
        <OutcomeBadge outcome={test.outcome} />
      </div>
    </motion.li>
  );
}

export function TestExplorer({ report }: { report: TestReport }) {
  const [category, setCategory] = useState("all");
  const [query, setQuery] = useState("");

  const tabs = useMemo(
    () => [
      { value: "all", label: `All ${report.total}` },
      ...report.categories.map((c) => ({
        value: c.id,
        label: `${CATEGORY_META[c.id]?.label ?? c.id} ${c.total}`,
      })),
    ],
    [report],
  );

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return report.tests.filter((test) => {
      if (category !== "all" && test.category !== category) return false;
      if (!needle) return true;
      return (
        test.name.toLowerCase().includes(needle) ||
        test.purpose.toLowerCase().includes(needle) ||
        test.file.toLowerCase().includes(needle) ||
        test.group.toLowerCase().includes(needle)
      );
    });
  }, [report.tests, category, query]);

  const activeMeta = category === "all" ? null : CATEGORY_META[category];

  return (
    <>
      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <label htmlFor="test-search" className="sr-only">
          Filter tests
        </label>
        <input
          id="test-search"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter by name, claim, or file…"
          style={{
            flex: 1,
            minWidth: 220,
            background: "var(--bg-panel)",
            border: "1px solid var(--border-subtle)",
            borderRadius: 10,
            padding: "10px 14px",
            fontSize: 13,
            color: "var(--text-primary)",
            fontFamily: "inherit",
          }}
        />
      </div>

      <div style={{ marginTop: 20 }}>
        <Tabs tabs={tabs} value={category} onChange={setCategory}>
          {activeMeta && (
            <p
              style={{
                fontSize: 13,
                color: "var(--text-secondary)",
                lineHeight: 1.6,
                maxWidth: "62ch",
                marginBottom: 20,
              }}
            >
              {activeMeta.blurb}
            </p>
          )}

          <div className="panel" style={{ padding: "8px 24px 20px" }}>
            <p
              className="eyebrow"
              aria-live="polite"
              style={{ paddingTop: 16, marginBottom: 0 }}
            >
              {visible.length} {visible.length === 1 ? "test" : "tests"}
            </p>

            {visible.length === 0 ? (
              <p
                style={{
                  fontSize: 13,
                  color: "var(--text-muted)",
                  padding: "24px 0 8px",
                }}
              >
                No tests match “{query}”.
              </p>
            ) : (
              <ol style={{ listStyle: "none", marginTop: 12 }}>
                {visible.map((test, index) => (
                  <TestRow key={test.id} test={test} index={index} />
                ))}
              </ol>
            )}
          </div>
        </Tabs>
      </div>
    </>
  );
}
