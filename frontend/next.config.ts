import type { NextConfig } from "next";

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

export default nextConfig;
