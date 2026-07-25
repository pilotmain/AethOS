import { describe, expect, it } from "vitest";

import { mergeJobLifecycleEvents } from "@/lib/chat/jobLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";

describe("jobFailureBubble", () => {
  it("renders provider timeout failure once", () => {
    const { messages } = mergeJobLifecycleEvents(
      [],
      [
        {
          id: "job-9:job_failed",
          job_id: "job-9",
          event_type: "job_failed",
          message: "⚠️ Job failed — Timeout test: Provider request timed out.",
          status: "failed",
          job_type: "research_plan",
          session_id: "default",
          at: 1,
        },
      ],
      new Set(),
    );
    expect(messages[0]?.content).toMatch(/timed out/i);
  });
});
