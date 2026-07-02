import Link from "next/link";

export default function Header() {
  return (
    <header
      style={{
        position: "relative",
        zIndex: 2,
        width: "100%",
        maxWidth: 600,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "22px 24px 0",
      }}
    >
      {/* Brand lockup: coral mic mark + display wordmark */}
      <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
        <div
          aria-hidden="true"
          style={{
            width: 34,
            height: 34,
            borderRadius: 11,
            background: "var(--accent-gradient)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: "0 6px 20px -8px var(--accent-glow)",
          }}
        >
          <svg width="16" height="16" fill="white" viewBox="0 0 24 24">
            <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
            <line x1="12" y1="19" x2="12" y2="23" stroke="white" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        <div>
          <span
            style={{
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: "0.14em",
              color: "var(--accent)",
              textTransform: "uppercase",
              display: "block",
              lineHeight: 1,
            }}
          >
            {process.env.NEXT_PUBLIC_COMPANY_NAME || "CommerceMind"}
          </span>
          <h1
            className="display"
            style={{ fontSize: 19, color: "var(--text-primary)", marginTop: 3, lineHeight: 1 }}
          >
            {process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI"}
          </h1>
        </div>
      </div>

      <Link href="/dashboard" className="header-admin-link">
        Admin
        <svg width="12" height="12" fill="none" viewBox="0 0 16 16" aria-hidden="true">
          <path d="M6 3l5 5-5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </Link>
    </header>
  );
}
