import { describe, expect, it } from "vitest";

import {
  canApproveMutationExecution,
  mutationExecutionLabel,
} from "@/lib/missionControl/mutationArtifacts";
import {
  governedMutationSafetyCopy,
  pendingApprovalReviewLines,
} from "@/lib/missionControl/jobApprovalUx";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

function pendingMutationJob(): TrackedJobRecord {
  return {
    id: "job-9739f23d9d4f",
    title: "Railway restart mutation preflight",
    job_type: "mutation_preflight",
    status: "completed",
    params: {
      provider: "railway",
      operation_type: "restart",
      target_name: "atlas-trader api",
      preflight_status: "ready_for_mutation_approval",
      risk_tier: "T2_service_restart",
      blast_radius: { summary: "Single service restart" },
      rollback_plan: { summary: "Redeploy previous deployment" },
      mutation_preflight: {
        provider: "railway",
        operation_type: "restart",
        target_name: "atlas-trader api",
        preflight_status: "ready_for_mutation_approval",
        risk_tier: "T2_service_restart",
      },
      is_current: true,
    },
  } as TrackedJobRecord;
}

describe("durableJobsApproval", () => {
  it("shows review items for pending approval job", () => {
    const job = pendingMutationJob();
    const lines = pendingApprovalReviewLines(job);
    expect(lines.some((line) => line.includes("Operation"))).toBe(true);
    expect(lines.some((line) => line.includes("Provider"))).toBe(true);
    expect(lines.some((line) => line.includes("Risk tier"))).toBe(true);
    expect(lines.some((line) => line.includes("Blast radius"))).toBe(true);
    expect(lines.some((line) => line.includes("Rollback plan"))).toBe(true);
  });

  it("shows approve button label and safety copy", () => {
    const job = pendingMutationJob();
    expect(canApproveMutationExecution(job)).toBe(true);
    expect(mutationExecutionLabel(job)).toBe("Approve governed mutation");
    expect(governedMutationSafetyCopy(job)).toMatch(/No mutation has been performed yet/i);
  });

  it("does not add new sidebar navigation surfaces", () => {
    expect(governedMutationSafetyCopy(pendingMutationJob())).not.toMatch(/Validation Center/i);
    expect(governedMutationSafetyCopy(pendingMutationJob())).not.toMatch(/Webhook Truth/i);
  });
});
