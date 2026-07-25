import { describe, expect, it } from "vitest";

import { mergeJobLifecycleEvents } from "@/lib/chat/jobLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";

describe("jobProgressBubbles", () => {
  it("shows progress then completion without duplicate progress", () => {
    const base: CachedMessage[] = [{ id: "1", role: "user", content: "research" }];
    const events = [
      {
        id: "job-1:job_started",
        job_id: "job-1",
        event_type: "job_started" as const,
        message: "⏳ Job started — Competitors",
        status: "running",
        job_type: "comparison_brief",
        session_id: "default",
        at: 1,
      },
      {
        id: "job-1:job_progress:main",
        job_id: "job-1",
        event_type: "job_progress" as const,
        message: "🧠 Researching competitors — Competitors…",
        status: "running",
        job_type: "comparison_brief",
        session_id: "default",
        at: 2,
      },
      {
        id: "job-1:job_completed",
        job_id: "job-1",
        event_type: "job_completed" as const,
        message: "✅ Job completed — Competitors",
        status: "completed",
        job_type: "comparison_brief",
        session_id: "default",
        at: 3,
      },
    ];
    const merged = mergeJobLifecycleEvents(base, events, new Set());
    expect(merged.messages).toHaveLength(4);
    const second = mergeJobLifecycleEvents(merged.messages, events, merged.seen);
    expect(second.messages).toHaveLength(4);
  });
});
