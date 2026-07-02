import { test, expect, type Page } from "@playwright/test";

/**
 * Browser-level smoke tests for the critical flows. Backend responses are
 * mocked at the network layer (page.route), so what's under test is the real
 * UI: Next middleware, the login flow, and dashboard rendering.
 */

const EMPTY_ANALYTICS = {
  total_tickets: 3,
  open_tickets: 2,
  escalated_tickets: 1,
  resolved_tickets: 0,
  tickets_by_language: { Hindi: 2, Tamil: 1 },
  tickets_by_category: { Refund: 3 },
  tickets_by_priority: { High: 1, Medium: 2 },
  tickets_by_sentiment: { Calm: 3 },
  tickets_over_time: [],
  resolution_rate: 0,
  escalation_rate: 33.3,
};

async function mockDashboardApis(page: Page) {
  await page.route("**/api/auth/login", (route) =>
    route.fulfill({ json: { access_token: "e2e-token", token_type: "bearer", expires_in: 28800 } }),
  );
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ json: { admin_email: "admin@e2e.test" } }),
  );
  await page.route("**/api/tickets/analytics", (route) =>
    route.fulfill({ json: EMPTY_ANALYTICS }),
  );
  await page.route("**/api/tickets/escalations", (route) => route.fulfill({ json: [] }));
  await page.route("**/health", (route) => route.fulfill({ json: { status: "ok" } }));
}

test("voice landing page renders the hero and language pills", async ({ page }) => {
  await page.route("**/health", (route) => route.fulfill({ json: { status: "ok" } }));
  await page.goto("/");

  // Brand + headline
  await expect(page.getByRole("heading", { name: /VoiceCare/i }).first()).toBeVisible();
  await expect(page.getByRole("heading", { level: 2 })).toBeVisible();

  // Language trust bar
  await expect(page.getByRole("button", { name: "Tamil" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Hindi" })).toBeVisible();

});

test("record button renders in the footer on a phone viewport", async ({ page }) => {
  await page.route("**/health", (route) => route.fulfill({ json: { status: "ok" } }));
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto("/");

  // The classic round mic pill (user-preferred placement) with translated
  // label + pressed state semantics.
  const mic = page.locator("button.btn-pill-accent[aria-pressed]");
  await expect(mic).toBeVisible();
  await expect(mic).toHaveAttribute("aria-pressed", "false");
});

test("unauthenticated /dashboard is redirected to /login by middleware", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
});

test("login flow lands on the dashboard overview", async ({ page }) => {
  await mockDashboardApis(page);

  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@e2e.test");
  await page.getByLabel("Password").fill("a-password");
  await page.getByRole("button", { name: /sign in/i }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole("heading", { name: "Support Operations" })).toBeVisible();
  // KPI strip rendered from the mocked analytics
  await expect(page.getByText("ESCALATED", { exact: true })).toBeVisible();
});

test("dashboard shell works on a phone viewport", async ({ page }) => {
  await mockDashboardApis(page);
  await page.setViewportSize({ width: 375, height: 720 });

  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@e2e.test");
  await page.getByLabel("Password").fill("a-password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  // Top-bar nav is reachable and the page doesn't overflow horizontally.
  await expect(page.getByRole("link", { name: "Tickets" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Support Operations" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});

test("tickets page sends the debounced search to the API", async ({ page }) => {
  await mockDashboardApis(page);

  const searches: string[] = [];
  await page.route("**/api/tickets/**", async (route) => {
    const url = route.request().url();
    if (url.includes("analytics") || url.includes("escalations")) return route.fallback();
    return route.fulfill({ json: [] });
  });
  await page.route("**/api/tickets/?*", (route) => {
    const url = new URL(route.request().url());
    const q = url.searchParams.get("search");
    if (q) searches.push(q);
    return route.fulfill({ json: [] });
  });

  // Authenticate via the real login flow (sets localStorage + cookie)
  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@e2e.test");
  await page.getByLabel("Password").fill("a-password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  await page.goto("/dashboard/tickets");
  await page.getByLabel("Search tickets").fill("Asha");

  await expect
    .poll(() => searches.includes("Asha"), { timeout: 5_000 })
    .toBe(true);
});
