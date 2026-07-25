import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  mergeJobLifecycleEvents,
  type JobLifecycleEvent,
} from "@/lib/chat/jobLifecycleBridge";
import { fetchJobEvents } from "@/lib/chat/jobLifecycleBridge";

describe("jobEventPollingNoChatBubbleOnTransientDrop", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("does not append chat bubble when poll fails transiently", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    const poll = await fetchJobEvents(["job-abc"]);
    const merged = mergeJobLifecycleEvents([], poll.events, new Set());
    expect(merged.added).toBe(0);
    expect(merged.messages).toHaveLength(0);
  });

  it("still appends real job failure events from backend", () => {
    const events: JobLifecycleEvent[] = [
      {
        id: "job-1:job_failed",
        job_id: "job-1",
        event_type: "job_failed",
        message: "⚠️ Job failed — Inventory: browser runtime unavailable",
        status: "failed",
        job_type: "vercel_projects_inventory",
        session_id: "default",
        at: 1,
      },
    ];
    const merged = mergeJobLifecycleEvents([], events, new Set());
    expect(merged.added).toBe(1);
    expect(merged.messages[0]?.content).toMatch(/Job failed/i);
  });
});
