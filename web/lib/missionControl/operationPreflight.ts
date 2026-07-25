/** Operation preflight + read-only execution (Phase 9.3). */

import { mcFetch } from "@/lib/missionControl/fetch";
import {
  CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE,
  CANONICAL_READONLY_EXECUTION_JOB_TYPE,
  isOperationPreflightJob as isOrchestrationPreflightJob,
  isReadonlyExecutionJob as isOrchestrationReadonlyExecutionJob,
  orchestrationLifecycleDisplay,
  orchestrationOperationFromJob,
  orchestrationProviderFromJob,
  usesCanonicalOrchestrationJobType,
} from "@/lib/missionControl/orchestrationArtifacts";
import type { JobsGrouped, TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

export {
  CANONICAL_OPERATION_PREFLIGHT_JOB_TYPE,
  CANONICAL_READONLY_EXECUTION_JOB_TYPE,
  orchestrationLifecycleDisplay,
  orchestrationOperationFromJob,
  orchestrationProviderFromJob,
  usesCanonicalOrchestrationJobType,
};

export type OperationPreflightRecord = {
  operation_id?: string;
  provider?: string;
  operation_type?: string;
  target_name?: string | null;
  target_status?: string;
  risk_level?: string;
  required_approval?: boolean;
  execution_enabled?: boolean;
  read_only_execution_enabled?: boolean;
  mutation_execution_enabled?: boolean;
  approval_required?: boolean;
  phase?: string;
  execution_approved?: boolean;
  execution_job_id?: string | null;
  preflight_status?: string;
  proposed_steps?: string[];
  blockers?: string[];
  evidence?: string[];
  missing_information?: string[];
  next_action?: string;
  current_state?: Record<string, unknown>;
};

export function isOperationPreflightJob(job: TrackedJobRecord): boolean {
  return isOrchestrationPreflightJob(job);
}

export function operationPreflightFromJob(job: TrackedJobRecord): OperationPreflightRecord | null {
  const raw = job.params?.operation_preflight;
  if (!raw || typeof raw !== "object") return null;
  return raw as OperationPreflightRecord;
}

export function preflightStatus(job: TrackedJobRecord): string {
  const pf = operationPreflightFromJob(job);
  const fromParams = job.params?.preflight_status;
  if (typeof fromParams === "string" && fromParams) return fromParams;
  if (typeof pf?.preflight_status === "string" && pf.preflight_status) return pf.preflight_status;
  return "ready_for_approval";
}

export function isCurrentPreflight(job: TrackedJobRecord): boolean {
  if (job.params?.is_current === false) return false;
  if (preflightStatus(job) === "superseded") return false;
  return true;
}

export function preflightStatusLabel(job: TrackedJobRecord): string {
  const status = preflightStatus(job);
  const labels: Record<string, string> = {
    ready_for_approval: "Preflight ready",
    ready_for_readonly_diagnostic: "Ready for read-only diagnostic",
    needs_information: "Needs info",
    blocked: "Blocked",
    superseded: "Superseded",
    execution_not_enabled: "Execution not enabled yet",
  };
  return labels[status] ?? status.replace(/_/g, " ");
}

export function partitionPreflights(items: TrackedJobRecord[]): {
  current: TrackedJobRecord[];
  previous: TrackedJobRecord[];
} {
  const current: TrackedJobRecord[] = [];
  const previous: TrackedJobRecord[] = [];
  for (const job of items) {
    if (isCurrentPreflight(job)) current.push(job);
    else previous.push(job);
  }
  return { current, previous };
}

export function partitionCompletedJobs(items: TrackedJobRecord[]): {
  operationPreflights: TrackedJobRecord[];
  trackedWork: TrackedJobRecord[];
} {
  const operationPreflights: TrackedJobRecord[] = [];
  const trackedWork: TrackedJobRecord[] = [];
  for (const job of items) {
    if (isOperationPreflightJob(job)) operationPreflights.push(job);
    else trackedWork.push(job);
  }
  return { operationPreflights, trackedWork };
}

export function missingInfoQuestions(job: TrackedJobRecord): string[] {
  const pf = operationPreflightFromJob(job);
  if (!pf) return [];
  const missing = new Set<string>();
  for (const m of pf.missing_information ?? []) {
    if (typeof m === "string") missing.add(m);
  }
  const questions: string[] = [];
  if (missing.has("exact_env_value_confirmation") || missing.has("environment_target")) {
    questions.push("Exact env value and environment target (Production / Preview / Development / all)");
  }
  if (missing.has("explicit_repo_path")) {
    questions.push("Repo path or permission to use canonical workspace");
  }
  return questions;
}

const MUTATING_OPERATIONS = new Set([
  "redeploy",
  "restart",
  "set_env_var",
  "deploy_from_git",
  "local_commit_preflight",
  "local_push_preflight",
  "git_deploy_preflight",
]);

export function isMutatingOperation(operationType: string | undefined | null): boolean {
  if (!operationType) return false;
  return MUTATING_OPERATIONS.has(operationType);
}

export function canApproveReadonlyExecution(job: TrackedJobRecord): boolean {
  if (job.status !== "completed") return false;
  if (!isCurrentPreflight(job)) return false;
  if (job.params?.execution_approved === true) return false;
  const pf = operationPreflightFromJob(job);
  if (isMutatingOperation(pf?.operation_type)) return false;
  const status = preflightStatus(job);
  if (status === "needs_information" || status === "superseded" || status === "blocked") {
    return false;
  }
  return status === "ready_for_approval" || status === "ready_for_readonly_diagnostic";
}

export async function approveReadonlyExecution(preflightJobId: string): Promise<{
  preflight_job: TrackedJobRecord;
  execution_job: TrackedJobRecord;
}> {
  return mcFetch(`/api/v1/jobs/${encodeURIComponent(preflightJobId)}/approve-readonly-execution`, {
    method: "POST",
    body: "{}",
  });
}

export function isReadonlyExecutionJob(job: TrackedJobRecord): boolean {
  return isOrchestrationReadonlyExecutionJob(job);
}

export type ExecutionTimelineEntry = {
  status?: string;
  label?: string;
  message?: string;
  at?: number;
};

export function executionTimelineFromJob(job: TrackedJobRecord): ExecutionTimelineEntry[] {
  const params = job.params ?? {};
  const topLevel = params.execution_timeline;
  if (Array.isArray(topLevel)) {
    return topLevel.filter((e): e is ExecutionTimelineEntry => e != null && typeof e === "object");
  }
  const artifact = readonlyExecutionFromJob(job);
  const nested = artifact?.timeline ?? artifact?.execution_timeline;
  if (Array.isArray(nested)) {
    return nested.filter((e): e is ExecutionTimelineEntry => e != null && typeof e === "object");
  }
  return [];
}

export type ExecutionEvidenceItem = {
  source?: string;
  type?: string;
  confidence?: string;
  message?: string;
  at?: string | number;
};

export function readonlyExecutionFromJob(job: TrackedJobRecord): Record<string, unknown> | null {
  const params = job.params ?? {};
  const raw = params.readonly_execution ?? params.execution_artifact;
  if (!raw || typeof raw !== "object") return null;
  return raw as Record<string, unknown>;
}

export function executionEvidenceFromJob(job: TrackedJobRecord): ExecutionEvidenceItem[] {
  const artifact = readonlyExecutionFromJob(job);
  const raw = artifact?.evidence;
  if (!Array.isArray(raw)) return [];
  return raw.filter((e): e is ExecutionEvidenceItem => e != null && typeof e === "object");
}

export function executionOperationalEventsFromJob(job: TrackedJobRecord): ExecutionTimelineEntry[] {
  const artifact = readonlyExecutionFromJob(job);
  const raw = artifact?.operational_events;
  if (!Array.isArray(raw)) return [];
  return raw.filter((e): e is ExecutionTimelineEntry => e != null && typeof e === "object");
}

export function executionConfidenceLabel(job: TrackedJobRecord): string {
  const artifact = readonlyExecutionFromJob(job);
  const confidence = artifact?.confidence;
  return typeof confidence === "string" ? confidence.replace(/_/g, " ") : "";
}

export function executionDataSourceLabel(job: TrackedJobRecord): string {
  const source = job.params?.data_source;
  if (source === "provider_api") return "Provider API execution";
  if (source === "browser_fallback") return "Browser fallback used for missing provider API data";
  if (source === "memory") return "Operational memory";
  return typeof source === "string" && source ? source.replace(/_/g, " ") : "";
}

export function readonlyExecutionBadge(job: TrackedJobRecord): string {
  return job.params?.read_only === true || isReadonlyExecutionJob(job)
    ? "Read-only execution · No mutation performed"
    : "";
}

export function operationCapabilityFromJob(job: TrackedJobRecord): {
  apiCapable?: boolean;
  browserRequired?: boolean;
  authMethod?: string;
} {
  const pf = operationPreflightFromJob(job);
  const pfState = (pf?.current_state ?? {}) as Record<string, unknown>;
  const params = (job.params ?? {}) as Record<string, unknown>;
  const state = {
    ...pfState,
    ...(typeof params.api_capable === "boolean" ? { api_capable: params.api_capable } : {}),
    ...(typeof params.browser_runtime_required === "boolean"
      ? { browser_runtime_required: params.browser_runtime_required }
      : {}),
    ...(typeof params.auth_method === "string" ? { auth_method: params.auth_method } : {}),
  };
  return {
    apiCapable: state.api_capable === true,
    browserRequired: state.browser_runtime_required === true,
    authMethod: typeof state.auth_method === "string" ? state.auth_method : undefined,
  };
}

export function showsApiTokenPreflightPath(job: TrackedJobRecord): boolean {
  const cap = operationCapabilityFromJob(job);
  return cap.apiCapable === true && cap.authMethod === "api_token";
}

export function isBrowserUnavailableInformational(job: TrackedJobRecord): boolean {
  const cap = operationCapabilityFromJob(job);
  return cap.apiCapable === true && cap.browserRequired === false;
}

export function preflightExecutionStatus(job: TrackedJobRecord): {
  phase?: string;
  readOnlyExecutionEnabled?: boolean;
  mutationExecutionEnabled?: boolean;
  approvalRequired?: boolean;
  executionApproved?: boolean;
  executionJobId?: string;
} {
  const pf = operationPreflightFromJob(job);
  const params = job.params ?? {};
  const approved = params.execution_approved === true || pf?.execution_approved === true;
  const jobId =
    (typeof params.execution_job_id === "string" ? params.execution_job_id : undefined) ??
    (typeof pf?.execution_job_id === "string" ? pf.execution_job_id : undefined);
  return {
    phase: pf?.phase ?? "9.3B",
    readOnlyExecutionEnabled: pf?.read_only_execution_enabled === true,
    mutationExecutionEnabled: pf?.mutation_execution_enabled === true,
    approvalRequired: pf?.approval_required ?? pf?.required_approval,
    executionApproved: approved,
    executionJobId: jobId,
  };
}

export function preflightExecutionStatusLines(job: TrackedJobRecord): string[] {
  const status = preflightExecutionStatus(job);
  const lines: string[] = [`Phase ${status.phase ?? "9.3B"}`];
  if (status.executionApproved) {
    lines.push("Execution approved");
    if (status.executionJobId) lines.push(`Execution job · ${status.executionJobId}`);
  }
  if (status.readOnlyExecutionEnabled) {
    lines.push(status.executionApproved ? "Read-only execution · approved" : "Read-only execution · available after approval");
  } else {
    lines.push("Read-only execution · not available");
  }
  lines.push("Mutating execution · disabled");
  return lines;
}

export function preflightExecutionLabel(job: TrackedJobRecord): string {
  if (job.params?.execution_approved === true) {
    const eid = job.params?.execution_job_id;
    return eid ? `Execution approved · ${eid}` : "Execution approved";
  }
  if (preflightStatus(job) === "blocked") {
    return "Blocked — browser runtime unavailable";
  }
  if (canApproveReadonlyExecution(job)) return "Approve read-only execution";
  const pf = operationPreflightFromJob(job);
  if (pf?.read_only_execution_enabled) return "Read-only execution available";
  if (pf?.execution_enabled) return "Approve execution";
  return "Execution not enabled yet";
}

export function executionJobIdFromPreflight(job: TrackedJobRecord): string | undefined {
  return preflightExecutionStatus(job).executionJobId;
}

export function preflightJobIdFromExecution(job: TrackedJobRecord): string | undefined {
  const source = job.params?.source_preflight_job_id;
  return typeof source === "string" ? source : undefined;
}

export function mcJobAnchorId(jobId: string): string {
  return `mc-job-${jobId}`;
}

const PREFLIGHT_DEBUG_STATE_KEYS = new Set([
  "known_in_memory",
  "api_capable",
  "credential_id",
  "resolution_source",
  "browser_fallback_available",
  "browser_runtime_required",
  "auth_method",
  "auth_method_label",
  "browser_required",
  "resolution_message",
  "evidence",
  "signal",
]);

export function preflightDebugState(job: TrackedJobRecord): Record<string, unknown> {
  const pf = operationPreflightFromJob(job);
  const state = (pf?.current_state ?? {}) as Record<string, unknown>;
  const debug: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(state)) {
    if (PREFLIGHT_DEBUG_STATE_KEYS.has(key)) {
      debug[key] = value;
    }
  }
  return debug;
}

