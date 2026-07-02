import Link from "next/link";

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
      <div>
        <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", color: "var(--accent)", textTransform: "uppercase" }}>
          {process.env.NEXT_PUBLIC_COMPANY_NAME || "CommerceMind"}
        </span>
        <h1 style={{ fontSize: 18, fontWeight: 800, color: "var(--text-primary)", marginTop: 2 }}>
          {process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI"}
        </h1>
      </div>
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
