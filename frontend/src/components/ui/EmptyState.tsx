import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  icon: LucideIcon;
  title: string;
  hint?: ReactNode;
  action?: ReactNode;
};

/** Empty/zero states — lucide icon instead of emoji, consistent spacing. */
export function EmptyState({ icon: Icon, title, hint, action }: Props) {
  return (
    <div style={{ textAlign: "center", padding: "64px 24px" }}>
      <Icon
        size={28}
        strokeWidth={1.5}
        aria-hidden="true"
        style={{ color: "var(--text-faint)", marginBottom: 12 }}
      />
      <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-secondary)" }}>{title}</p>
      {hint && (
        <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{hint}</p>
      )}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}
