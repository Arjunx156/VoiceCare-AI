/**
 * Sentry browser-side initialisation.
 * This file is injected by withSentryConfig (next.config.ts) before any app code.
 * Runs only in the browser; set NEXT_PUBLIC_SENTRY_DSN to enable.
 */

import * as Sentry from "@sentry/nextjs";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV,
    tracesSampleRate: 0.1,          // 10 % of browser navigations traced
    replaysSessionSampleRate: 0.05, // 5 % of sessions recorded
    replaysOnErrorSampleRate: 1.0,  // always record session on error
    integrations: [
      Sentry.replayIntegration({
        maskAllText: true,   // mask PII in recordings
        blockAllMedia: true,
      }),
    ],
    // Send only unhandled errors — filter out noise like network timeouts
    ignoreErrors: [
      "ResizeObserver loop limit exceeded",
      "Non-Error promise rejection captured",
    ],
  });
}
