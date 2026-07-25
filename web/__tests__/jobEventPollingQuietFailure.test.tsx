import { beforeEach, describe, expect, it, vi } from "vitest";

import { fetchJobEvents } from "@/lib/chat/jobLifecycleBridge";

describe("jobEventPollingQuietFailure", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns no events on network failure instead of synthetic job_failed", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    const result = await fetchJobEvents(["job-abc"]);
    expect(result.ok).toBe(false);
    expect(result.events).toEqual([]);
    expect(result.events.some((e) => e.event_type === "job_failed")).toBe(false);
  });
});
