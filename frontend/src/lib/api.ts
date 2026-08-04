/**
 * CommerceMind VoiceCare AI — API Client
 * Handles all communication with the FastAPI backend.
 */

// Defaults to the direct Render URL in production (same fallback next.config.ts's
// rewrites() already uses) rather than an empty string. An empty string would route
// every call through Vercel's own rewrite proxy, which imposes its own timeout
// independent of this file's timeoutMs — a request that needs to wait out a Render
// cold start (50-90s) can get killed by that proxy layer well before any client-side
// timeout here has a chance to matter. Calling Render directly removes that variable.
const _IS_PROD_BUILD = process.env.NODE_ENV === "production";
const _DEFAULT_BACKEND_URL = _IS_PROD_BUILD ? "https://voicecare-backend.onrender.com" : "http://localhost:8000";
const BACKEND_URL = typeof window !== "undefined"
  ? (process.env.NEXT_PUBLIC_BACKEND_URL || _DEFAULT_BACKEND_URL)
  : (process.env.BACKEND_URL || _DEFAULT_BACKEND_URL);

// ---- Auth token helpers (stored in localStorage + cookie for middleware) ----

const TOKEN_KEY = "vc_admin_token";
// Must match backend/app/api/auth.py's _TOKEN_EXPIRE_HOURS — the cookie is
// only a UX signal for middleware, but if it outlives the real JWT it can
// claim "logged in" for hours after the token has actually expired.
const TOKEN_MAX_AGE_SECONDS = 60 * 60 * 8; // 8h

type CacheEntry<T> = {
  expiresAt: number;
  promise?: Promise<T>;
  data?: T;
};

const dashboardReadCache = new Map<string, CacheEntry<unknown>>();

// Mirrored into sessionStorage so a hard reload, a 401 bounce or a login
// redirect doesn't drop every tab back to a cold spinner. sessionStorage (not
// local) so the cache dies with the tab and can't outlive the session.
const CACHE_STORAGE_KEY = "vc_dashboard_cache_v1";