export function readonlyExecutionCardMeta(job: TrackedJobRecord): {
  operation: string;
  target: string;
  provider: string;
  authMethod: string;
  dataSource: string;
  evidenceCount: number;
  evidenceSummary: ExecutionEvidenceSummary;
  timelineCount: number;
  statusReason: string;
} {
  const artifact = readonlyExecutionFromJob(job);
  const params = job.params ?? {};
  const evidenceSummary = executionEvidenceSummary(job);
  return {
    operation: String(
      artifact?.operation_type ?? params.operation_type ?? orchestrationOperationFromJob(job) ?? job.job_type,
    ).replace(/_/g, " "),
    target: String(artifact?.target_name ?? params.target_name ?? "(none)"),
    provider: String(artifact?.provider ?? params.provider ?? orchestrationProviderFromJob(job)),
    authMethod: String(
      artifact?.auth_method_label ?? params.auth_method_label ?? params.auth_method ?? "unknown",
    ),
    dataSource: executionDataSourceLabel(job) || String(params.data_source ?? "unknown"),
    evidenceCount: evidenceSummary.total,
    evidenceSummary,
    timelineCount:
      executionOperationalEventsFromJob(job).length || executionTimelineFromJob(job).length,
    statusReason: String(params.status_reason ?? ""),
  };
}

