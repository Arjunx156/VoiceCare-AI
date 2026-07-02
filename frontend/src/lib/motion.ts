"use client";

/**
 * Shared Framer Motion variants + a reduced-motion-aware helper.
 * Replaces the fadeUp/transition objects redefined in nearly every page.
 */

import { useReducedMotion } from "framer-motion";
import type { Transition, Variants } from "framer-motion";

/** The house easing curve (matches the CSS fade-up keyframe). */
export const EASE_OUT_EXPO = [0.16, 1, 0.3, 1] as const;

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0 },
};

export const fadeUpTransition = (delay = 0): Transition => ({
  delay,
  duration: 0.5,
  ease: EASE_OUT_EXPO,
});

/**
 * Motion props for the standard page-entry fade. Returns instant (opacity
 * only, zero duration) variants when the user prefers reduced motion —
 * Framer Motion animations are JS-driven and ignore the CSS
 * `prefers-reduced-motion` override in globals.css.
 */
export function useMotionSafe() {
  const reduced = useReducedMotion();

  const entry = (delay = 0) =>
    reduced
      ? { initial: { opacity: 1 }, animate: { opacity: 1 } }
      : {
          initial: { opacity: 0, y: 14 },
          animate: { opacity: 1, y: 0 },
          transition: fadeUpTransition(delay),
        };

  return { reduced, entry };
}