function tokenFingerprint(): string {
  const token = getAuthToken();
  if (!token) return "anonymous";
  // We only need to notice that the token *changed* (logout/login), not to
  // recover it — so hash rather than copying the JWT into a second store.
  let h = 0;
  for (let i = 0; i < token.length; i++) h = (Math.imul(31, h) + token.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}

function dashboardCacheKey(path: string): string {
  // Keep cache entries scoped to the current admin session. A logout/login swap
  // must never show data fetched under an older token.
  return `${tokenFingerprint()}:${path}`;
}

let cacheHydrated = false;

function hydrateDashboardCache(): void {
  if (cacheHydrated || typeof window === "undefined") return;
  cacheHydrated = true;
  try {
    const raw = sessionStorage.getItem(CACHE_STORAGE_KEY);
    if (!raw) return;
    const stored = JSON.parse(raw) as Record<string, { data: unknown; expiresAt: number }>;
    for (const [key, entry] of Object.entries(stored)) {
      dashboardReadCache.set(key, { data: entry.data, expiresAt: entry.expiresAt });
    }
  } catch {
    // Corrupt or unavailable storage must never break a page load.
    try {
      sessionStorage.removeItem(CACHE_STORAGE_KEY);
    } catch {}
  }
}

function persistDashboardCache(): void {
  if (typeof window === "undefined") return;
  try {
    const stored: Record<string, { data: unknown; expiresAt: number }> = {};
    for (const [key, entry] of dashboardReadCache.entries()) {
      // In-flight promises aren't serialisable and aren't worth persisting.
      if (entry.data !== undefined) stored[key] = { data: entry.data, expiresAt: entry.expiresAt };
    }
    sessionStorage.setItem(CACHE_STORAGE_KEY, JSON.stringify(stored));
  } catch {
    // Quota exceeded or private mode — the in-memory cache still works.
  }
}

function clearDashboardReadCache(matcher?: (path: string) => boolean): void {
  if (!matcher) {
    dashboardReadCache.clear();
    persistDashboardCache();
    return;
  }

  for (const key of dashboardReadCache.keys()) {
    const path = key.slice(key.indexOf(":") + 1);
    if (matcher(path)) dashboardReadCache.delete(key);
  }
  persistDashboardCache();
}

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  // Also set a cookie so Next.js middleware can guard /dashboard routes
  document.cookie = `vc_logged_in=1; path=/; max-age=${TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
}

export function clearAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  document.cookie = "vc_logged_in=; path=/; max-age=0";
  clearDashboardReadCache();
}

export interface VoiceQueryResponse {
  session_id: string;
  ticket_id: string;
  ticket_number?: string;   // short customer-facing code, e.g. TKT-9QXM2
  ticket_created?: boolean; // false when this turn's ticket write failed
  order_number?: string;    // short order code, e.g. ORD-7K3F
  response_text: string;
  response_audio_base64?: string;
  language: string;
  intent: string;
  sentiment: string;
  priority: string;
  recommended_action: string;
  policy_reference?: string;
  confidence_score: number;
  is_escalated: boolean;
  escalation_reason?: string;
  agent_trace: AgentTraceStep[];
  // End-to-end wall clock for the turn. On the WebSocket answer frame this is
  // time-to-answer; the terminal `done` frame replaces it with the full figure.
  total_duration_ms?: number;
}

export interface AgentTraceStep {
  agent_name: string;
  stage_number: number;
  input_summary: string;
  output_summary: string;
  decision?: string;
  reasoning?: string;
  duration_ms?: number;
  timestamp: string;
}

export interface TicketSummary {
  ticket_id: string;
  ticket_number?: string;
  user_name: string;
  phone: string;
  ticket_type: string;
  priority: string;
  status: string;
  language: string;
  sentiment?: string;
  summary?: string;
  created_at: string;
  resolved_at?: string;
  assigned_to?: string;
}

export interface TicketDetail extends TicketSummary {
  escalated_at?: string;
  assigned_to?: string;
  order_id?: string;
  order_number?: string;
  order_status?: string;
  order_amount?: number;
  order_date?: string;
  recommended_action?: string;
  policy_reference?: string;
  response_text?: string;
  internal_note?: string;
  confidence_score?: number;
  agent_trace: AgentTraceStep[];
  messages: MessageItem[];
}

export interface MessageItem {
  message_id: string;
  sender_type: string;
  message_text: string;
  language: string;
  timestamp: string;
}

export interface AnalyticsOverview {
  total_tickets: number;
  open_tickets: number;
  escalated_tickets: number;
  resolved_tickets: number;
  avg_resolution_time_minutes?: number;
  tickets_by_language: Record<string, number>;
  tickets_by_category: Record<string, number>;
  tickets_by_priority: Record<string, number>;
  tickets_by_sentiment: Record<string, number>;
  tickets_over_time: { date: string; count: number }[];
  resolution_rate: number;
  escalation_rate: number;
}

export interface HandoffNote {
  ticket_id: string;
  customer_name: string;
  customer_phone: string;
  language: string;
  issue_summary: string;
  sentiment: string;
  priority: string;
  order_details?: string;
  ai_attempted_resolution: string;
  policy_referenced?: string;
  escalation_reason: string;
  recommended_next_steps: string;
  conversation_history: { sender: string; text: string; time: string }[];
  generated_at: string;
}

// ---- API Functions ----

async function apiFetch<T>(path: string, options?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const controller = new AbortController();
  // 20 s default — long enough for dashboard API calls; callers can override.
  const timeoutMs = options?.timeoutMs ?? 20_000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  // Chain a caller-supplied signal onto our own rather than replacing it.
  // Passing `options.signal` straight to fetch() detaches the timeout — the
  // timer still fires but nothing listens, so the request can hang forever.
  // That is what happened to the escalations poll during a backend cold start.
  // (Listener rather than AbortSignal.any() for older-browser support.)
  const callerSignal = options?.signal;
  if (callerSignal) {
    if (callerSignal.aborted) controller.abort();
    else callerSignal.addEventListener("abort", () => controller.abort(), { once: true });
  }

  try {
    // Strip our custom option so it never reaches fetch()
    const fetchOptions = { ...(options ?? {}) };
    delete fetchOptions.timeoutMs;
    const res = await fetch(`${BACKEND_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      headers: { ...headers, ...(options?.headers as Record<string, string> | undefined) },
    });

    if (res.status === 401) {
      clearAuthToken();
      // Redirect to login with a clear reason, but never loop if we're already
      // on the login page (e.g. the post-login verify call returning 401).
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.assign("/login?expired=1");
      }
      throw new Error("Session expired. Please log in again.");
    }
    if (res.status === 429) {
      const retryAfter = res.headers.get("Retry-After");
      const wait = retryAfter ? ` Please wait ${retryAfter} seconds.` : "";
      throw new Error(`Too many requests.${wait}`);
    }
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `API Error: ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Stale-while-revalidate read cache.
 *
 * A hard TTL miss used to mean a blank spinner on every tab, which is what made
 * the dashboard feel slow even when data was seconds old. Now an expired entry
 * is served immediately and refreshed behind the screen.
 */
async function cachedDashboardFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number; ttlMs?: number },
): Promise<T> {
  hydrateDashboardCache();

  const ttlMs = options?.ttlMs ?? 60_000;
  const key = dashboardCacheKey(path);
  const now = Date.now();
  const cached = dashboardReadCache.get(key) as CacheEntry<T> | undefined;

  const fetchOptions = { ...(options ?? {}) };
  delete fetchOptions.ttlMs;

  const revalidate = (): Promise<T> =>
    apiFetch<T>(path, fetchOptions)
      .then((data) => {
        dashboardReadCache.set(key, { data, expiresAt: Date.now() + ttlMs });
        persistDashboardCache();
        return data;
      })
      .catch((err) => {
        // Keep whatever we already hold — a failed refresh should not blank a
        // working screen. Just mark it stale so the next read tries again.
        const entry = dashboardReadCache.get(key) as CacheEntry<T> | undefined;
        if (entry?.data !== undefined) {
          dashboardReadCache.set(key, { data: entry.data, expiresAt: 0 });
        } else {
          dashboardReadCache.delete(key);
        }
        throw err;
      });

  // A polling caller (identified by passing its own AbortSignal) always goes to
  // the network — that is the point of polling — but its result is written
  // through to the cache so the next cold mount of that tab paints instantly.
  // It also stays out of the shared promise below: one caller's abort must
  // never cancel another caller's request.
  if (options?.signal) return revalidate();

  // Fresh.
  if (cached?.data !== undefined && cached.expiresAt > now) return cached.data;

  // Already in flight — join it instead of opening a second request.
  if (cached?.promise && cached.expiresAt > now) return cached.promise;

  // Stale but present: hand back the stale copy now, refresh behind it.
  if (cached?.data !== undefined) {
    const refresh = revalidate();
    // Park the in-flight refresh alongside the stale data so concurrent callers
    // reuse it rather than each firing their own.
    dashboardReadCache.set(key, { data: cached.data, promise: refresh, expiresAt: now + ttlMs });
    // Background refresh: the caller already has its answer, so a rejection
    // here must not surface as an unhandled promise.
    void refresh.catch(() => {});
    return cached.data;
  }

  // Cold — nothing to show, so this one has to wait.
  const promise = revalidate();
  dashboardReadCache.set(key, { promise, expiresAt: now + ttlMs });
  return promise;
}

export async function getTickets(params?: {
  status?: string;
  priority?: string;
  language?: string;
  search?: string;
}): Promise<TicketSummary[]> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.priority) query.set("priority", params.priority);
  if (params?.language) query.set("language", params.language);
  if (params?.search) query.set("search", params.search);
  const qs = query.toString();
  return cachedDashboardFetch<TicketSummary[]>(`/api/tickets/${qs ? `?${qs}` : ""}`, { ttlMs: 45_000 });
}

export async function getEscalations(signal?: AbortSignal): Promise<TicketSummary[]> {
  // One TTL for both call shapes: a polled result is written through to the
  // cache with the same freshness as a plain read, so entering the tab shows
  // the last polled value instantly instead of starting from a spinner.
  return cachedDashboardFetch<TicketSummary[]>("/api/tickets/escalations", { signal, ttlMs: 15_000 });
}

export async function getTicketDetail(ticketId: string): Promise<TicketDetail> {
  return cachedDashboardFetch<TicketDetail>(`/api/tickets/${ticketId}`, { ttlMs: 60_000 });
}

export async function getAnalytics(): Promise<AnalyticsOverview> {
  return cachedDashboardFetch<AnalyticsOverview>("/api/tickets/analytics", { ttlMs: 60_000 });
}

export async function getHandoffNote(ticketId: string): Promise<HandoffNote> {
  return cachedDashboardFetch<HandoffNote>(`/api/tickets/${ticketId}/handoff`, { ttlMs: 120_000 });
}

export async function adminLogin(email: string, password: string): Promise<void> {
  // Abort after 65s — Render free-tier cold starts can take 50-90 s, so we
  // need headroom beyond 45 s. The UI shows a "waking up server" notice after
  // 10 s so the user knows why it's slow (see login/page.tsx).
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 65_000);
  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      signal: controller.signal,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login failed." }));
      throw new Error(err.detail || "Login failed.");
    }
    const data = await res.json();
    setAuthToken(data.access_token);
  } catch (e: unknown) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("Server is still starting up. Please wait a moment and try again.");
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }

  // Verify the freshly-issued token end-to-end against a lightweight, auth-only
  // endpoint BEFORE the caller redirects. This guarantees we never navigate to
  // the dashboard with a token the backend will reject (e.g. a NEXTAUTH_SECRET
  // mismatch on the server), which previously looked like a silent "glitch".
  // A definitive 401 is fatal; a transient network/timeout is tolerated.
  const vController = new AbortController();
  const vTimer = setTimeout(() => vController.abort(), 10_000);
  try {
    const token = getAuthToken();
    const verify = await fetch(`${BACKEND_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: vController.signal,
    });
    if (verify.status === 401) {
      clearAuthToken();
      throw new Error("Signed in, but the server rejected the session. Please try again.");
    }
  } catch (e: unknown) {
    // Re-throw only our explicit rejection; ignore transient network/timeout so
    // a flaky verify never blocks an otherwise-valid login.
    if (e instanceof Error && e.message.startsWith("Signed in, but")) throw e;
  } finally {
    clearTimeout(vTimer);
  }
}

