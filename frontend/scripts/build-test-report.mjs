/**
 * Folds the three test runners' JSON output into one file the /tests page renders.
 *
 *   backend/test-report.json               <- pytest     (tests/report_plugin.py)
 *   frontend/test-reports/vitest.json      <- vitest     (npm run test:json)
 *   frontend/test-reports/playwright.json  <- playwright (npm run e2e)
 *
 * The merged result is committed at src/data/test-report.json so the deployed
 * page renders without needing a test run at build time. Any runner whose
 * output is missing is simply skipped — running only the backend suite should
 * still refresh the backend half of the page rather than failing outright.
 *
 * Usage: npm run test:report
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const repoRoot = resolve(frontendRoot, "..");

const OUTPUT = resolve(frontendRoot, "src/data/test-report.json");

const SOURCES = {
  pytest: resolve(repoRoot, "backend/test-report.json"),
  vitest: resolve(frontendRoot, "test-reports/vitest.json"),
  playwright: resolve(frontendRoot, "test-reports/playwright.json"),
};

function readJson(path) {
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, "utf-8"));
  } catch (err) {
    console.warn(`[test-report] ignoring unreadable ${path}: ${err.message}`);
    return null;
  }
}

/** `should render the hero` -> `Should render the hero` */
function titleCase(text) {
  const trimmed = String(text ?? "").trim();
  return trimmed ? trimmed[0].toUpperCase() + trimmed.slice(1) : trimmed;
}

/** pytest records are already in the target shape. */
function fromPytest(report) {
  return (report?.tests ?? []).map((test) => ({ ...test, suite: "backend" }));
}

/** Vitest's JSON reporter emits a jest-compatible testResults array. */
function fromVitest(report) {
  const tests = [];
  for (const file of report?.testResults ?? []) {
    const relative = String(file.name ?? "").split(/[\\/]src[\\/]/).pop() ?? file.name;
    for (const assertion of file.assertionResults ?? []) {
      tests.push({
        id: `${relative}::${assertion.fullName ?? assertion.title}`,
        suite: "frontend",
        category: "unit",
        file: `frontend/src/${relative}`,
        group: (assertion.ancestorTitles ?? []).join(" › "),
        name: titleCase(assertion.title),
        // Vitest has no docstring equivalent; the test title is the claim.
        purpose: "",
        outcome: assertion.status === "pending" ? "skipped" : assertion.status,
        duration_ms: Number((assertion.duration ?? 0).toFixed(2)),
      });
    }
  }
  return tests;
}

/** Playwright nests suites arbitrarily deep; flatten to specs. */
function fromPlaywright(report) {
  const tests = [];

  const walk = (suite, trail) => {
    const path = suite.title ? [...trail, suite.title] : trail;
    for (const spec of suite.specs ?? []) {
      const result = spec.tests?.[0]?.results?.[0];
      const status = spec.ok ? "passed" : result?.status === "skipped" ? "skipped" : "failed";
      tests.push({
        id: `${suite.file ?? "e2e"}::${spec.title}`,
        suite: "frontend",
        category: "e2e",
        file: `frontend/e2e/${suite.file ?? ""}`.replace(/\/$/, ""),
        group: path.filter((p) => p !== suite.file).join(" › "),
        name: titleCase(spec.title),
        purpose: "",
        outcome: status,
        duration_ms: Number((result?.duration ?? 0).toFixed(2)),
      });
    }
    for (const child of suite.suites ?? []) walk(child, path);
  };

  for (const suite of report?.suites ?? []) walk(suite, []);
  return tests;
}

const pytest = readJson(SOURCES.pytest);
const vitest = readJson(SOURCES.vitest);
const playwright = readJson(SOURCES.playwright);

for (const [name, path] of Object.entries(SOURCES)) {
  if (!existsSync(path)) {
    console.warn(`[test-report] no ${name} output at ${path} — skipping`);
  }
}

const tests = [
  ...fromPytest(pytest),
  ...fromVitest(vitest),
  ...fromPlaywright(playwright),
];

if (tests.length === 0) {
  console.error(
    "[test-report] no results found. Run `pytest` in backend/ and " +
      "`npm run test:json` here first.",
  );
  process.exit(1);
}

const CATEGORY_ORDER = [
  "unit",
  "integration",
  "contract",
  "performance",
  "security",
  "multilingual",
  "resilience",
  "e2e",
];

const categories = CATEGORY_ORDER.filter((c) => tests.some((t) => t.category === c)).map(
  (id) => {
    const inCategory = tests.filter((t) => t.category === id);
    return {
      id,
      total: inCategory.length,
      passed: inCategory.filter((t) => t.outcome === "passed").length,
      failed: inCategory.filter((t) => t.outcome === "failed" || t.outcome === "error").length,
      durationMs: Number(
        inCategory.reduce((sum, t) => sum + (t.duration_ms ?? 0), 0).toFixed(2),
      ),
    };
  },
);

const payload = {
  generatedAt: new Date().toISOString(),
  total: tests.length,
  passed: tests.filter((t) => t.outcome === "passed").length,
  failed: tests.filter((t) => t.outcome === "failed" || t.outcome === "error").length,
  skipped: tests.filter((t) => t.outcome === "skipped").length,
  durationMs: Number(tests.reduce((sum, t) => sum + (t.duration_ms ?? 0), 0).toFixed(2)),
  categories,
  tests,
};

mkdirSync(dirname(OUTPUT), { recursive: true });
writeFileSync(OUTPUT, `${JSON.stringify(payload, null, 2)}\n`, "utf-8");

console.log(
  `[test-report] ${payload.total} tests (${payload.passed} passed, ` +
    `${payload.failed} failed) across ${categories.length} categories -> ${OUTPUT}`,
);
