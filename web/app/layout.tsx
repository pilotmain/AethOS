import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AethosGate } from "@/components/auth/AethosGate";
import { CommandPalette } from "@/components/CommandPalette";
import { AppVersionGate } from "@/components/pwa/AppVersionGate";
import { PwaBootstrap } from "@/components/pwa/PwaBootstrap";
import { MissionControlThemeProvider } from "@/lib/missionControl/theme";

export const metadata: Metadata = {
  title: "AethOS",
  description: "Unified agentic OS — one local-first control plane.",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "AethOS",
    statusBarStyle: "black-translucent",
  },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "32x32", type: "image/x-icon" },
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon.svg", type: "image/svg+xml" },
    ],
    apple: "/icons/apple-touch-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0c10",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <PwaBootstrap />
        <a href="#main-content" className="aethos-skip-link">
          Skip to main content
        </a>
        <MissionControlThemeProvider>
          <AppVersionGate>
            <AethosGate>
              <CommandPalette />
              <div id="main-content">{children}</div>
            </AethosGate>
          </AppVersionGate>
        </MissionControlThemeProvider>
      </body>
    </html>
  );
}
