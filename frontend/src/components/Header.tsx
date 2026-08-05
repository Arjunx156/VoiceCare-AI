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
      {/* Same lockup as the console sidebar: meter mark, wordmark, mono
          company tag. The company name no longer wears the brand coral —
          coral is reserved for live state and the primary action. */}
      <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
        <span className="brandmark" aria-hidden="true">
          <span /><span /><span /><span /><span />
        </span>
        <div className="dash-brand-text">
          <h1 className="wordmark" style={{ fontSize: 16 }}>
            {process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI"}
          </h1>
          <span className="wordmark-tag">
            {process.env.NEXT_PUBLIC_COMPANY_NAME || "CommerceMind"}
          </span>
        </div>
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
