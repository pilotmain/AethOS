import { describe, expect, it } from "vitest";

import { executionJobIdFromPreflight, mcJobAnchorId } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("preflightExecutionLink", () => {
  it("exposes execution job anchor for preflight cards", () => {
    const job = {
      id: "job-pf1",
      title: "Preflight",
      job_type: "vercel_domains_preflight",
      status: "completed",
      params: {
        execution_approved: true,
        execution_job_id: "job-exec99",
      },
    } as TrackedJobRecord;
    expect(executionJobIdFromPreflight(job)).toBe("job-exec99");
    expect(mcJobAnchorId("job-exec99")).toBe("mc-job-job-exec99");
  });
});
