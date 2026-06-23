"use client";

/**
 * CommerceMind VoiceCare AI — Dashboard Layout
 * Sidebar navigation for admin pages.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: "📊" },
  { href: "/dashboard/tickets", label: "Tickets", icon: "🎫" },
  { href: "/dashboard/escalations", label: "Escalations", icon: "🚨" },
  { href: "/dashboard/analytics", label: "Analytics", icon: "📈" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen flex" style={{ zIndex: 1, position: "relative" }}>
      {/* Sidebar */}
      <aside
        className="w-64 flex-shrink-0 flex flex-col p-4 gap-1"
        style={{
          background: "var(--bg-secondary)",
          borderRight: "1px solid var(--border-subtle)",
        }}
      >
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 px-3 py-4 mb-4">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm"
            style={{
              background: "linear-gradient(135deg, var(--primary), var(--accent))",
            }}
          >
            🎙️
          </div>
          <div>
            <h2 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
              VoiceCare AI
            </h2>
            <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
              Admin Dashboard
            </p>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className="relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all"
                style={{
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  background: isActive ? "var(--bg-card)" : "transparent",
                }}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute left-0 w-1 h-6 rounded-r-full"
                    style={{ background: "var(--primary)" }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="mt-auto pt-4" style={{ borderTop: "1px solid var(--border-subtle)" }}>
          <Link
            href="/"
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all hover:opacity-80"
            style={{ color: "var(--text-muted)" }}
          >
            <span>🎙️</span>
            <span>Voice Interface</span>
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
