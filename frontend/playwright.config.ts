import { defineConfig } from "@playwright/test";

/**
 * E2E smoke suite — runs against a production `next start` on :3000.
 * All backend API calls are mocked with page.route() inside the specs, so no
 * FastAPI/Postgres is needed: these tests cover the browser-level flows
 * (middleware redirects, login, dashboard render), while the backend is
 * covered by its own pytest suite.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["list"]] : "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: {
    command: "npm run start",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
