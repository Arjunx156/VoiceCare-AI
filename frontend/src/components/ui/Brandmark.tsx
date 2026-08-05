import { clsx } from "clsx";

type Props = {
  /** Renders the wordmark as an h1. Use on pages where it is the page title. */
  as?: "span" | "h1";
  /** Animate the meter. Only pass this while the pipeline is actually live. */
  isLive?: boolean;
  className?: string;
};

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI";

/**
 * The lockup: a four-bar meter glyph plus the wordmark, with the last word of
 * the product name carrying the accent colour.
 *
 * One component rather than three copies, because the previous version had the
 * sidebar, the login card and the voice header each hand-rolling the same
 * markup - which is how they drift apart. See the BRANDMARK note in globals.css
 * for why this shape replaced the squircle-and-mic.
 */
export function Brandmark({ as = "span", isLive = false, className }: Props) {
  const words = APP_NAME.trim().split(/\s+/);
  const lead = words.slice(0, -1).join(" ");
  const tail = words.length > 1 ? words[words.length - 1] : null;
  const Word = as;

  return (
    <span className={clsx("brand-lockup", className)} style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span className={clsx("brandmark", isLive && "live")} aria-hidden="true">
        <span /><span /><span /><span />
      </span>
      <Word className="wordmark">
        {lead}
        {tail && <span className="wordmark-accent">{lead ? " " : ""}{tail}</span>}
      </Word>
    </span>
  );
}
