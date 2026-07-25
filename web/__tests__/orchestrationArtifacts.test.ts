import { describe, expect, it } from "vitest";

import {
  CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE,
  CANONICAL_READONLY_EXECUTION_JOB_TYPE,
  isOperationPreflightJob,
  isReadonlyExecutionJob,
  orchestrationLifecycleDisplay,
  orchestrationOperationFromJob,
  orchestrationProviderFromJob,
  usesCanonicalOrchestrationJobType,
} from "@/lib/missionControl/orchestrationArtifacts";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("orchestrationArtifacts", () => {
  it("detects canonical operation_preflight jobs", () => {
    const job: TrackedJobRecord = {
      id: "job-pf-1",
      title: "Railway deployments preflight",
      job_type: CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE,
      status: "completed",
      params: {
        provider: "railway",
        operation_type: "list_deployments",
        operation_preflight: {
          provider: "railway",
          operation_type: "list_deployments",
          target_name: "speakglobal-ai",
        },
      },
    };
    expect(isOperationPreflightJob(job)).toBe(true);
    expect(orchestrationLifecycleDisplay(job)).toBe(CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE);
    expect(orchestrationProviderFromJob(job)).toBe("railway");
    expect(orchestrationOperationFromJob(job)).toBe("list_deployments");
    expect(usesCanonicalOrchestrationJobType(job)).toBe(true);
  });

  it("detects canonical readonly_execution jobs", () => {
    const job: TrackedJobRecord = {
      id: "job-ex-1",
      title: "Read-only execution",
      job_type: CANONICAL_READONLY_EXECUTION_JOB_TYPE,
      status: "completed",
      params: {
        provider: "github",
        operation_type: "workflow_runs",
        readonly_execution: {
          provider: "github",
          operation_type: "workflow_runs",
          target_name: "pilotmain/AethOS",
        },
      },
    };
    expect(isReadonlyExecutionJob(job)).toBe(true);
    expect(isOperationPreflightJob(job)).toBe(false);
    expect(orchestrationLifecycleDisplay(job)).toBe(CANONICAL_READONLY_EXECUTION_JOB_TYPE);
    expect(usesCanonicalOrchestrationJobType(job)).toBe(true);
  });

  it("supports legacy preflight job types", () => {
    const job: TrackedJobRecord = {
      id: "job-legacy-pf",
      title: "Vercel domains preflight",
      job_type: "vercel_domains_preflight",
      status: "completed",
      params: {
        operation_preflight: {
          provider: "vercel",
          operation_type: "list_domains",
          target_name: "invoicepilot",
        },
      },
    };
    expect(isOperationPreflightJob(job)).toBe(true);
    expect(orchestrationLifecycleDisplay(job)).toBe(CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE);
    expect(orchestrationProviderFromJob(job)).toBe("vercel");
  });

  it("supports legacy readonly execution job types", () => {
    const job: TrackedJobRecord = {
      id: "job-legacy-ex",
      title: "Read-only execution",
      job_type: "readonly_execution_railway",
      status: "completed",
      params: {
        provider: "railway",
        operation_type: "list_deployments",
        readonly_execution: {
          provider: "railway",
          operation_type: "list_deployments",
        },
      },
    };
    expect(isReadonlyExecutionJob(job)).toBe(true);
    expect(orchestrationLifecycleDisplay(job)).toBe(CANONICAL_READONLY_EXECUTION_JOB_TYPE);
  });

  it("falls back to execution_artifact param key for legacy railway tests", () => {
    const job: TrackedJobRecord = {
      id: "job-rw-legacy",
      title: "Read-only execution",
      job_type: "readonly_execution_railway",
      status: "completed",
      params: {
        provider: "railway",
        execution_artifact: {
          provider: "railway",
          operation_type: "why_down",
        },
      },
    };
    expect(isReadonlyExecutionJob(job)).toBe(true);
    expect(orchestrationProviderFromJob(job)).toBe("railway");
    expect(orchestrationOperationFromJob(job)).toBe("why_down");
  });
});
