import { describe, expect, it } from "vitest";

import { preflightExecutionLabel } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

/** Phase 9.3: mutating preflights must not offer read-only execution approval. */
describe("mutationBlockedPhase92", () => {
  it("never enables execution label for mutating operations", () => {
    const job: TrackedJobRecord = {
      id: "job-x",
      title: "Preflight",
      job_type: "vercel_restart_preflight",
      status: "completed",
      params: {
        preflight_status: "ready_for_approval",
        operation_preflight: {
          operation_type: "restart",
          execution_enabled: false,
        },
        execution_enabled: false,
      },
    };
    expect(preflightExecutionLabel(job)).not.toMatch(/approve read-only execution/i);
    expect(preflightExecutionLabel(job)).toMatch(/not enabled/i);
  });
});
