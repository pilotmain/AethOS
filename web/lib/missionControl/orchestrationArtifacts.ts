/** Canonical orchestration lifecycle — Phase 9.3M Slice G. */

import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

export const CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE = "operation_preflight";
export const CANONICAL_READONLY_EXECUTION_JOB_TYPE = "readonly_execution";

/** Legacy preflight job types — backward compat for in-flight jobs. */
export const LEGACY_OPERATION_PREFLIGHT_JOB_TYPES = new Set([
  "vercel_redeploy_preflight",
  "vercel_restart_preflight",
  "vercel_logs_preflight",
  "vercel_env_var_preflight",
  "vercel_down_diagnostic_preflight",
  "vercel_domains_preflight",
  "vercel_deployments_preflight",
  "vercel_project_details_preflight",
  "local_workspace_fix_preflight",
  "railway_redeploy_preflight",
  "railway_restart_preflight",
  "railway_logs_preflight",
  "railway_env_var_preflight",
  "railway_down_diagnostic_preflight",
  "railway_deployments_preflight",
  "railway_project_details_preflight",
  "github_workflow_runs_preflight",
  "github_workflow_diagnostic_preflight",
  "github_workflow_jobs_preflight",
]);

/** Legacy readonly execution job types — backward compat for in-flight jobs. */
export const LEGACY_READONLY_EXECUTION_JOB_TYPES = new Set([
  "readonly_execution_vercel",
  "readonly_execution_railway",
  "readonly_execution_github",
  "readonly_execution_local",
]);

function recordFromParams(params: Record<string, unknown>, key: string): Record<string, unknown> | null {
  const raw = params[key];
  if (!raw || typeof raw !== "object") return null;
  return raw as Record<string, unknown>;
}

function providerFromLegacyJobType(jobType: string): string | null {
  if (jobType.startsWith("railway_")) return "railway";
  if (jobType.startsWith("github_")) return "github";
  if (jobType.startsWith("vercel_")) return "vercel";
  if (jobType.startsWith("local_")) return "local";
  if (jobType === "readonly_execution_railway") return "railway";
  if (jobType === "readonly_execution_github") return "github";
  if (jobType === "readonly_execution_vercel") return "vercel";
  if (jobType === "readonly_execution_local") return "local";
  return null;
}

export function orchestrationProviderFromJob(job: TrackedJobRecord): string {
  const params = (job.params ?? {}) as Record<string, unknown>;
  if (typeof params.provider === "string" && params.provider.trim()) {
    return params.provider.trim().toLowerCase();
  }
  const pf = recordFromParams(params, "operation_preflight");
  if (typeof pf?.provider === "string" && pf.provider.trim()) {
    return pf.provider.trim().toLowerCase();
  }
  const re = recordFromParams(params, "readonly_execution") ?? recordFromParams(params, "execution_artifact");
  if (typeof re?.provider === "string" && re.provider.trim()) {
    return re.provider.trim().toLowerCase();
  }
  return providerFromLegacyJobType(job.job_type) ?? "unknown";
}

export function orchestrationOperationFromJob(job: TrackedJobRecord): string | undefined {
  const params = (job.params ?? {}) as Record<string, unknown>;
  if (typeof params.operation_type === "string" && params.operation_type) {
    return params.operation_type;
  }
  const pf = recordFromParams(params, "operation_preflight");
  if (typeof pf?.operation_type === "string" && pf.operation_type) {
    return pf.operation_type;
  }
  const re = recordFromParams(params, "readonly_execution") ?? recordFromParams(params, "execution_artifact");
  if (typeof re?.operation_type === "string" && re.operation_type) {
    return re.operation_type;
  }
  return undefined;
}

export function isReadonlyExecutionJob(job: TrackedJobRecord): boolean {
  if (job.job_type === CANONICAL_READONLY_EXECUTION_JOB_TYPE) return true;
  if (LEGACY_READONLY_EXECUTION_JOB_TYPES.has(job.job_type)) return true;
  const params = job.params ?? {};
  const artifact = params.readonly_execution ?? params.execution_artifact;
  return artifact != null && typeof artifact === "object";
}

export function isOperationPreflightJob(job: TrackedJobRecord): boolean {
  if (isReadonlyExecutionJob(job)) return false;
  if (job.job_type === CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE) return true;
  if (LEGACY_OPERATION_PREFLIGHT_JOB_TYPES.has(job.job_type)) return true;
  const pf = job.params?.operation_preflight;
  return pf != null && typeof pf === "object";
}

/** MC display label — canonical lifecycle category, not legacy job_type explosion. */
export function orchestrationLifecycleDisplay(job: TrackedJobRecord): string {
  if (isReadonlyExecutionJob(job)) return CANONICAL_READONLY_EXECUTION_JOB_TYPE;
  if (isOperationPreflightJob(job)) return CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE;
  return job.job_type;
}

/** Whether job uses canonical orchestration taxonomy (Slice F+). */
export function usesCanonicalOrchestrationJobType(job: TrackedJobRecord): boolean {
  return (
    job.job_type === CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE ||
    job.job_type === CANONICAL_READONLY_EXECUTION_JOB_TYPE
  );
}
