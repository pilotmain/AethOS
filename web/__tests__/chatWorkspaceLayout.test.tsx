import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import {
  CHAT_ASSISTANT_MESSAGE_MAX,
  CHAT_USER_MESSAGE_MAX,
  CHAT_WORKSPACE_MAX_WIDTH,
  isOperationalMessage,
  isSidebarToggleShortcut,
  isWideArtifactContent,
  operationalEventTone,
} from "@/lib/chat/layout";

const key = (over: Partial<KeyboardEvent>): KeyboardEvent =>
  ({ key: "b", ctrlKey: false, metaKey: false, altKey: false, shiftKey: false, ...over }) as KeyboardEvent;

describe("isSidebarToggleShortcut", () => {
  it("matches Ctrl+B and ⌘B", () => {
    expect(isSidebarToggleShortcut(key({ ctrlKey: true }))).toBe(true);
    expect(isSidebarToggleShortcut(key({ metaKey: true }))).toBe(true);
    expect(isSidebarToggleShortcut(key({ ctrlKey: true, key: "B" }))).toBe(true);
  });

  it("ignores plain 'b' so typing in the composer is never hijacked", () => {
    expect(isSidebarToggleShortcut(key({}))).toBe(false);
  });

  it("ignores other keys and modifier combos", () => {
    expect(isSidebarToggleShortcut(key({ ctrlKey: true, key: "a" }))).toBe(false);
    expect(isSidebarToggleShortcut(key({ ctrlKey: true, shiftKey: true }))).toBe(false);
    expect(isSidebarToggleShortcut(key({ ctrlKey: true, altKey: true }))).toBe(false);
  });
});

describe("ChatShell sidebar toggle wiring", () => {
  const src = readFileSync(join(__dirname, "../components/ChatShell.tsx"), "utf8");

  it("uses the shared shortcut matcher and toggles the collapse state", () => {
    expect(src).toContain("isSidebarToggleShortcut");
    expect(src).toContain("setSidebarCollapsed");
    expect(src).toContain("collapsed={sidebarCollapsed}");
  });

  it("renders a click affordance to restore an accidentally-collapsed sidebar", () => {
    // When collapsed, a visible 'Show sidebar' button must let the user click back —
    // not rely on knowing the keyboard shortcut.
    expect(src).toMatch(/sidebarCollapsed && \(/);
    expect(src).toContain('aria-label="Show sidebar"');
    expect(src).toContain("setSidebarCollapsed(false)");
  });

  it("has no second inline Ctrl/Cmd+B handler fighting the collapse state", () => {
    // The old mobile-only handler matched the 'b' key inline and cancelled out the
    // desktop collapse. The 'b' match now lives ONLY in isSidebarToggleShortcut.
    expect(src).not.toMatch(/===\s*"b"/);
    // The 'm' (switch-model) handler is still inline and must stay.
    expect(src).toMatch(/===\s*"m"/);
  });
});

describe("chatWorkspaceLayout", () => {
  it("uses wide workspace max width instead of narrow 720px column", () => {
    expect(CHAT_WORKSPACE_MAX_WIDTH).toBeGreaterThanOrEqual(1400);
    expect(CHAT_USER_MESSAGE_MAX).toBe(700);
    expect(CHAT_ASSISTANT_MESSAGE_MAX).toBe(1100);
  });

  it("detects operational lifecycle messages", () => {
    expect(isOperationalMessage({ role: "system", id: "jevt-1" })).toBe(true);
    expect(isOperationalMessage({ role: "assistant", id: "m-1" })).toBe(false);
  });

  it("detects wide artifact assistant content", () => {
    const preflight = "# Mutation preflight (governed execution)\n\n**Provider:** railway";
    expect(isWideArtifactContent(preflight)).toBe(true);
    expect(isWideArtifactContent("Short answer.")).toBe(false);
  });

  it("maps lifecycle event tones", () => {
    expect(operationalEventTone("job_completed")).toBe("success");
    expect(operationalEventTone("job_failed")).toBe("error");
    expect(operationalEventTone("job_started")).toBe("progress");
  });
});
