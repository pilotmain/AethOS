import { describe, expect, it } from "vitest";

import {
  canApproveReadonlyExecution,
  isOperationPreflightJob,
  isReadonlyExecutionJob,
  preflightExecutionLabel,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

function githubPreflightJob(overrides: Partial<TrackedJobRecord> = {}): TrackedJobRecord {
  return {
    id: "job-gh-pf",
    title: "GitHub workflow runs preflight",
    job_type: "github_workflow_runs_preflight",
    status: "completed",
    params: {
      is_current: true,
      preflight_status: "ready_for_readonly_diagnostic",
      operation_preflight: {
        provider: "github",
        operation_type: "workflow_runs",
        target_name: "pilotmain/AethOS",
        target_status: "resolved",
        read_only_execution_enabled: true,
        preflight_status: "ready_for_readonly_diagnostic",
      },
    },
    ...overrides,
  };
}

describe("githubPreflightApproval", () => {
  it("recognizes github preflight job types", () => {
    expect(isOperationPreflightJob(githubPreflightJob())).toBe(true);
  });

  it("allows approve for ready github workflow runs preflight", () => {
    expect(canApproveReadonlyExecution(githubPreflightJob())).toBe(true);
    expect(preflightExecutionLabel(githubPreflightJob())).toMatch(/approve read-only execution/i);
  });

  it("recognizes github workflow diagnostic preflight job types", () => {
    expect(
      isOperationPreflightJob(
        githubPreflightJob({ job_type: "github_workflow_diagnostic_preflight" }),
      ),
    ).toBe(true);
  });

  it("allows approve for ready github workflow diagnostic preflight", () => {
    const job = githubPreflightJob({
      job_type: "github_workflow_diagnostic_preflight",
      params: {
        is_current: true,
        preflight_status: "ready_for_readonly_diagnostic",
        operation_preflight: {
          provider: "github",
          operation_type: "workflow_diagnostic",
          target_name: "pilotmain/AethOS",
          target_status: "resolved",
          read_only_execution_enabled: true,
          preflight_status: "ready_for_readonly_diagnostic",
        },
      },
    });
    expect(canApproveReadonlyExecution(job)).toBe(true);
    expect(preflightExecutionLabel(job)).toMatch(/approve read-only execution/i);
  });

  it("recognizes github workflow jobs preflight job types", () => {
    expect(
      isOperationPreflightJob(
        githubPreflightJob({ job_type: "github_workflow_jobs_preflight" }),
      ),
    ).toBe(true);
  });

  it("allows approve for ready github workflow jobs preflight", () => {
    const job = githubPreflightJob({
      job_type: "github_workflow_jobs_preflight",
      params: {
        is_current: true,
        preflight_status: "ready_for_readonly_diagnostic",
        operation_preflight: {
          provider: "github",
          operation_type: "workflow_jobs",
          target_name: "pilotmain/AethOS",
          target_status: "resolved",
          read_only_execution_enabled: true,
          preflight_status: "ready_for_readonly_diagnostic",
        },
      },
    });
    expect(canApproveReadonlyExecution(job)).toBe(true);
    expect(preflightExecutionLabel(job)).toMatch(/approve read-only execution/i);
  });

  it("recognizes github readonly execution jobs", () => {
    const exec: TrackedJobRecord = {
      id: "job-gh-exec",
      title: "Read-only execution",
      job_type: "readonly_execution_github",
      status: "completed",
      params: { provider: "github", read_only: true },
    };
    expect(isReadonlyExecutionJob(exec)).toBe(true);
  });
});
