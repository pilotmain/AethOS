import { describe, expect, it } from "vitest";

import { isReadonlyExecutionTimedOut } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("readonlyExecutionRunningTimeout", () => {
  it("detects timed out execution jobs", () => {
    const job = {
      id: "job-ex",
      job_type: "readonly_execution_vercel",
      status: "failed",
      params: { status_reason: "execution_timed_out" },
    } as unknown as TrackedJobRecord;
    expect(isReadonlyExecutionTimedOut(job)).toBe(true);
  });
});
