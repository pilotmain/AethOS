"use client";

import { withBasePath } from "@/lib/pwa/basePath";

/** Branded gate loading — logo + spinner instead of a blank screen. */

export function AethosLoadingScreen() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        background: "linear-gradient(180deg, #141d31 0%, #0a0c10 100%)",
        color: "var(--aethos-text-muted)",
      }}
    >
      <div style={{ textAlign: "center", maxWidth: 320 }}>
        <img
          src={withBasePath("/icons/icon-192.png")}
          alt="AethOS"
          width={88}
          height={88}
          style={{ borderRadius: 22, marginBottom: 20 }}
        />
        <div
          style={{
            fontSize: 11,
            letterSpacing: "0.18em",
            fontWeight: 700,
            color: "var(--aethos-text-dim)",
            marginBottom: 8,
          }}
        >
          AETHOS
        </div>
        <p style={{ fontSize: 14, margin: "0 0 16px" }}>Loading…</p>
        <div
          style={{
            width: 28,
            height: 28,
            margin: "0 auto",
            border: "2px solid rgba(34, 211, 238, 0.25)",
            borderTopColor: "#22d3ee",
            borderRadius: "50%",
            animation: "aethos-spin 0.8s linear infinite",
          }}
        />
        <style>{`@keyframes aethos-spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    </div>
  );
}
