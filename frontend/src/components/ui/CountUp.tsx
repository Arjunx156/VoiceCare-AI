"use client";

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";

/** Ease-out cubic — fast start, gentle settle. Pure, exported for tests. */
export function easeOutCubic(t: number): number {
  const clamped = t < 0 ? 0 : t > 1 ? 1 : t;
  return 1 - Math.pow(1 - clamped, 3);
}

/** Interpolate `to` from 0 at eased progress, rounded to `decimals`. Pure. */
export function countAt(to: number, progress: number, decimals: number): number {
  const raw = to * easeOutCubic(progress);
  const factor = Math.pow(10, decimals);
  return Math.round(raw * factor) / factor;
}

type Props = {
  value: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  durationMs?: number;
  style?: React.CSSProperties;
  className?: string;
};

/**
 * Animated number that counts from 0 → `value` on mount. Renders the final
 * value instantly under `prefers-reduced-motion`. Uses requestAnimationFrame
 * (setState only inside the async frame callback, never synchronously in the
 * effect body).
 */
export function CountUp({
  value,
  decimals = 0,
  prefix = "",
  suffix = "",
  durationMs = 900,
  style,
  className,
}: Props) {
  const reduced = useReducedMotion();
  const [animated, setAnimated] = useState<number>(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    // Under reduced motion the value is derived during render — no animation,
    // no setState here (keeps effects free of synchronous state updates).
    if (reduced) return;
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / durationMs, 1);
      setAnimated(countAt(value, progress, decimals));
      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [value, decimals, durationMs, reduced]);

  const shown = reduced ? value : animated;

  return (
    <span className={className} style={{ fontVariantNumeric: "tabular-nums", ...style }}>
      {prefix}
      {shown.toFixed(decimals)}
      {suffix}
    </span>
  );
}
