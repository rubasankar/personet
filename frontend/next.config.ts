import type { NextConfig } from "next";

// In production set NEXT_PUBLIC_API_URL to your deployed backend URL,
// e.g. https://pernet-api.onrender.com
// Locally this falls back to localhost:8000 via the rewrite below.
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
