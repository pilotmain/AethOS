import type { MetadataRoute } from "next";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? (process.env.NODE_ENV === "production" ? "/aethos" : "");

/** Installable PWA shell — offline cache, standalone display, push-ready icons. */
export default function manifest(): MetadataRoute.Manifest {
  const icon192 = `${basePath}/icons/icon-192.png`;
  const icon512 = `${basePath}/icons/icon-512.png`;
  const icon512Maskable = `${basePath}/icons/icon-512-maskable.png`;
  const iconSvg = `${basePath}/icons/icon.svg`;
  return {
    name: "AethOS",
    short_name: "AethOS",
    description: "Unified agentic OS — one local-first control plane.",
    start_url: basePath || "/",
    scope: basePath || "/",
    display: "standalone",
    orientation: "portrait-primary",
    background_color: "#0a0c10",
    theme_color: "#0a0c10",
    icons: [
      { src: icon192, sizes: "192x192", type: "image/png", purpose: "any" },
      { src: icon512, sizes: "512x512", type: "image/png", purpose: "any" },
      { src: icon512Maskable, sizes: "512x512", type: "image/png", purpose: "maskable" },
      { src: iconSvg, sizes: "any", type: "image/svg+xml", purpose: "any" },
    ],
  };
}
