/** @type {import('next').NextConfig} */

import { fileURLToPath } from "node:url";

// The UI is served behind `pilotmain.com/aethos` on Railway, so production builds
// mount under the `/aethos` base path. Local `next dev` stays at `/` so the app
// loads at http://localhost:3000 without a 404. Override with NEXT_PUBLIC_BASE_PATH
// (set it to "" to force root, or to another prefix) when needed.
const isProd = process.env.NODE_ENV === "production";
const basePath =
  process.env.NEXT_PUBLIC_BASE_PATH ?? (isProd ? "/aethos" : "");

const appVersion =
  process.env.NEXT_PUBLIC_APP_VERSION?.trim() ||
  process.env.RAILWAY_GIT_COMMIT_SHA?.trim() ||
  process.env.APP_VERSION?.trim() ||
  "dev";

const nextConfig = {
  outputFileTracingRoot: fileURLToPath(new URL(".", import.meta.url)),
  ...(basePath ? { basePath, assetPrefix: basePath } : {}),
  env: {
    NEXT_PUBLIC_APP_VERSION: appVersion,
  },
  output: "standalone",
  reactStrictMode: true,
  productionBrowserSourceMaps: false,
  poweredByHeader: false,
  compress: true,
  async headers() {
    const staticCache = "public, max-age=31536000, immutable";
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Access-Control-Allow-Origin", value: "https://pilotmain.com" },
          { key: "Access-Control-Allow-Credentials", value: "true" },
        ],
      },
      ...(basePath
        ? [
            {
              source: "/_next/static/:path*",
              headers: [{ key: "Cache-Control", value: staticCache }],
            },
          ]
        : []),
    ];
  },
};

export default nextConfig;
