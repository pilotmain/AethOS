import { describe, expect, it } from "vitest";

import { preflightExecutionLabel } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("blockedPreflightNoApprovalButton", () => {
  it("does not show approve label when preflight is blocked", () => {
    const job: TrackedJobRecord = {
      id: "job-pf-1",
      title: "Logs preflight",
      job_type: "vercel_logs_preflight",
      status: "completed",
      params: {
        preflight_status: "blocked",
        operation_preflight: {
          operation_type: "check_logs",
          execution_enabled: false,
          preflight_status: "blocked",
        },
      },
    };
    expect(preflightExecutionLabel(job)).toMatch(/blocked/i);
    expect(preflightExecutionLabel(job)).not.toMatch(/approve read-only execution/i);
  });
});
