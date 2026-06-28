"use client";

/**
 * CommerceMind VoiceCare AI — Dashboard Layout v2
 * Design brief: dark sidebar, accent active state (left border + accent text),
 * no glassmorphism, editorial feel.
 */

import React, { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { clearAuthToken, getAuthToken } from "@/lib/api";

class DashboardErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; message: string }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(err: unknown) {
    return { hasError: true, message: err instanceof Error ? err.message : "Unknown error" };
  }

  componentDidCatch(err: unknown, info: React.ErrorInfo) {
    console.error("Dashboard error boundary caught:", err, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "48px 36px", color: "var(--text-secondary)" }}>
          <p style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
            Something went wrong
          </p>
          <p style={{ fontSize: 13, marginBottom: 20 }}>{this.state.message}</p>
          <button
            className="btn-pill"
            onClick={() => this.setState({ hasError: false, message: "" })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const NAV_ITEMS = [
  { href: "/dashboard",             label: "Overview",    icon: "overview" },
  { href: "/dashboard/tickets",     label: "Tickets",     icon: "tickets" },
  { href: "/dashboard/escalations", label: "Escalations", icon: "escalations" },
  { href: "/dashboard/analytics",   label: "Analytics",   icon: "analytics" },
];

// Minimal SVG icons (no emojis — editorial clean)
function NavIcon({ name, active }: { name: string; active: boolean }) {
  const color = active ? "var(--accent)" : "var(--text-muted)";
  if (name === "overview")
    return <svg width="16" height="16" fill="none" viewBox="0 0 16 16"><rect x="1" y="1" width="6" height="6" rx="1.5" fill={color}/><rect x="9" y="1" width="6" height="6" rx="1.5" fill={color} opacity=".5"/><rect x="1" y="9" width="6" height="6" rx="1.5" fill={color} opacity=".5"/><rect x="9" y="9" width="6" height="6" rx="1.5" fill={color} opacity=".3"/></svg>;
  if (name === "tickets")
    return <svg width="16" height="16" fill="none" viewBox="0 0 16 16"><rect x="2" y="3" width="12" height="10" rx="2" stroke={color} strokeWidth="1.5"/><line x1="5" y1="7" x2="11" y2="7" stroke={color} strokeWidth="1.5" strokeLinecap="round"/><line x1="5" y1="10" x2="9" y2="10" stroke={color} strokeWidth="1.5" strokeLinecap="round"/></svg>;
  if (name === "escalations")
    return <svg width="16" height="16" fill="none" viewBox="0 0 16 16"><path d="M8 2L14 13H2L8 2Z" stroke={color} strokeWidth="1.5" strokeLinejoin="round"/><line x1="8" y1="7" x2="8" y2="10" stroke={color} strokeWidth="1.5" strokeLinecap="round"/><circle cx="8" cy="12" r="0.75" fill={color}/></svg>;
  // analytics
  return <svg width="16" height="16" fill="none" viewBox="0 0 16 16"><rect x="2" y="9" width="3" height="5" rx="1" fill={color} opacity=".5"/><rect x="6.5" y="6" width="3" height="8" rx="1" fill={color} opacity=".7"/><rect x="11" y="3" width="3" height="11" rx="1" fill={color}/></svg>;
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Client-side guard: if there's no token, don't render the dashboard shell —
  // send the user to login. (API data is already protected server-side by
  // require_admin; this just avoids showing an empty/erroring dashboard.)
  useEffect(() => {
    if (!getAuthToken()) window.location.assign("/login");
  }, []);

  function handleLogout() {
    clearAuthToken();
    window.location.assign("/login");
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "var(--bg-base)", position: "relative", zIndex: 1 }}>
      {/* Sidebar */}
      <aside
        style={{
          width: 220,
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          padding: "24px 0",
          background: "var(--bg-panel)",
          borderRight: "1px solid var(--border-subtle)",
        }}
      >
        {/* Logo */}
        <Link
          href="/"
          style={{ display: "flex", alignItems: "center", gap: 10, padding: "0 20px 24px", textDecoration: "none" }}
        >
          {/* Mic mark */}
          <div
            style={{
              width: 32, height: 32,
              borderRadius: 10,
              background: "var(--accent)",
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <svg width="16" height="16" fill="white" viewBox="0 0 24 24">
              <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round"/>
              <line x1="12" y1="19" x2="12" y2="23" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>{process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI"}</p>
            <p style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.04em" }}>Admin Dashboard</p>
          </div>
        </Link>

        {/* Divider */}
        <div className="divider" style={{ marginBottom: 12 }} />

        {/* Nav */}
        <nav style={{ display: "flex", flexDirection: "column", gap: 2, padding: "0 12px" }}>
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  position: "relative",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "9px 12px",
                  borderRadius: 10,
                  fontSize: 13,
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  background: isActive ? "var(--bg-panel-raised)" : "transparent",
                  textDecoration: "none",
                  transition: "background 120ms, color 120ms",
                }}
              >
                {/* Active accent left border */}
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    style={{
                      position: "absolute",
                      left: 0,
                      width: 3,
                      height: 20,
                      borderRadius: "0 3px 3px 0",
                      background: "var(--accent)",
                    }}
                    transition={{ type: "spring", stiffness: 320, damping: 32 }}
                  />
                )}
                <NavIcon name={item.icon} active={isActive} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom — back to voice + logout */}
        <div style={{ marginTop: "auto", padding: "12px 12px 0" }}>
          <div className="divider" style={{ marginBottom: 12 }} />
          <Link
            href="/"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "9px 12px",
              borderRadius: 10,
              fontSize: 12,
              color: "var(--text-muted)",
              textDecoration: "none",
              transition: "color 120ms",
            }}
          >
            <svg width="14" height="14" fill="none" viewBox="0 0 16 16">
              <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Voice Interface
          </Link>
          <button
            onClick={handleLogout}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "9px 12px",
              borderRadius: 10,
              fontSize: 12,
              color: "var(--text-muted)",
              background: "none",
              border: "none",
              cursor: "pointer",
              width: "100%",
              textAlign: "left",
              transition: "color 120ms",
              marginTop: 2,
            }}
          >
            <svg width="14" height="14" fill="none" viewBox="0 0 16 16">
              <path d="M6 2H3a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              <path d="M10 11l3-3-3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <line x1="13" y1="8" x2="6" y2="8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, overflow: "auto", padding: "32px 36px" }}>
        <DashboardErrorBoundary>{children}</DashboardErrorBoundary>
      </main>
    </div>
  );
}
