"use client";

import { AccountMenu } from "@/components/auth/AccountMenu";
import { AppNav } from "@/components/AppNav";
import { AethosLogo } from "@/components/branding/AethosLogo";
import { chatHeaderStyle } from "@/lib/chat/layout";
import { mcButtonSecondaryStyle, mcColors } from "@/lib/missionControl/layout";
import type { ChatHealth } from "@/lib/connection/chatHealth";

type Props = {
  health: ChatHealth | null;
  onToggleMobileNav?: () => void;
  onToggleContext?: () => void;
  contextOpen?: boolean;
};

export function ChatHeader({ health, onToggleMobileNav, onToggleContext, contextOpen }: Props) {
  return (
    <header style={chatHeaderStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {onToggleMobileNav ? (
              <button
                type="button"
                className="mc-mobile-nav-toggle chat-mobile-nav-toggle"
                onClick={onToggleMobileNav}
                style={{ ...mcButtonSecondaryStyle, padding: "6px 10px", display: "none" }}
                aria-label="Open navigation"
              >
                ☰
              </button>
            ) : null}
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <AethosLogo size={28} />
                <h1 className="aethos-gradient-text" style={{ margin: 0, fontSize: 24, fontWeight: 700, letterSpacing: "-0.01em", width: "fit-content" }}>
                  AethOS
                </h1>
              </div>
              <p style={{ margin: "6px 0 0", color: mcColors.textMuted, fontSize: 13 }}>
                Calm operational conversation — governed execution, evidence, and lifecycle clarity.
              </p>
            </div>
          </div>
          <AppNav active="chat" />
          {health ? (
            <p style={{ margin: "8px 0 0", fontSize: 12, color: health.chatReady ? mcColors.green : mcColors.red }}>
              {health.connectionLabel}
            </p>
          ) : null}
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "flex-start" }}>
          <AccountMenu />
          {onToggleContext ? (
            <button
              type="button"
              className="chat-context-toggle"
              onClick={onToggleContext}
              style={mcButtonSecondaryStyle}
            >
              {contextOpen ? "Hide context" : "Show context"}
            </button>
          ) : null}
        </div>
      </div>
    </header>
  );
}