export async function adminLogout(): Promise<void> {
  const token = getAuthToken();
  if (!token) return;
  try {
    // keepalive lets the revocation request survive the immediate navigation
    // to /login. Best-effort: local sign-out proceeds even if this fails.
    await fetch(`${BACKEND_URL}/api/auth/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      keepalive: true,
    });
  } catch {
    /* token still expires server-side at its 8h limit */
  } finally {
    clearDashboardReadCache();
  }
}

export async function claimTicket(ticketId: string): Promise<{ ticket_id: string; status: string; assigned_to: string }> {
  const result = await apiFetch<{ ticket_id: string; status: string; assigned_to: string }>(`/api/tickets/${ticketId}/claim`, { method: "PATCH" });
  clearDashboardReadCache((path) => (
    path.startsWith("/api/tickets") || path === "/api/tickets/analytics"
  ));
  return result;
}

export async function replyToTicket(
  ticketId: string,
  messageText: string,
): Promise<{ message_id: string; sender_type: string; message_text: string; language: string; timestamp: string; ticket_status: string }> {
  const result = await apiFetch<{ message_id: string; sender_type: string; message_text: string; language: string; timestamp: string; ticket_status: string }>(`/api/tickets/${ticketId}/reply`, {
    method: "POST",
    body: JSON.stringify({ message_text: messageText }),
  });
  clearDashboardReadCache((path) => path.startsWith("/api/tickets"));
  return result;
}

export async function resolveTicket(ticketId: string): Promise<{ ticket_id: string; status: string }> {
  const result = await apiFetch<{ ticket_id: string; status: string }>(`/api/tickets/${ticketId}/resolve`, { method: "PATCH" });
  clearDashboardReadCache((path) => (
    path.startsWith("/api/tickets") || path === "/api/tickets/analytics"
  ));
  return result;
}

export interface CustomerSummary {
  user_id: string;
  customer_code?: string;
  name: string;
  phone: string;
  email: string | null;
  city: string | null;
  customer_segment: string;
  preferred_language: string;
  ticket_count: number;
  last_contact: string | null;
}

export interface CustomerProfile extends CustomerSummary {
  created_at: string;
  orders: {
    order_id: string;
    order_number?: string;
    order_date: string;
    status: string;
    total_amount: number;
    shipping_address?: string | null;
    items: {
      product_name: string;
      category: string | null;
      sku: string | null;
      quantity: number;
      price_at_purchase: number;
      line_total: number;
    }[];
    shipment: { status: string; courier: string; tracking_number: string | null; expected_delivery: string | null; actual_delivery?: string | null } | null;
    payment: { method: string; status: string; amount: number } | null;
  }[];
  tickets: {
    ticket_id: string;
    ticket_type: string;
    status: string;
    priority: string;
    sentiment: string | null;
    summary: string | null;
    created_at: string;
    resolved_at: string | null;
  }[];
  sentiment_timeline: { label: string; confidence: number | null; recorded_at: string }[];
}

export async function getCustomers(search?: string): Promise<CustomerSummary[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : "";
  return cachedDashboardFetch<CustomerSummary[]>(`/api/customers/${qs}`, { ttlMs: search ? 30_000 : 60_000 });
}

export async function getCustomerProfile(customerId: string): Promise<CustomerProfile> {
  return cachedDashboardFetch<CustomerProfile>(`/api/customers/${customerId}`, { ttlMs: 120_000 });
}

export async function clearConversation(sessionId: string): Promise<void> {
  await apiFetch(`/api/voice/session/${sessionId}`, { method: "DELETE" });
}

export interface SessionHistoryTurn {
  role: "customer" | "ai";
  content: string;
  timestamp?: string;
}

export async function getSessionHistory(sessionId: string): Promise<SessionHistoryTurn[]> {
  const data = await apiFetch<{ session_id: string; turns: SessionHistoryTurn[] }>(
    `/api/voice/session/${sessionId}/history`,
  );
  return data.turns;
}

export function createWebSocket(sessionId: string): WebSocket {
  // WebSocket connections MUST go directly to the backend URL — Vercel's
  // serverless edge cannot proxy the HTTP→WS upgrade that rewrites() handles
  // for regular HTTP requests. Use NEXT_PUBLIC_BACKEND_URL (set it in Vercel
  // env vars to https://voicecare-backend.onrender.com). In local dev, falls
  // back to localhost:8000.
  const base = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  const wsUrl = base.replace(/^http/, "ws");
  return new WebSocket(`${wsUrl}/api/voice/ws/${sessionId}`);
}
