import { describe, expect, it } from "vitest";

import {
  canApproveMutationExecution,
  isMutationPreflightJob,
  mutationExecutionBlocked,
  mutationLifecycleDisplay,
  mutationPreflightFromJob,
  mutationStatusLabel,
} from "@/lib/missionControl/mutationArtifacts";
import {
  mutationExecutionStateLabel,
  mutationVerificationStateLabel,
} from "@/lib/missionControl/mutationAudit";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

function job(partial: Partial<TrackedJobRecord>): TrackedJobRecord {
  return {
    id: "job-1",
    title: "Mutation preflight",
    job_type: "mutation_preflight",
    status: "completed",
    params: {},
    ...partial,
  } as TrackedJobRecord;
}

describe("mutationArtifacts", () => {
  it("detects approvable mutation preflight jobs", () => {
    const record = job({
      params: {
        preflight_status: "ready_for_mutation_approval",
        execution_blocked: false,
        mutation_preflight: {
          provider: "railway",
          operation_type: "restart",
          target_name: "api",
          target_resolved: true,
          risk_label: "T3 production impacting",
          preflight_status: "ready_for_mutation_approval",
          blast_radius: { scope: "production" },
        },
      },
    });
    expect(isMutationPreflightJob(record)).toBe(true);
    expect(mutationPreflightFromJob(record)?.provider).toBe("railway");
    expect(canApproveMutationExecution(record)).toBe(true);
    expect(mutationExecutionBlocked(record)).toBe(false);
    expect(mutationLifecycleDisplay(record)).toContain("awaiting approval");
  });

  it("separates execution completed from verified state", () => {
    const exec = {
      id: "exec-1",
      title: "Mutation execution",
      job_type: "mutation_execution",
      status: "completed",
      params: {
        executed: true,
        verification_job_id: "verify-1",
        verification_state: "verification_pending",
        execution_state: "execution_completed",
      },
    } as TrackedJobRecord;
    expect(mutationStatusLabel(exec)).toBe("verification pending");
    expect(mutationExecutionStateLabel(exec)).toBe("execution completed");
    expect(mutationVerificationStateLabel(exec)).toBe("verification pending");
    expect(mutationLifecycleDisplay(exec)).toContain("execution completed");
    expect(mutationLifecycleDisplay(exec)).toContain("verification pending");
  });
});
