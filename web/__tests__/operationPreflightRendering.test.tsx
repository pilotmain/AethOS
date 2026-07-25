import { describe, expect, it } from "vitest";

import {
  isOperationPreflightJob,
  operationPreflightFromJob,
  preflightExecutionLabel,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("operationPreflightRendering", () => {
  const job: TrackedJobRecord = {
    id: "job-pf1",
    title: "Vercel redeploy preflight",
    job_type: "vercel_redeploy_preflight",
    status: "completed",
    params: {
      operation_preflight: {
        target_name: "quotepilot",
        target_status: "resolved",
        provider: "vercel",
        operation_type: "redeploy",
        risk_level: "medium",
        execution_enabled: false,
        proposed_steps: ["Confirm latest deployment state"],
        blockers: ["Mutating operations remain disabled until a later phase."],
      },
    },
  };

  it("detects operation preflight jobs", () => {
    expect(isOperationPreflightJob(job)).toBe(true);
  });

  it("reads preflight artifact from job params", () => {
    const pf = operationPreflightFromJob(job);
    expect(pf?.target_name).toBe("quotepilot");
    expect(pf?.risk_level).toBe("medium");
  });

  it("blocks readonly approval for mutating preflights", () => {
    expect(preflightExecutionLabel(job)).toBe("Execution not enabled yet");
  });
});
