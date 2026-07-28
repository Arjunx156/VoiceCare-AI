import type { Metadata } from "next";
import Link from "next/link";

import reportData from "@/data/test-report.json";
import { TestExplorer } from "./TestExplorer";
import { CATEGORY_META, type TestReport } from "./types";

const report = reportData as TestReport;

export const metadata: Metadata = {
  title: "Test suite — VoiceCare AI",
  description:
    "Every automated test behind VoiceCare AI, grouped by what it proves: correctness, latency, security, multilingual support, and resilience.",
};

function Stat({
  value,
  label,
  accent,
}: {
  value: string;
  label: string;
  accent?: string;
}) {
  return (
    <div>
      <p
        style={{
          fontSize: 32,
          fontWeight: 700,
          letterSpacing: "-0.02em",
          color: accent ?? "var(--text-primary)",
          fontVariantNumeric: "tabular-nums",
          lineHeight: 1.1,
        }}
      >
        {value}
      </p>
      <p
        style={{
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--text-muted)",
          marginTop: 6,
        }}
      >
        {label}
      </p>
    </div>
  );
}

export default function TestsPage() {
  const generated = new Date(report.generatedAt);
  const allGreen = report.failed === 0;

  return (
    <main
      style={{
        maxWidth: 940,
        margin: "0 auto",
        padding: "64px 24px 96px",
      }}
    >
      <Link
        href="/"
        style={{
          fontSize: 12,
          fontWeight: 600,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--text-muted)",
          textDecoration: "none",
        }}
      >
        ← VoiceCare AI
      </Link>

      <h1
        style={{
          fontSize: "clamp(2rem, 1.2rem + 3vw, 3.2rem)",
          fontWeight: 700,
          letterSpacing: "-0.03em",
          lineHeight: 1.05,
          marginTop: 28,
        }}
      >
        The test suite
      </h1>

      <p
        style={{
          fontSize: 15,
          color: "var(--text-secondary)",
          lineHeight: 1.65,
          maxWidth: "64ch",
          marginTop: 18,
        }}
      >
        Every automated check behind VoiceCare AI, grouped by what it actually proves
        rather than by where the file happens to live. Each entry shows the claim the
        test makes — taken from the test&rsquo;s own documentation, so this page cannot
        drift from the code — along with its result and how long it took.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
          gap: 28,
          marginTop: 44,
          paddingBottom: 32,
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <Stat value={String(report.total)} label="Tests" />
        <Stat
          value={String(report.passed)}
          label="Passing"
          accent={allGreen ? "var(--status-low)" : undefined}
        />
        <Stat
          value={String(report.failed)}
          label="Failing"
          accent={allGreen ? undefined : "var(--status-high)"}
        />
        <Stat value={String(report.categories.length)} label="Categories" />
        <Stat
          value={`${(report.durationMs / 1000).toFixed(1)}s`}
          label="Total runtime"
        />
      </div>

      <section style={{ marginTop: 40 }}>
        <h2 className="sr-only">Categories</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: 16,
          }}
        >
          {report.categories.map((category) => {
            const meta = CATEGORY_META[category.id];
            return (
              <div
                key={category.id}
                className="panel"
                style={{ padding: "18px 20px" }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    justifyContent: "space-between",
                    gap: 12,
                  }}
                >
                  <span
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: "var(--text-primary)",
                    }}
                  >
                    {meta?.label ?? category.id}
                  </span>
                  <span
                    style={{
                      fontSize: 13,
                      fontWeight: 700,
                      color:
                        category.failed === 0
                          ? "var(--status-low)"
                          : "var(--status-high)",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {category.passed}/{category.total}
                  </span>
                </div>
                {meta && (
                  <p
                    style={{
                      fontSize: 12,
                      color: "var(--text-muted)",
                      lineHeight: 1.55,
                      marginTop: 8,
                    }}
                  >
                    {meta.blurb}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </section>

      <section style={{ marginTop: 48 }}>
        <h2
          style={{
            fontSize: 20,
            fontWeight: 700,
            letterSpacing: "-0.01em",
            marginBottom: 20,
          }}
        >
          Every test
        </h2>
        <TestExplorer report={report} />
      </section>

      <p
        style={{
          fontSize: 11,
          color: "var(--text-faint)",
          marginTop: 40,
          lineHeight: 1.6,
        }}
      >
        Generated{" "}
        <time dateTime={report.generatedAt}>
          {generated.toISOString().replace("T", " ").slice(0, 16)} UTC
        </time>{" "}
        from pytest, Vitest and Playwright. Refresh with{" "}
        <code style={{ color: "var(--text-muted)" }}>npm run test:report</code>.
      </p>
    </main>
  );
}
