import type { CSSProperties } from "react";

type Props = {
  /** Diameter of the glow in px (defaults to a large hero glow). */
  size?: number;
  /** Slow ambient drift (disabled automatically under reduced motion via CSS). */
  animate?: boolean;
  /** Extra positioning — e.g. top/left/right/bottom, transform. */
  style?: CSSProperties;
  className?: string;
};

/**
 * Radial coral glow that sits behind hero content for atmosphere/depth.
 * Purely decorative (aria-hidden), GPU-friendly (filter/transform only),
 * and never intercepts pointer events. See `.glow-backdrop` in globals.css.
 */
export function GlowBackdrop({ size = 520, animate = true, style, className }: Props) {
  return (
    <div
      aria-hidden="true"
      className={`glow-backdrop${animate ? " glow-animate" : ""}${className ? ` ${className}` : ""}`}
      style={{ width: size, height: size, ...style }}
    />
  );
}
