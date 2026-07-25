import { describe, expect, it } from "vitest";

import { canApproveReadonlyExecution } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("readonlyExecutionApproval", () => {
  it("allows approval for ready completed preflight", () => {
    const job: TrackedJobRecord = {
      id: "job-pf",
      title: "Preflight",
      job_type: "local_workspace_fix_preflight",
      status: "completed",
      params: {
        is_current: true,
        preflight_status: "ready_for_approval",
        operation_preflight: { preflight_status: "ready_for_approval" },
      },
    };
    expect(canApproveReadonlyExecution(job)).toBe(true);
  });

  it("blocks needs_information", () => {
    const job: TrackedJobRecord = {
      id: "job-pf2",
      title: "Preflight",
      job_type: "vercel_env_var_preflight",
      status: "completed",
      params: { is_current: true, preflight_status: "needs_information" },
    };
    expect(canApproveReadonlyExecution(job)).toBe(false);
  });
});