export function isReadonlyExecutionTimedOut(job: TrackedJobRecord): boolean {
  return job.params?.status_reason === "execution_timed_out";
}

function splitReadonly(items: TrackedJobRecord[]): {
  readonly: TrackedJobRecord[];
  other: TrackedJobRecord[];
} {
  const readonly: TrackedJobRecord[] = [];
  const other: TrackedJobRecord[] = [];
  for (const job of items) {
    if (isReadonlyExecutionJob(job)) readonly.push(job);
    else other.push(job);
  }
  return { readonly, other };
}

export function partitionGroupedJobs(grouped: JobsGrouped): {
  readonlyExecutions: JobsGrouped;
  withoutReadonlyExecutions: JobsGrouped;
} {
  const q = splitReadonly(grouped.queued);
  const r = splitReadonly(grouped.running);
  const c = splitReadonly(grouped.completed);
  const f = splitReadonly(grouped.failed);
  const x = splitReadonly(grouped.cancelled);
  return {
    readonlyExecutions: {
      queued: q.readonly,
      running: r.readonly,
      completed: c.readonly,
      failed: f.readonly,
      cancelled: x.readonly,
    },
    withoutReadonlyExecutions: {
      queued: q.other,
      running: r.other,
      completed: c.other,
      failed: f.other,
      cancelled: x.other,
    },
  };
}

