"use client";

import { useEffect } from "react";

/**
 * Fire-and-forget warm-up ping so a sleeping free-tier backend (Render spins
 * down after idle) starts waking the moment the page loads — not when the
 * user first records a query or submits the login form. Renders nothing.
 */
export default function BackendWarmup() {
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_BACKEND_URL || "";
    // Same-origin path is proxied by Next rewrites in local dev.
    fetch(`${base}/health`, { cache: "no-store" }).catch(() => {
      /* purely opportunistic — never surface errors */
    });
  }, []);

  return null;
}
