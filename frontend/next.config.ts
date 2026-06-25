import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  async rewrites() {
    const isProd = process.env.NODE_ENV === 'production';
    const defaultBackendUrl = isProd ? "https://voicecare-backend.onrender.com" : "http://localhost:8000";
    const backendUrl = (process.env.BACKEND_URL || defaultBackendUrl).replace(/\/$/, "");
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default withSentryConfig(nextConfig, {
  // Sentry build-time options
  // Source map upload is skipped unless SENTRY_AUTH_TOKEN + SENTRY_ORG + SENTRY_PROJECT are set in CI.
  silent: !process.env.CI,
  telemetry: false,
  sourcemaps: {
    disable: !process.env.SENTRY_AUTH_TOKEN,
  },
  // Turbopack-compatible tree-shaking options (replaces deprecated disableLogger)
  webpack: {
    treeshake: {
      removeDebugLogging: true,
    },
  },
});