export function executionDiagnosticFromJob(job: TrackedJobRecord): Record<string, unknown> {
  const artifact = readonlyExecutionFromJob(job);
  const raw = artifact?.diagnostic;
  if (!raw || typeof raw !== "object") return {};
  return raw as Record<string, unknown>;
}

export function executionEvidenceByTier(job: TrackedJobRecord): Record<string, ExecutionEvidenceItem[]> {
  const diag = executionDiagnosticFromJob(job);
  const tiers = diag.evidence_by_tier;
  if (!tiers || typeof tiers !== "object") return {};
  return tiers as Record<string, ExecutionEvidenceItem[]>;
}

export type ExecutionEvidenceSummary = {
  primary: number;
  supporting: number;
  historical: number;
  debug: number;
  total: number;
  hasTiers: boolean;
};

export function executionEvidenceSummary(job: TrackedJobRecord): ExecutionEvidenceSummary {
  const tiers = executionEvidenceByTier(job);
  const tierKeys = ["primary", "supporting", "historical", "debug"] as const;
  const counts = tierKeys.map((key) => (Array.isArray(tiers[key]) ? tiers[key].length : 0));
  const tierTotal = counts.reduce((sum, n) => sum + n, 0);
  if (tierTotal > 0) {
    return {
      primary: counts[0],
      supporting: counts[1],
      historical: counts[2],
      debug: counts[3],
      total: tierTotal,
      hasTiers: true,
    };
  }
  const flat = executionEvidenceFromJob(job).length;
  return {
    primary: flat,
    supporting: 0,
    historical: 0,
    debug: 0,
    total: flat,
    hasTiers: false,
  };
}

