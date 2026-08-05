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
import {
  BarChart3,
  ChevronLeft,
  LayoutGrid,
  LogOut,
  MessageSquareText,
  TriangleAlert,
  Users,
  type LucideIcon,
} from "lucide-react";
import {
  adminLogout,
  clearAuthToken,
  getAnalytics,
  getAuthToken,
  getCustomers,
  getEscalations,
  getTickets,
} from "@/lib/api";
import { useMotionSafe } from "@/lib/motion";
import { Brandmark } from "@/components/ui";

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

const NAV_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/dashboard",             label: "Overview",    icon: LayoutGrid },
  { href: "/dashboard/tickets",     label: "Tickets",     icon: MessageSquareText },
  { href: "/dashboard/customers",   label: "Customers",   icon: Users },
  { href: "/dashboard/escalations", label: "Escalations", icon: TriangleAlert },
  { href: "/dashboard/analytics",   label: "Analytics",   icon: BarChart3 },
];

/** One family, one stroke weight. Hand-drawn SVG paths drifted in both. */
const ICON_STROKE = 1.75;

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { reduced } = useMotionSafe();

  // Client-side guard: if there's no token, don't render the dashboard shell —
  // send the user to login. (API data is already protected server-side by
  // require_admin; this just avoids showing an empty/erroring dashboard.)
  useEffect(() => {
    if (!getAuthToken()) window.location.assign("/login");
  }, []);

  useEffect(() => {
    if (!getAuthToken()) return;

    const warmDashboardTabs = () => {
      void Promise.allSettled([
        getAnalytics(),
        getTickets(),
        getCustomers(),
        getEscalations(),
      ]);
    };

    const win = window as Window & {
      requestIdleCallback?: (cb: () => void, options?: { timeout: number }) => number;
      cancelIdleCallback?: (id: number) => void;
    };

    if (win.requestIdleCallback) {
      const idleId = win.requestIdleCallback(warmDashboardTabs, { timeout: 2_000 });
      return () => win.cancelIdleCallback?.(idleId);
    }

    const timer = window.setTimeout(warmDashboardTabs, 600);
    return () => window.clearTimeout(timer);
  }, []);

  function handleLogout() {
    // Fire-and-forget server-side revocation (keepalive survives the redirect);
    // never block local sign-out on the network.
    void adminLogout();
    clearAuthToken();
    window.location.assign("/login");
  }

  return (
    <div className="dash-shell" style={{ minHeight: "100vh", display: "flex", background: "var(--bg-base)", position: "relative", zIndex: 1 }}>
      {/* Sidebar (top bar under 768px — see DASHBOARD RESPONSIVE in globals.css) */}
      <aside
        className="dash-sidebar"
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
        {/* Brand lockup — level-meter mark, no container box. See the
            BRANDMARK note in globals.css for why the mic squircle went. */}
        <Link
          href="/"
          className="dash-brand"
          style={{ display: "flex", alignItems: "center", gap: 11, padding: "0 20px 22px", textDecoration: "none" }}
        >
          <Brandmark />
        </Link>

        {/* Divider */}
        <div className="divider dash-divider" style={{ marginBottom: 12 }} />

        {/* Nav */}
        <nav className="dash-nav" aria-label="Dashboard navigation" style={{ display: "flex", flexDirection: "column", gap: 2, padding: "0 12px" }}>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                style={{
                  position: "relative",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "9px 12px",
                  borderRadius: "var(--radius-inner)",
                  fontSize: 13.5,
                  fontWeight: isActive ? 600 : 450,
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  background: isActive ? "var(--bg-panel-raised)" : "transparent",
                  textDecoration: "none",
                  transition: "background 120ms, color 120ms",
                }}
              >
                {/* Active accent left border (slides between items; static under reduced motion) */}
                {isActive && (
                  <motion.div
                    layoutId={reduced ? undefined : "activeNav"}
                    aria-hidden="true"
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
                <Icon
                  size={16}
                  strokeWidth={ICON_STROKE}
                  aria-hidden="true"
                  style={{ color: isActive ? "var(--accent)" : "var(--text-muted)", flexShrink: 0 }}
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom — back to voice + logout */}
        <div className="dash-bottom" style={{ marginTop: "auto", padding: "12px 12px 0" }}>
          <div className="divider dash-divider" style={{ marginBottom: 12 }} />
          <Link
            href="/"
            className="dash-voice-link"
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
            <ChevronLeft size={15} strokeWidth={ICON_STROKE} aria-hidden="true" />
            Voice interface
          </Link>
          <button
            onClick={handleLogout}
            aria-label="Sign out"
            style={{
              whiteSpace: "nowrap",
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
            <LogOut size={15} strokeWidth={ICON_STROKE} aria-hidden="true" />
            {/* Label drops on the compact top bar; the icon plus aria-label
                keeps the control reachable without crowding the nav. */}
            <span className="dash-signout-label">Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="dash-main" style={{ flex: 1, overflow: "auto", padding: "32px 36px" }}>
        <DashboardErrorBoundary>{children}</DashboardErrorBoundary>
      </main>
    </div>
  );
}
