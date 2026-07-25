import { describe, expect, it } from "vitest";

import { jobControlHint, normalizeJobsGrouped } from "@/lib/missionControl/trackedJobs";

describe("jobsPanelCancelQueuedJob", () => {
  it("queued job shows Queued hint", () => {
    expect(jobControlHint("queued")).toBe("Queued");
  });

  it("only queued jobs appear in queued group for cancel UI", () => {
    const grouped = normalizeJobsGrouped({
      queued: [
        {
          id: "job-q",
          title: "Cancel me",
          job_type: "manual_note",
          status: "queued",
        },
      ],
      running: [],
      completed: [
        {
          id: "job-c",
          title: "Done",
          job_type: "manual_note",
          status: "completed",
        },
      ],
      failed: [],
      cancelled: [],
    });
    expect(grouped.queued).toHaveLength(1);
    expect(grouped.completed).toHaveLength(1);
    expect(grouped.queued[0]?.status).toBe("queued");
  });

  it("completed job has no queued status", () => {
    expect(jobControlHint("completed")).toBe("Completed");
  });
});
