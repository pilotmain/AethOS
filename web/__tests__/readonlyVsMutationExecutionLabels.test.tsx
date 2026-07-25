import { describe, expect, it } from "vitest";

import {
  preflightExecutionLabel,
  preflightExecutionStatusLines,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("readonlyVsMutationExecutionLabels", () => {
  it("labels diagnostic preflights as read-only available", () => {
    const job: TrackedJobRecord = {
      id: "job-ro",
      title: "Preflight",
      job_type: "vercel_down_diagnostic_preflight",
      status: "completed",
      params: {
        preflight_status: "ready_for_readonly_diagnostic",
        operation_preflight: {
          operation_type: "why_down",
          read_only_execution_enabled: true,
          mutation_execution_enabled: false,
          phase: "9.3B",
        },
      },
    };
    expect(preflightExecutionLabel(job)).toMatch(/approve read-only execution/i);
    expect(preflightExecutionStatusLines(job).join(" ")).toMatch(/Mutating execution · disabled/);
  });

  it("labels mutating preflights as execution not enabled", () => {
    const job: TrackedJobRecord = {
      id: "job-mut",
      title: "Preflight",
      job_type: "vercel_redeploy_preflight",
      status: "completed",
      params: {
        preflight_status: "blocked",
        operation_preflight: {
          operation_type: "redeploy",
          read_only_execution_enabled: false,
          mutation_execution_enabled: false,
          phase: "9.3B",
        },
      },
    };
    expect(preflightExecutionLabel(job)).not.toMatch(/approve read-only execution/i);
    expect(preflightExecutionStatusLines(job).join(" ")).toMatch(/Read-only execution · not available/);
  });

  it("shows approved execution job reference", () => {
    const job: TrackedJobRecord = {
      id: "job-appr",
      title: "Preflight",
      job_type: "vercel_down_diagnostic_preflight",
      status: "completed",
      params: {
        execution_approved: true,
        execution_job_id: "job-5573764a5ffd",
        preflight_status: "ready_for_readonly_diagnostic",
        operation_preflight: {
          operation_type: "why_down",
          read_only_execution_enabled: true,
          execution_approved: true,
          execution_job_id: "job-5573764a5ffd",
          phase: "9.3B",
        },
      },
    };
    expect(preflightExecutionLabel(job)).toMatch(/Execution approved · job-5573764a5ffd/);
    expect(preflightExecutionStatusLines(job).join(" ")).toMatch(/Execution job · job-5573764a5ffd/);
  });
});
