/**
 * Skeleton placeholders for list surfaces. The row anatomy mirrors the real
 * ticket/customer rows (eyebrow bar, title, subtitle on the left; pills and a
 * date on the right) so content doesn't jump when data arrives.
 * Pulse animation freezes under prefers-reduced-motion (global override).
 */

function Bar({ w, h = 10, style }: { w: number | string; h?: number; style?: React.CSSProperties }) {
  return <span className="skeleton" style={{ display: "block", width: w, height: h, ...style }} />;
}

function SkeletonRow({ isLast }: { isLast: boolean }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        padding: "16px 24px",
        borderBottom: isLast ? "none" : "1px solid var(--border-subtle)",
      }}
    >
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 7 }}>
        <Bar w={64} h={8} />
        <Bar w="45%" h={12} />
        <Bar w="65%" h={9} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
        <Bar w={72} h={18} style={{ borderRadius: 999 }} />
        <Bar w={56} h={18} style={{ borderRadius: 999 }} />
      </div>
      <Bar w={52} h={9} />
    </div>
  );
}

/** Placeholder rows shown while a list loads. */
export function SkeletonList({ rows = 6, label = "Loading" }: { rows?: number; label?: string }) {
  return (
    <div role="status" aria-label={label}>
      {Array.from({ length: rows }, (_, i) => (
        <SkeletonRow key={i} isLast={i === rows - 1} />
      ))}
      <span className="sr-only">{label}</span>
    </div>
  );
}
