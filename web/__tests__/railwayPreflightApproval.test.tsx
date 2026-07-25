import { describe, expect, it } from "vitest";

import {
  canApproveReadonlyExecution,
  isOperationPreflightJob,
  isReadonlyExecutionJob,
  preflightExecutionLabel,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

function railwayPreflightJob(overrides: Partial<TrackedJobRecord> = {}): TrackedJobRecord {
  return {
    id: "job-rw-pf",
    title: "Railway deployments preflight",
    job_type: "railway_deployments_preflight",
    status: "completed",
    params: {
      is_current: true,
      preflight_status: "ready_for_readonly_diagnostic",
      operation_preflight: {
        provider: "railway",
        operation_type: "list_deployments",
        target_name: "speakglobal-ai",
        target_status: "resolved",
        read_only_execution_enabled: true,
        preflight_status: "ready_for_readonly_diagnostic",
      },
    },
    ...overrides,
  };
}

describe("railwayPreflightApproval", () => {
  it("recognizes railway preflight job types", () => {
    expect(isOperationPreflightJob(railwayPreflightJob())).toBe(true);
    expect(isOperationPreflightJob(railwayPreflightJob({ job_type: "railway_project_details_preflight" }))).toBe(
      true,
    );
  });

  it("allows approve for ready railway deployments preflight", () => {
    expect(canApproveReadonlyExecution(railwayPreflightJob())).toBe(true);
    expect(preflightExecutionLabel(railwayPreflightJob())).toMatch(/approve read-only execution/i);
  });

  it("recognizes railway readonly execution jobs", () => {
    const exec: TrackedJobRecord = {
      id: "job-rw-exec",
      title: "Read-only execution",
      job_type: "readonly_execution_railway",
      status: "completed",
      params: { provider: "railway", read_only: true },
    };
    expect(isReadonlyExecutionJob(exec)).toBe(true);
  });
});
