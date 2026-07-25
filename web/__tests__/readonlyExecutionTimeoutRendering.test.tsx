import { describe, expect, it } from "vitest";

import { isReadonlyExecutionTimedOut } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("readonlyExecutionTimeoutRendering", () => {
  it("shows structured timeout reason for failed readonly execution", () => {
    const job = {
      id: "job-ex",
      job_type: "readonly_execution_vercel",
      status: "failed",
      failure_reason: "Read-only execution timed out before completion.",
      params: {
        status_reason: "execution_timed_out",
        timeout_last_progress: "Fetching deployment events",
      },
    } as unknown as TrackedJobRecord;
    expect(isReadonlyExecutionTimedOut(job)).toBe(true);
  });
});
