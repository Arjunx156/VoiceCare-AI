"use client";

/**
 * Test Runs — isolated QA scenario runner. Fully independent of Tickets/
 * Escalations/Analytics: results live in their own backend table
 * (test_runs / test_case_results) with no FK into SupportTicket, so nothing
 * run here can ever show up as a real complaint.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  cancelTestRun,
  getTestRun,
  listTestRunScenarios,
  startTestRun,
  type TestCaseResultItem,
  type TestRunItem,
  type TestScenarioSummary,
} from "@/lib/api";
import { useMotionSafe } from "@/lib/motion";
import { Badge, Button, EmptyState, LoadingBlock, Panel } from "@/components/ui";
import { Hourglass } from "lucide-react";

const STATUS_META: Record<TestCaseResultItem["status"], { bg: string; fg: string }> = {
  passed: { bg: "rgba(52,168,83,0.14)", fg: "var(--status-low)" },
  failed: { bg: "rgba(229,57,53,0.12)", fg: "var(--status-high)" },
  observed: { bg: "var(--bg-panel-raised)", fg: "var(--text-secondary)" },
  skipped: { bg: "var(--bg-panel-raised)", fg: "var(--text-muted)" },
};

function ResultStatusBadge({ status }: { status: TestCaseResultItem["status"] }) {
  return <Badge meta={STATUS_META[status]}>{status}</Badge>;
}

export default function TestRunsPage() {
  const { entry } = useMotionSafe();
  const [scenarios, setScenarios] = useState<TestScenarioSummary[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [run, setRun] = useState<TestRunItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    listTestRunScenarios()
      .then((data) => {
        if (!mounted) return;
        setScenarios(data);
        setSelected(new Set(data.map((s) => s.id)));
      })
      .catch((err) => {
        if (mounted) setError(err instanceof Error ? err.message : "Failed to load scenarios");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  // Polls the active run every 3s (backing off to 5s on a transient fetch
  // error) until it leaves the "running" state. Re-arms whenever a new run
  // starts (run_id changes) and stops naturally once status flips away from
  // "running" — no separate cleanup ref needed.
  useEffect(() => {
    if (!run || run.status !== "running") return;
    const runId = run.run_id;
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;
    let controller: AbortController;

    async function tick() {
      controller = new AbortController();
      try {
        const data = await getTestRun(runId, controller.signal);
        if (cancelled) return;
        setRun(data);
        if (data.status === "running") {
          timeoutId = setTimeout(tick, 3_000);
        }
      } catch (err: unknown) {
        if (cancelled || (err instanceof Error && err.name === "AbortError")) return;
        timeoutId = setTimeout(tick, 5_000);
      }
    }
    timeoutId = setTimeout(tick, 3_000);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
      controller?.abort();
    };
    // Deliberately keyed on run_id/status rather than the whole `run` object:
    // every poll tick calls setRun() with a new object reference, and depending
    // on `run` directly would tear down and re-arm this effect (and its
    // in-flight request) on every single tick instead of only when the run
    // identity or its running/not-running state actually changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run?.run_id, run?.status]);

  function toggleScenario(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected((prev) => (prev.size === scenarios.length ? new Set() : new Set(scenarios.map((s) => s.id))));
  }

  async function handleStart() {
    setStarting(true);
    setError(null);
    try {
      const scenarioIds = selected.size === scenarios.length ? undefined : Array.from(selected);
      const started = await startTestRun(scenarioIds);
      setRun(started); // polling effect below picks this up automatically
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start test run");
    } finally {
      setStarting(false);
    }
  }

  async function handleCancel() {
    if (!run) return;
    try {
      await cancelTestRun(run.run_id);
    } catch (err) {
      console.error("Failed to cancel test run:", err);
    }
  }

  if (loading) {
    return <LoadingBlock label="Loading test scenarios" />;
  }

  const isRunning = run?.status === "running";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      <motion.div {...entry()}>
        <span className="eyebrow">QA TEST RUNS</span>
        <h1 className="page-title">Test Runs</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 6 }}>
          Runs canned scenarios through the live pipeline (agents 1-7 only — no ticket is
          created, no TTS is invoked). Real Gemini calls are capped per run; once the budget
          is spent, remaining scenarios fall back to a mocked response so the run always
          finishes.
        </p>
      </motion.div>

      {error && (
        <Panel style={{ padding: "14px 18px" }}>
          <p style={{ fontSize: 13, color: "var(--status-high)" }}>{error}</p>
        </Panel>
      )}

      <Panel style={{ padding: "20px 22px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
            Scenarios ({selected.size}/{scenarios.length} selected)
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            <Button variant="ghost" size="sm" onClick={toggleAll} disabled={isRunning}>
              {selected.size === scenarios.length ? "Deselect all" : "Select all"}
            </Button>
            {isRunning ? (
              <Button variant="danger" size="sm" onClick={handleCancel}>
                Cancel run
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={handleStart}
                isLoading={starting}
                disabled={selected.size === 0}
              >
                Run {selected.size} scenario{selected.size === 1 ? "" : "s"}
              </Button>
            )}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 8 }}>
          {scenarios.map((s) => (
            <label
              key={s.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 12,
                color: "var(--text-secondary)",
                padding: "6px 10px",
                borderRadius: 8,
                background: "var(--bg-panel-raised)",
                cursor: isRunning ? "not-allowed" : "pointer",
                opacity: isRunning ? 0.6 : 1,
              }}
            >
              <input
                type="checkbox"
                checked={selected.has(s.id)}
                onChange={() => toggleScenario(s.id)}
                disabled={isRunning}
              />
              {s.label}
            </label>
          ))}
        </div>
      </Panel>

      {run && (
        <Panel style={{ padding: "20px 22px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <div>
              <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                Run {run.run_id.slice(0, 8)} — {run.status}
              </p>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                {run.completed_scenarios}/{run.total_scenarios} complete ·{" "}
                {run.live_call_count} live Gemini calls · {run.mock_fallback_count} mocked
              </p>
            </div>
          </div>

          {run.results.length === 0 ? (
            <EmptyState icon={Hourglass} title="No results yet" hint="Waiting for the first scenario to finish" />
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ textAlign: "left", color: "var(--text-muted)" }}>
                    <th style={{ padding: "6px 8px" }}>Scenario</th>
                    <th style={{ padding: "6px 8px" }}>Status</th>
                    <th style={{ padding: "6px 8px" }}>Intent</th>
                    <th style={{ padding: "6px 8px" }}>Escalated</th>
                    <th style={{ padding: "6px 8px" }}>Confidence</th>
                    <th style={{ padding: "6px 8px" }}>Latency</th>
                    <th style={{ padding: "6px 8px" }}>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {run.results.map((r) => (
                    <tr key={r.result_id} style={{ borderTop: "1px solid var(--border-subtle)" }}>
                      <td style={{ padding: "8px" }}>{r.scenario_label}</td>
                      <td style={{ padding: "8px" }}>
                        <ResultStatusBadge status={r.status} />
                      </td>
                      <td style={{ padding: "8px", color: "var(--text-secondary)" }}>{r.intent || "—"}</td>
                      <td style={{ padding: "8px", color: "var(--text-secondary)" }}>
                        {r.is_escalated ? "Yes" : "No"}
                      </td>
                      <td style={{ padding: "8px", color: "var(--text-secondary)" }}>
                        {r.confidence_score != null ? r.confidence_score.toFixed(2) : "—"}
                      </td>
                      <td style={{ padding: "8px", color: "var(--text-secondary)" }}>
                        {r.latency_ms != null ? `${r.latency_ms}ms` : "—"}
                      </td>
                      <td style={{ padding: "8px" }}>
                        <span
                          style={{
                            fontSize: 10,
                            fontWeight: 600,
                            color: r.used_live_api ? "var(--accent)" : "var(--text-muted)",
                          }}
                        >
                          {r.used_live_api ? "LIVE" : "MOCKED"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}
