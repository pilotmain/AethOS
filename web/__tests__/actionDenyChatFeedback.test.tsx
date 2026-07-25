import { describe, expect, it } from "vitest";

import { mergeLifecycleEvents } from "@/lib/chat/actionLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";

describe("actionDenyChatFeedback", () => {
  it("renders action_denied bubble once", () => {
    const base: CachedMessage[] = [{ id: "1", role: "user", content: "check vercel" }];
    const events = [
      {
        id: "act-1:action_denied",
        action_id: "act-1",
        event_type: "action_denied" as const,
        message: "🚫 Action denied — Vercel CLI probe was not run.",
        status: "denied",
        action_type: "vercel_cli_probe",
        session_id: "default",
        at: 1,
      },
    ];
    const first = mergeLifecycleEvents(base, events, new Set());
    expect(first.messages[1]?.content).toMatch(/🚫 Action denied/);
    const second = mergeLifecycleEvents(first.messages, events, first.seen);
    expect(second.messages).toHaveLength(2);
  });
});
