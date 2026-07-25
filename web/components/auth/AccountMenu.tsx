"use client";

import { useState } from "react";

import { useAuthScope } from "@/lib/auth/AuthScopeContext";
import { mcButtonSecondaryStyle, mcColors } from "@/lib/missionControl/layout";

export function AccountMenu() {
  const { authenticated, authEnabled, email, logout } = useAuthScope();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!authEnabled || !authenticated || !email) return null;

  const initials = email.slice(0, 1).toUpperCase();

  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{
          ...mcButtonSecondaryStyle,
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 10px",
          maxWidth: 240,
        }}
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <span
          style={{
            width: 26,
            height: 26,
            borderRadius: 999,
            background: "rgba(34, 211, 238, 0.15)",
            color: mcColors.cyan,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 12,
            fontWeight: 700,
          }}
        >
          {initials}
        </span>
        <span style={{ fontSize: 12, color: mcColors.textMuted, overflow: "hidden", textOverflow: "ellipsis" }}>
          {email}
        </span>
      </button>
      {open ? (
        <div
          role="menu"
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 6px)",
            minWidth: 180,
            background: "var(--aethos-surface-strong)",
            border: `1px solid ${mcColors.borderSubtle}`,
            borderRadius: 10,
            padding: 6,
            zIndex: 40,
            boxShadow: "0 12px 40px rgba(0,0,0,0.35)",
          }}
        >
          <button
            type="button"
            role="menuitem"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void logout();
            }}
            style={{
              width: "100%",
              textAlign: "left",
              border: "none",
              background: "transparent",
              color: mcColors.text,
              padding: "8px 10px",
              borderRadius: 8,
              fontSize: 13,
              cursor: busy ? "default" : "pointer",
            }}
          >
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}
