/**
 * Shape of frontend/src/data/test-report.json, produced by
 * scripts/build-test-report.mjs from the pytest, Vitest and Playwright runs.
 */

export type TestOutcome = "passed" | "failed" | "error" | "skipped";

export interface TestRecord {
  id: string;
  suite: "backend" | "frontend";
  category: string;
  file: string;
  group: string;
  name: string;
  /** The test's own docstring summary. Empty when the test has none. */
  purpose: string;
  outcome: TestOutcome;
  duration_ms: number;
}

export interface CategorySummary {
  id: string;
  total: number;
  passed: number;
  failed: number;
  durationMs: number;
}

export interface TestReport {
  generatedAt: string;
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  durationMs: number;
  categories: CategorySummary[];
  tests: TestRecord[];
}

/** What each category proves, shown as the section's standfirst. */
export const CATEGORY_META: Record<string, { label: string; blurb: string }> = {
  unit: {
    label: "Unit",
    blurb:
      "Individual services and helpers in isolation — every external dependency mocked.",
  },
  integration: {
    label: "Integration",
    blurb:
      "The 9-agent pipeline end to end against an in-memory database, including multi-turn identity.",
  },
  contract: {
    label: "Contract",
    blurb:
      "The wire format between backend and browser: WebSocket frame shapes, response parity, trace structure.",
  },
  performance: {
    label: "Performance",
    blurb:
      "Latency budgets and query ceilings. These fail if a change reintroduces a blocking call or a query fan-out.",
  },
  security: {
    label: "Security",
    blurb:
      "Authentication, rate limits, input ceilings, identity corroboration, and information-leak defences.",
  },
  multilingual: {
    label: "Multilingual",
    blurb:
      "All nine supported languages: code mapping, native-script round trips, and speech routing.",
  },
  resilience: {
    label: "Resilience",
    blurb:
      "What happens when Gemini, Chroma, Bhashini, or the database fails mid-turn.",
  },
  e2e: {
    label: "End-to-end",
    blurb:
      "Real browser flows through a production build: routing, auth redirects, and the voice surface.",
  },
};
