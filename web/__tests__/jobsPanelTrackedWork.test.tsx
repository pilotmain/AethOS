import { describe, expect, it } from "vitest";

import { normalizeJobsGrouped } from "@/lib/missionControl/trackedJobs";
import { mcFailureAffectsChat } from "@/lib/missionControl/panelError";

describe("jobsPanelTrackedWork", () => {
  it("separates queued and completed jobs", () => {
    const grouped = normalizeJobsGrouped({
      queued: [
        {
          id: "job-a",
          title: "Queued task",
          job_type: "manual_note",
          status: "queued",
        },
      ],
      running: [],
      completed: [
        {
          id: "job-b",
          title: "Done task",
          job_type: "checklist_generation",
          status: "completed",
          result: "- [ ] item",
        },
      ],
      failed: [],
      cancelled: [],
    });
    expect(grouped.queued).toHaveLength(1);
    expect(grouped.completed).toHaveLength(1);
  });

  it("jobs panel failure does not affect chat", () => {
    expect(mcFailureAffectsChat("Jobs request failed: 500")).toBe(false);
  });
});
