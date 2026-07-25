/** Chat workspace layout tokens — mirrors Mission Control wide console. */

import type { CSSProperties } from "react";

import { mcColors } from "@/lib/missionControl/layout";

export const CHAT_SIDEBAR_WIDTH = 240;
export const CHAT_CONTEXT_PANEL_WIDTH = 340;
export const CHAT_WORKSPACE_MAX_WIDTH = 1600;
export const CHAT_USER_MESSAGE_MAX = 700;
export const CHAT_ASSISTANT_MESSAGE_MAX = 1100;

export const chatAppShellStyle: CSSProperties = {
  display: "flex",
  minHeight: "100vh",
  height: "100vh",
  width: "100%",
  background: `linear-gradient(135deg, ${mcColors.bg} 0%, ${mcColors.navy} 48%, ${mcColors.bg} 100%)`,
  color: mcColors.text,
};

export const chatMainColumnStyle: CSSProperties = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  minWidth: 0,
  minHeight: 0,
};

export const chatWorkspaceGridStyle: CSSProperties = {
  flex: 1,
  display: "flex",
  minHeight: 0,
  minWidth: 0,
  width: "100%",
  // Fill the available width (no centered max-width gutters on wide screens). Message
  // bubbles keep their own readable max-width; the context panel sits flush right.
  maxWidth: "100%",
  margin: 0,
};

export const chatConversationColumnStyle: CSSProperties = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  minWidth: 0,
  minHeight: 0,
};

export const chatScrollAreaStyle: CSSProperties = {
  flex: 1,
  overflowY: "auto",
  minHeight: 0,
  padding: "0 28px 20px",
};

export const chatComposerDockStyle: CSSProperties = {
  flexShrink: 0,
  padding: "16px 28px 24px",
  borderTop: `1px solid ${mcColors.borderSubtle}`,
  background: "linear-gradient(180deg, transparent 0%, rgba(5,5,8,0.92) 24%)",
};

export const chatHeaderStyle: CSSProperties = {
  flexShrink: 0,
  padding: "20px 28px 14px",
  borderBottom: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
};

/** True for the sidebar-toggle shortcut: Ctrl+B (Windows/Linux) or ⌘B (macOS).
 * Ignores plain "b" so typing in the composer is never hijacked. */
export function isSidebarToggleShortcut(e: {
  key: string;
  ctrlKey: boolean;
  metaKey: boolean;
  altKey: boolean;
  shiftKey: boolean;
}): boolean {
  if (e.altKey || e.shiftKey) return false;
  if (!(e.ctrlKey || e.metaKey)) return false;
  return e.key.toLowerCase() === "b";
}

export function isOperationalMessage(message: { role: string; id: string; event_type?: string }): boolean {
  if (message.role === "system") return true;
  if (message.id.startsWith("jevt-") || message.id.startsWith("evt-") || message.id.startsWith("bsess-evt-")) {
    return true;
  }
  return Boolean(message.event_type);
}

export function isWideArtifactContent(content: string): boolean {
  const text = (content || "").trim();
  if (!text) return false;
  if (/^#\s/m.test(text)) return true;
  if (/\*\*Provider:\*\*/i.test(text) || /\*\*Operation:\*\*/i.test(text)) return true;
  if (/Mutation preflight/i.test(text) || /Browser evidence/i.test(text)) return true;
  if (/Open Mission Control/i.test(text) && text.length > 200) return true;
  if (text.length > 900) return true;
  return false;
}

export function operationalEventTone(eventType?: string): "neutral" | "progress" | "success" | "warning" | "error" {
  const t = (eventType || "").toLowerCase();
  if (t.includes("failed") || t.includes("denied") || t.includes("cancelled")) return "error";
  if (t.includes("completed") || t.includes("approved")) return "success";
  if (t.includes("started") || t.includes("progress") || t.includes("waiting")) return "progress";
  if (t.includes("verification") || t.includes("pending")) return "warning";
  return "neutral";
}
