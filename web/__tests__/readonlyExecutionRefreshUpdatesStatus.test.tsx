import { describe, expect, it } from "vitest";

import { emptyJobsGrouped, hasActiveTrackedJobs } from "@/lib/missionControl/trackedJobs";

describe("readonlyExecutionRefreshUpdatesStatus", () => {
  it("detects active jobs that need polling refresh", () => {
    const grouped = emptyJobsGrouped();
    grouped.running = [
      {
        id: "job-ex",
        job_type: "readonly_execution_vercel",
        status: "running",
        title: "Read-only execution",
      } as never,
    ];
    expect(hasActiveTrackedJobs(grouped)).toBe(true);
  });

  it("returns false when no queued or running jobs", () => {
    expect(hasActiveTrackedJobs(emptyJobsGrouped())).toBe(false);
  });
});
