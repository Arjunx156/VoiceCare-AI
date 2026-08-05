import Link from "next/link";

import { Brandmark } from "@/components/ui";

export default function Header() {
  return (
    <header
      style={{
        width: "100%",
        maxWidth: 560,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "20px 24px 0",
      }}
    >
      <Brandmark as="h1" />
      <Link
        href="/dashboard"
        style={{
          padding: "8px 18px",
          borderRadius: 999,
          fontSize: 12,
          fontWeight: 600,
          color: "var(--text-secondary)",
          border: "1px solid var(--border-subtle)",
          background: "transparent",
          textDecoration: "none",
          transition: "border-color 150ms, color 150ms",
        }}
      >
        Admin →
      </Link>
    </header>
  );
}
