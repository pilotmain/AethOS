import { describe, expect, it } from "vitest";

import { preflightExecutionLabel } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("executionStatusStreaming", () => {
  it("shows approve label when execution can start", () => {
    const job: TrackedJobRecord = {
      id: "job-pf",
      title: "Preflight",
      job_type: "vercel_logs_preflight",
      status: "completed",
      params: {
        is_current: true,
        preflight_status: "ready_for_readonly_diagnostic",
      },
    };
    expect(preflightExecutionLabel(job)).toMatch(/approve read-only execution/i);
  });
});
