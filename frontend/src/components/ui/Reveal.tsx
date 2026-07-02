"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { EASE_OUT_EXPO } from "@/lib/motion";

type Props = {
  children: ReactNode;
  /** Stagger delay in seconds. */
  delay?: number;
  /** Travel distance in px (y). */
  y?: number;
  /** Render as a different element via motion (default div). */
  className?: string;
  style?: React.CSSProperties;
};

/**
 * Scroll-reveal wrapper: fades + lifts content the first time it enters the
 * viewport. Under `prefers-reduced-motion` it renders immediately with no
 * transform (Framer animations are JS-driven and ignore the CSS override).
 */
export function Reveal({ children, delay = 0, y = 18, className, style }: Props) {
  const reduced = useReducedMotion();

  if (reduced) {
    return (
      <div className={className} style={style}>
        {children}
      </div>
    );
  }

  return (
    <motion.div
      className={className}
      style={style}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "0px 0px -80px 0px" }}
      transition={{ duration: 0.6, ease: EASE_OUT_EXPO, delay }}
    >
      {children}
    </motion.div>
  );
}
