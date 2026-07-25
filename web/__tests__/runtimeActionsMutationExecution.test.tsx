import { describe, expect, it } from "vitest";

import {
  mutationExecutionStatusLabel,
  preflightPostApprovalLabel,
  providerEvidenceCardsFromJob,
  providerEvidenceCardsLabel,
} from "@/lib/missionControl/mutationArtifacts";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

function execJob(overrides: Partial<TrackedJobRecord> = {}): TrackedJobRecord {
  return {
    id: "job-exec-test",
    title: "Mutation execution — restart",
    job_type: "mutation_execution",
    status: "completed",
    source: "mutation_approval",
    session_id: "default",
    params: {
      provider: "railway",
      operation_type: "restart",
      target_name: "atlas-trader api",
      executed: true,
      provider_mutation_requested: true,
      execution_state: "provider_mutation_requested",
      verification_state: "verification_pending",
      verification_job_id: "job-verify-1",
      mutation_execution: {
        provider_result: { ok: true },
      },
    },
    ...overrides,
  } as TrackedJobRecord;
}

function preflightJob(execId = "job-exec-test"): TrackedJobRecord {
  return {
    id: "job-pf-test",
    title: "Railway restart mutation preflight",
    job_type: "mutation_preflight",
    status: "completed",
    source: "chat",
    session_id: "default",
    params: {
      provider: "railway",
      operation_type: "restart",
      target_name: "atlas-trader api",
      mutation_execution_approved: true,
      mutation_execution_job_id: execId,
      preflight_status: "ready_for_mutation_approval",
      mutation_preflight: {
        mutation_execution_approved: true,
        mutation_execution_job_id: execId,
      },
      is_current: true,
    },
  } as TrackedJobRecord;
}

describe("runtimeActionsMutationExecution", () => {
  it("approved preflight points to execution below", () => {
    expect(preflightPostApprovalLabel(preflightJob())).toBe("Approved · view execution below");
  });

  it("provider accepted shows restart requested", () => {
    expect(mutationExecutionStatusLabel(execJob())).toBe("Restart requested · stabilizing");
  });

  it("missing credentials show execution failed", () => {
    const job = execJob({
      params: {
        provider: "railway",
        operation_type: "restart",
        executed: false,
        execution_state: "execution_failed",
        mutation_execution: {
          provider_result: { detail: "Railway mutation credentials are not configured." },
        },
      },
    });
    expect(mutationExecutionStatusLabel(job)).toContain("Execution failed");
    expect(mutationExecutionStatusLabel(job)).toContain("credentials");
  });

  it("runtime actions panel renders execution status helper", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const source = fs.readFileSync(
      path.join(process.cwd(), "components/JobsTrackedWorkPanel.tsx"),
      "utf8",
    );
    expect(source).toContain("mutationExecutionStatusLabel");
  });

  it("provider evidence cards show restart verified without deployment transition", () => {
    const job = execJob({
      params: {
        provider: "railway",
        operation_type: "restart",
        executed: true,
        command: "railway restart --service 'atlas-trader api' --yes --json",
        provider_evidence_bundle: {
          command: "railway restart --service 'atlas-trader api' --yes --json",
          command_submitted: true,
          before: { latest_deployment_id: "dep-old" },
          after: { latest_deployment_id: "dep-old", last_log_at: "2026-01-15T12:05:00+00:00" },
          evidence: {
            log_activity_after_approval: true,
            deployment_transition_detected: false,
            health_confirmed: true,
          },
          verification: { status: "verified_restart", verified: true },
        },
      },
    });
    const cards = providerEvidenceCardsFromJob(job);
    expect(cards).not.toBeNull();
    expect(cards?.deploymentEvidence).toContain("unchanged");
    expect(cards?.restartEvidence).toContain("logs updated");
    expect(cards?.finalStatus).toBe("verified_restart");
    expect(providerEvidenceCardsLabel(cards!)).toContain("verified_restart");
  });
});
