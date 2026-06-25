/**
 * Next.js instrumentation hook — initialises Sentry on the server and edge runtimes.
 * Called once per worker startup; no-ops gracefully when DSN is not set.
 * https://nextjs.org/docs/app/api-reference/file-conventions/instrumentation
 */

import * as Sentry from "@sentry/nextjs";

export async function register() {
  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
  if (!dsn) return;

  if (process.env.NEXT_RUNTIME === "nodejs") {
    Sentry.init({
      dsn,
      environment: process.env.NODE_ENV,
      tracesSampleRate: 0.1,
      // Do not capture PII from server-side request headers
      sendDefaultPii: false,
    });
  }

  if (process.env.NEXT_RUNTIME === "edge") {
    Sentry.init({
      dsn,
      environment: process.env.NODE_ENV,
      tracesSampleRate: 0.1,
    });
  }
}

// Capture server component / route handler errors automatically (Next.js 15+)
export const onRequestError = Sentry.captureRequestError;
