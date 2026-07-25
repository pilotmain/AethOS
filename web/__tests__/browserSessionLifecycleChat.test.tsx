import { describe, expect, it } from "vitest";

import { mergeLifecycleEvents } from "@/lib/chat/actionLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";

describe("browserSessionLifecycleChat", () => {
  it("shows browser opened feedback on approve", () => {
    const base: CachedMessage[] = [
      { id: "1", role: "user", content: "open vercel.com in browser automation" },
    ];
    const events = [
      {
        id: "act-1:action_approved",
        action_id: "act-1",
        event_type: "action_approved" as const,
        message: "⏳ Browser session launching — vercel.com…",
        status: "approved",
        action_type: "browser_navigation_plan",
        session_id: "default",
        at: 1,
      },
      {
        id: "act-1:action_completed",
        action_id: "act-1",
        event_type: "action_completed" as const,
        message: "🌐 Browser session opened — vercel.com",
        status: "completed",
        action_type: "browser_navigation_plan",
        session_id: "default",
        at: 2,
      },
    ];
    const merged = mergeLifecycleEvents(base, events, new Set());
    expect(merged.messages[1]?.content).toMatch(/Browser session launching/i);
    expect(merged.messages[2]?.content).toMatch(/Browser session opened/i);
    expect(merged.messages[2]?.content).not.toMatch(/logged in/i);
  });

  it("shows playwright missing failure message", () => {
    const base: CachedMessage[] = [{ id: "1", role: "user", content: "open site" }];
    const events = [
      {
        id: "act-1:action_failed",
        action_id: "act-1",
        event_type: "action_failed" as const,
        message:
          "⚠️ Browser session could not start — Playwright package is missing in the AethOS runtime environment.",
        status: "failed",
        action_type: "browser_navigation_plan",
        session_id: "default",
        at: 1,
      },
    ];
    const merged = mergeLifecycleEvents(base, events, new Set());
    expect(merged.messages[1]?.content).toMatch(/runtime environment/i);
  });
});
