import { describe, expect, it } from "vitest";

import {
  canApproveMutationExecution,
  mutationExecutionLabel,
  targetResolvedFromJob,
} from "@/lib/missionControl/mutationArtifacts";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

function mutationJob(overrides: Partial<TrackedJobRecord> = {}): TrackedJobRecord {
  return {
    id: "job-test-target",
    title: "Railway restart mutation preflight",
    job_type: "mutation_preflight",
    status: "completed",
    source: "chat",
    session_id: "default",
    params: {
      provider: "railway",
      operation_type: "restart",
      preflight_status: "ready_for_mutation_approval",
      target_resolved: true,
      target_name: "atlas-trader api",
      target: {
        service_name: "atlas-trader api",
        project_name: "atlas-trader",
        environment: "production",
        resolved: true,
      },
      mutation_preflight: {
        provider: "railway",
        operation_type: "restart",
        target_name: "atlas-trader api",
        target_resolved: true,
        preflight_status: "ready_for_mutation_approval",
      },
      is_current: true,
    },
    ...overrides,
  } as TrackedJobRecord;
}

describe("runtimeActionsTargetResolution", () => {
  it("resolved target allows approval when preflight is ready", () => {
    const job = mutationJob();
    expect(targetResolvedFromJob(job)).toBe(true);
    expect(canApproveMutationExecution(job)).toBe(true);
    expect(mutationExecutionLabel(job)).toBe("Approve governed mutation");
  });

  it("unresolved target blocks approval", () => {
    const job = mutationJob({
      params: {
        provider: "railway",
        operation_type: "restart",
        preflight_status: "needs_information",
        target_resolved: false,
        mutation_preflight: {
          provider: "railway",
          operation_type: "restart",
          preflight_status: "needs_information",
          target_resolved: false,
        },
        is_current: true,
      },
    });
    expect(targetResolvedFromJob(job)).toBe(false);
    expect(canApproveMutationExecution(job)).toBe(false);
    expect(mutationExecutionLabel(job)).toBe("Resolve target before approval");
  });

  it("runtime actions panel exposes resolve target action", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const source = fs.readFileSync(
      path.join(process.cwd(), "components/JobsTrackedWorkPanel.tsx"),
      "utf8",
    );
    expect(source).toContain("Resolve target");
    expect(source).toContain("resolveJobTarget");
    expect(source).toContain("Approval blocked");
  });
});
