import { describe, expect, it } from "vitest";

import {
  CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE,
  CANONICAL_READONLY_EXECUTION_JOB_TYPE,
  isOperationPreflightJob,
  isReadonlyExecutionJob,
  orchestrationLifecycleDisplay,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("canonicalOrchestrationRendering", () => {
  it("recognizes canonical preflight and execution jobs from Slice F", () => {
    const preflight: TrackedJobRecord = {
      id: "job-pf-canonical",
      title: "GitHub workflow runs preflight",
      job_type: CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE,
      status: "completed",
      params: {
        provider: "github",
        operation_type: "workflow_runs",
        operation_preflight: {
          provider: "github",
          operation_type: "workflow_runs",
          target_name: "pilotmain/AethOS",
          read_only_execution_enabled: true,
        },
      },
    };
    expect(isOperationPreflightJob(preflight)).toBe(true);
    expect(orchestrationLifecycleDisplay(preflight)).toBe(CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE);

    const execution: TrackedJobRecord = {
      id: "job-ex-canonical",
      title: "Read-only execution — workflow runs",
      job_type: CANONICAL_READONLY_EXECUTION_JOB_TYPE,
      status: "completed",
      params: {
        provider: "vercel",
        operation_type: "list_domains",
        readonly_execution: {
          provider: "vercel",
          operation_type: "list_domains",
          evidence: [{ source: "vercel_api", type: "domain_record", message: "invoicepilot.com" }],
        },
      },
    };
    expect(isReadonlyExecutionJob(execution)).toBe(true);
    expect(orchestrationLifecycleDisplay(execution)).toBe(CANONICAL_READONLY_EXECUTION_JOB_TYPE);
  });
});
