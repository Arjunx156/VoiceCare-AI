"use client";

import { Suspense, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { adminLogin, getAuthToken, clearAuthToken } from "@/lib/api";
import { Button, GlowBackdrop, GrainOverlay, Panel } from "@/components/ui";

// Only honor internal, single-slash paths as a redirect target — never an
// absolute URL or protocol-relative "//host" (open-redirect protection).
function safeDest(from: string | null): string {
  if (from && from.startsWith("/") && !from.startsWith("//")) return from;
  return "/dashboard";
}

function LoginForm() {
  const params = useSearchParams();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);

  const expired = params.get("expired") === "1";
  const [warmingUp, setWarmingUp] = useState(false);

  // Already logged in → go straight to dashboard (hard nav, see handleSubmit).
  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;

    // If the middleware cookie expired but the localStorage token is still
    // around, clear the stale token to prevent an infinite redirect loop
    // (login → dashboard → middleware redirect → login → …).
    const hasCookie = document.cookie
      .split(";")
      .some((c) => c.trim().startsWith("vc_logged_in=1"));
    if (!hasCookie) {
      clearAuthToken();
      return;
    }

    window.location.assign(safeDest(params.get("from")));
  }, [params]);

  // Show a "server waking up" message if login is taking > 10 s (Render cold start).
  useEffect(() => {
    if (!loading) return;
    const t = setTimeout(() => setWarmingUp(true), 10_000);
    return () => clearTimeout(t);
  }, [loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setLoading(true);
    setWarmingUp(false);
    setError(null);
    try {
      await adminLogin(email.trim(), password);
      // Hard navigation (full document load), NOT router.replace. A soft App
      // Router navigation here could silently no-op and strand the user on the
      // login page while already authenticated — the original bug. A full load
      // mounts the dashboard fresh with the token present.
      window.location.assign(safeDest(params.get("from")));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed.");
      setLoading(false);
    }
  }

  return (
    <Panel elevated style={{ width: "100%", maxWidth: 420, padding: "38px 34px" }}>
      <span className="eyebrow">Admin access</span>
      <h1 className="display-h2" style={{ color: "var(--text-primary)", marginTop: 6, marginBottom: 8 }}>
        Sign in to VoiceCare
      </h1>
      <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: expired ? 16 : 28 }}>
        Dashboard access is restricted to administrators.
      </p>

      {expired && (
        <p
          style={{
            fontSize: 13,
            color: "var(--status-medium, #d4a017)",
            background: "rgba(212,160,23,0.10)",
            border: "1px solid rgba(212,160,23,0.25)",
            borderRadius: 10,
            padding: "10px 12px",
            marginBottom: 20,
          }}
        >
          Your session expired — please sign in again.
        </p>
      )}

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <label htmlFor="login-email" className="field-label">
            Email
          </label>
          <input
            id="login-email"
            className="text-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <label htmlFor="login-password" className="field-label">
            Password
          </label>
          <input
            id="login-password"
            className="text-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        {error && (
          <p role="alert" style={{ fontSize: 13, color: "var(--status-high)", margin: 0 }}>
            {error}
          </p>
        )}

        <Button type="submit" isLoading={loading} style={{ marginTop: 8 }}>
          {loading ? "Signing in…" : "Sign in"}
        </Button>

        {loading && warmingUp && (
          <p aria-live="polite" style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", margin: 0, lineHeight: 1.5 }}>
            Server is waking up — this can take up to 60 s on free hosting. Please wait…
          </p>
        )}
      </form>
    </Panel>
  );
}

/** Brand column shown beside the form on wide screens — pure atmosphere. */
function LoginBrand() {
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        gap: 22,
        maxWidth: 460,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div
          aria-hidden="true"
          style={{
            width: 40,
            height: 40,
            borderRadius: 13,
            background: "var(--accent-gradient)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 8px 24px -10px var(--accent-glow)",
          }}
        >
          <svg width="19" height="19" fill="white" viewBox="0 0 24 24">
            <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
            <line x1="12" y1="19" x2="12" y2="23" stroke="white" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.14em", color: "var(--accent)", textTransform: "uppercase" }}>
          {process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI"}
        </span>
      </div>

      <h2 className="display-hero" style={{ color: "var(--text-primary)", fontSize: "clamp(2rem, 1.4rem + 2.6vw, 3.25rem)" }}>
        Support that{" "}
        <span className="text-gradient">speaks every language</span>.
      </h2>
      <p style={{ fontSize: 15, lineHeight: 1.6, color: "var(--text-secondary)", maxWidth: 400 }}>
        The operations console for a voice-first, multilingual customer-support pipeline.
        Track tickets, escalations, and live sentiment in one place.
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div
      style={{
        position: "relative",
        overflow: "hidden",
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-base)",
        padding: "48px 24px",
      }}
    >
      <GrainOverlay />
      <GlowBackdrop size={640} style={{ top: "-10%", left: "-8%" }} />
      <GlowBackdrop size={520} animate={false} style={{ bottom: "-14%", right: "-6%", opacity: 0.35 }} />

      <div
        className="login-shell"
        style={{
          position: "relative",
          zIndex: 1,
          width: "100%",
          maxWidth: 960,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 64,
        }}
      >
        <LoginBrand />
        <Suspense fallback={null}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
