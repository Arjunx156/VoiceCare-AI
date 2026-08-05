import type { ReactNode } from "react";

import { priorityMeta, sentimentMeta, statusMeta, type BadgeMeta } from "@/lib/theme";

type BadgeProps = {
  meta: BadgeMeta;
  children: ReactNode;
  /** Show the colored dot so meaning never rests on tint alone. */
  withDot?: boolean;
};

/**
 * A classification the pipeline assigned — priority, status, sentiment. Set in
 * the mono register and cut square rather than pill-shaped, so it reads as a
 * data tag rather than a marketing chip.
 */
export function Badge({ meta, children, withDot = true }: BadgeProps) {
  return (
    <span
      className="mono"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        fontSize: 10,
        fontWeight: 500,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        padding: "3px 7px",
        borderRadius: 4,
        whiteSpace: "nowrap",
        background: meta.bg,
        color: meta.fg,
      }}
    >
      {withDot && (
        <span
          aria-hidden="true"
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: meta.fg,
            flexShrink: 0,
          }}
        />
      )}
      {children}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: string | null | undefined }) {
  if (!priority) return null;
  return <Badge meta={priorityMeta(priority)}>{priority}</Badge>;
}

export function StatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return null;
  return <Badge meta={statusMeta(status)}>{status}</Badge>;
}

export function SentimentBadge({ sentiment }: { sentiment: string | null | undefined }) {
  if (!sentiment) return null;
  return <Badge meta={sentimentMeta(sentiment)}>{sentiment}</Badge>;
}
