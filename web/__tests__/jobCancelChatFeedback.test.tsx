import { describe, expect, it } from "vitest";

import { mergeJobLifecycleEvents } from "@/lib/chat/jobLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";

describe("jobCancelChatFeedback", () => {
  it("renders job_cancelled bubble once", () => {
    const base: CachedMessage[] = [{ id: "1", role: "user", content: "queued task" }];
    const events = [
      {
        id: "job-1:job_cancelled",
        job_id: "job-1",
        event_type: "job_cancelled" as const,
        message: "🚫 Job cancelled — test cancel",
        status: "cancelled",
        job_type: "manual_note",
        session_id: "default",
        at: 1,
      },
    ];
    const first = mergeJobLifecycleEvents(base, events, new Set());
    expect(first.messages[1]?.content).toMatch(/🚫 Job cancelled/);
    const second = mergeJobLifecycleEvents(first.messages, events, first.seen);
    expect(second.messages).toHaveLength(2);
  });
});
