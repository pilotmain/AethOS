import { describe, expect, it } from "vitest";

import { partitionCompletedJobs } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("operationPreflightGrouping", () => {
  it("separates operation preflights from tracked work", () => {
    const jobs: TrackedJobRecord[] = [
      {
        id: "job-pf",
        title: "Preflight",
        job_type: "vercel_redeploy_preflight",
        status: "completed",
      },
      {
        id: "job-inv",
        title: "Inventory",
        job_type: "vercel_projects_inventory",
        status: "completed",
      },
    ];
    const { operationPreflights, trackedWork } = partitionCompletedJobs(jobs);
    expect(operationPreflights).toHaveLength(1);
    expect(trackedWork).toHaveLength(1);
  });
});
