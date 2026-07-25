import { describe, expect, it } from "vitest";

import { mergeLifecycleEvents } from "@/lib/chat/actionLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";

describe("browserLoginSafetyCopy", () => {
  it("shows browser denied feedback without secret prompts", () => {
    const base: CachedMessage[] = [
      { id: "1", role: "user", content: "login to vercel.com and check my dashboard" },
    ];
    const events = [
      {
        id: "act-br:action_denied",
        action_id: "act-br",
        event_type: "action_denied" as const,
        message: "🚫 Browser job denied — no browser session opened for vercel.com.",
        status: "denied",
        action_type: "browser_login_required_notice",
        session_id: "default",
        at: 1,
      },
    ];
    const merged = mergeLifecycleEvents(base, events, new Set());
    const bubble = merged.messages[1]?.content ?? "";
    expect(bubble).toMatch(/Browser job denied/);
    expect(bubble).not.toMatch(/password/i);
    expect(bubble).not.toMatch(/enter your credentials/i);
  });

  it("browser completion warns execution not implemented", () => {
    const base: CachedMessage[] = [{ id: "1", role: "user", content: "open vercel.com" }];
    const events = [
      {
        id: "act-br:action_completed",
        action_id: "act-br",
        event_type: "action_completed" as const,
        message:
          "⚠️ Browser execution is not implemented in this build. No browser session was opened.",
        status: "completed",
        action_type: "browser_navigation_plan",
        session_id: "default",
        at: 2,
      },
    ];
    const merged = mergeLifecycleEvents(base, events, new Set());
    expect(merged.messages[1]?.content).toMatch(/not implemented/i);
    expect(merged.messages[1]?.content).not.toMatch(/logged in/i);
  });
});
