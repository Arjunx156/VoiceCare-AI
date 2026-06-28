"use client";

import { Suspense, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { adminLogin, getAuthToken } from "@/lib/api";

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
    if (getAuthToken()) window.location.assign(safeDest(params.get("from")));
  }, [params]);

  // Show a "server waking up" message if login is taking > 10 s (Render cold start).
  useEffect(() => {
    if (!loading) { setWarmingUp(false); return; }
    const t = setTimeout(() => setWarmingUp(true), 10_000);
    return () => clearTimeout(t);
  }, [loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setLoading(true);
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
    <div className="panel" style={{ width: "100%", maxWidth: 400, padding: "36px 32px" }}>
      <span className="eyebrow">ADMIN ACCESS</span>
      <h1 style={{ fontSize: 24, fontWeight: 800, color: "var(--text-primary)", marginTop: 8, marginBottom: 6 }}>
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
          <label style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "0.04em" }}>
            EMAIL
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
            style={{
              background: "var(--bg-base)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 10,
              padding: "10px 14px",
              fontSize: 14,
              color: "var(--text-primary)",
              outline: "none",
              width: "100%",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "0.04em" }}>
            PASSWORD
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            style={{
              background: "var(--bg-base)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 10,
              padding: "10px 14px",
              fontSize: 14,
              color: "var(--text-primary)",
              outline: "none",
              width: "100%",
              boxSizing: "border-box",
            }}
          />
        </div>

        {error && (
          <p style={{ fontSize: 13, color: "var(--status-high)", margin: 0 }}>{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn-pill-accent"
          style={{ marginTop: 8, opacity: loading ? 0.6 : 1, cursor: loading ? "not-allowed" : "pointer" }}
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>

        {warmingUp && (
          <p style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", margin: 0, lineHeight: 1.5 }}>
            Server is waking up — this can take up to 60 s on free hosting. Please wait…
          </p>
        )}
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "var(--bg-base)",
    }}>
      <Suspense fallback={null}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
