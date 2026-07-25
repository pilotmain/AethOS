"use client";

import { useEffect, useState } from "react";

import { useAuthScope } from "@/lib/auth/AuthScopeContext";
import { mcAlpha, mcColors } from "@/lib/missionControl/layout";
import { usePwaInstall } from "@/lib/pwa/usePwaInstall";
import { useWebPush } from "@/lib/pwa/useWebPush";

const DISMISS_KEY = "aethos-pwa-install-dismissed";
const INSTALLED_KEY = "aethos-pwa-installed";

export function PwaInstallBanner() {
  const { authenticated, authEnabled } = useAuthScope();
  const { canInstall, installed, install } = usePwaInstall();
  const push = useWebPush();
  const [dismissed, setDismissed] = useState(true);
  const [storedInstalled, setStoredInstalled] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setDismissed(window.localStorage.getItem(DISMISS_KEY) === "1");
    setStoredInstalled(window.localStorage.getItem(INSTALLED_KEY) === "1");
  }, []);

  useEffect(() => {
    if (!installed) return;
    window.localStorage.setItem(INSTALLED_KEY, "1");
    setStoredInstalled(true);
  }, [installed]);

  const inAuthenticatedApp = !authEnabled || authenticated;
  if (!inAuthenticatedApp || dismissed || installed || storedInstalled) return null;
  if (!canInstall && !push.enabled) return null;

  return (
    <div
      role="region"
      aria-label="Install AethOS"
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: 8,
        alignItems: "center",
        justifyContent: "space-between",
        margin: "0 auto 8px",
        maxWidth: 1100,
        width: "100%",
        padding: "10px 12px",
        borderRadius: 10,
        border: `1px solid ${mcColors.borderSubtle}`,
        background: mcAlpha(mcColors.cyan, 8),
        fontSize: 12,
      }}
    >
      <span style={{ color: mcColors.textMuted }}>
        Install AethOS for a full-screen app experience
        {push.enabled ? " and enable push for proactive automations." : "."}
      </span>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {canInstall ? (
          <button
            type="button"
            onClick={() => void install()}
            style={{
              padding: "6px 12px",
              borderRadius: 8,
              border: `1px solid ${mcColors.cyan}`,
              background: mcAlpha(mcColors.cyan, 16),
              color: mcColors.cyan,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Install app
          </button>
        ) : null}
        {push.enabled && push.supported && !push.subscribed ? (
          <button
            type="button"
            onClick={() => void push.subscribe()}
            style={{
              padding: "6px 12px",
              borderRadius: 8,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "transparent",
              color: mcColors.text,
              cursor: "pointer",
            }}
          >
            Enable push
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => {
            window.localStorage.setItem(DISMISS_KEY, "1");
            setDismissed(true);
          }}
          style={{
            padding: "6px 10px",
            border: "none",
            background: "transparent",
            color: mcColors.textDim,
            cursor: "pointer",
          }}
        >
          Dismiss
        </button>
      </div>
      {push.error ? <span style={{ width: "100%", color: mcColors.amber }}>{push.error}</span> : null}
    </div>
  );
}
