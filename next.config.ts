import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  output: "standalone",
  outputFileTracingRoot: path.join(process.cwd()),
  images: { remotePatterns: [{ protocol: "https", hostname: "images.unsplash.com" }] },
  async headers() {
    return [{
      source: "/:path*",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        // Defense-in-depth: the production nginx config (deploy/nginx) already sends this at the edge, but
        // this covers any deployment path that reaches the Next.js server directly.
        { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" }
        // Content-Security-Policy is intentionally NOT set here - it needs a fresh nonce per request, which
        // static next.config.ts headers can't generate. See middleware.ts.
      ]
    }];
  }
};

export default nextConfig;
