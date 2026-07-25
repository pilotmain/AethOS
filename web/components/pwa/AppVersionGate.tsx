"use client";

import { useEffect, useState } from "react";

import {
  CLIENT_APP_VERSION,
  fetchServerVersion,
  isClientBelowMinSupported,
  shouldPromptVersionReload,
} from "@/lib/pwa/appVersion";

type GateState = "ok" | "stale" | "blocked";

/**
 * Checks /api/v1/version on load and periodically — prompts reload or blocks stale clients.
 */
export function AppVersionGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<GateState>("ok");

  useEffect(() => {
    let cancelled = false;

    const check = async () => {
      const info = await fetchServerVersion();
      if (cancelled || !info) return;
      if (isClientBelowMinSupported(CLIENT_APP_VERSION, info.min_supported)) {
        setState("blocked");
        return;
      }
      if (shouldPromptVersionReload(CLIENT_APP_VERSION, info.version)) {
        setState("stale");
      }
    };

    void check();
    const timer = window.setInterval(() => void check(), 5 * 60 * 1000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  if (state === "blocked") {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 24,
          background: "var(--aethos-bg-deep)",
          color: "var(--aethos-text)",
        }}
      >
        <div style={{ maxWidth: 420, textAlign: "center" }}>
          <h1 style={{ fontSize: 20, marginBottom: 12 }}>Update required</h1>
          <p style={{ fontSize: 14, color: "var(--aethos-text-muted)", marginBottom: 20 }}>
            This build is no longer supported. Refresh to load the latest AethOS.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            style={{
              padding: "10px 18px",
              borderRadius: 10,
              border: "none",
              background: "var(--aethos-accent)",
              color: "var(--aethos-bg)",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Refresh now
          </button>
        </div>
      </div>
    );
  }

  if (state === "stale") {
    return (
      <>
        {children}
        <div
          style={{
            position: "fixed",
            bottom: 16,
            left: 16,
            right: 16,
            maxWidth: 480,
            margin: "0 auto",
            padding: "12px 14px",
            borderRadius: 12,
            background: "var(--aethos-surface-strong)",
            border: "1px solid var(--aethos-border)",
            boxShadow: "0 12px 40px rgba(0,0,0,0.35)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            gap: 12,
            fontSize: 13,
          }}
        >
          <span style={{ flex: 1 }}>A new version of AethOS is available.</span>
          <button
            type="button"
            onClick={() => window.location.reload()}
            style={{
              padding: "6px 12px",
              borderRadius: 8,
              border: "none",
              background: "var(--aethos-accent)",
              color: "var(--aethos-bg)",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Reload
          </button>
        </div>
      </>
    );
  }

  return <>{children}</>;
}