/** Compact MC label — tiered when diagnostic grouping exists. */
export function formatExecutionEvidenceLabel(job: TrackedJobRecord): string {
  const summary = executionEvidenceSummary(job);
  if (summary.total === 0) return "";
  if (!summary.hasTiers) {
    return `Evidence: ${summary.total}`;
  }
  const parts: string[] = [];
  if (summary.primary > 0) parts.push(`Primary: ${summary.primary}`);
  if (summary.supporting > 0) parts.push(`Supporting: ${summary.supporting}`);
  if (summary.historical > 0) parts.push(`Historical: ${summary.historical}`);
  return parts.length > 0 ? parts.join(" · ") : `Evidence: ${summary.primary}`;
}

export function formatExecutionDebugEvidenceLabel(job: TrackedJobRecord): string {
  const summary = executionEvidenceSummary(job);
  if (!summary.hasTiers || summary.debug === 0) return "";
  return `Debug records: ${summary.debug}`;
}

export function productionImpactLabel(job: TrackedJobRecord): string {
  const diag = executionDiagnosticFromJob(job);
  const conf = diag.production_impact_confidence;
  return typeof conf === "string" ? conf.replace(/_/g, " ") : "";
}

export function formatOperationalEventAt(at: unknown): string {
  if (typeof at === "string" && at.includes("UTC")) return at;
  if (typeof at === "number" && at > 1_000_000_000_000) {
    try {
      return new Date(at).toISOString().replace("T", " ").slice(0, 16) + " UTC";
    } catch {
      return String(at);
    }
  }
  return typeof at === "string" ? at : "";
}

export function readonlyExecutionsEmpty(grouped: JobsGrouped): boolean {
  return (
    grouped.queued.length +
      grouped.running.length +
      grouped.completed.length +
      grouped.failed.length +
      grouped.cancelled.length ===
    0
  );
}
