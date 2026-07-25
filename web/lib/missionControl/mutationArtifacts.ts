/** Mutation governance artifacts — Phase 9.6/9.7 governed execution. */

import { mcFetch } from "@/lib/missionControl/fetch";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

export const CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE = "mutation_preflight";
export const CANONICAL_MUTATION_EXECUTION_JOB_TYPE = "mutation_execution";

export type MutationPreflightRecord = {
  provider?: string;
  operation_type?: string;
  target_name?: string | null;
  target_resolved?: boolean;
  target?: Record<string, unknown> | null;
  risk_tier?: string;
  risk_label?: string;
  preflight_status?: string;
  mutation_execution_enabled?: boolean;
  mutation_execution_approved?: boolean;
  mutation_execution_job_id?: string | null;
  rollback_plan?: Record<string, unknown>;
  blast_radius?: Record<string, unknown>;
  required_future_steps?: string[];
  audit?: Record<string, unknown>;
  credential_guidance?: CredentialGuidanceRecord;
  credential_requirements_reply?: string;
};

export type CredentialGuidanceRecord = {
  preflight_status?: string;
  provider?: string;
  provider_label?: string;
  operation_type?: string;
  target_name?: string | null;
  target_path?: string;
  missing_credentials?: string[];
  why_needed?: string;
  setup_steps?: Array<{ kind: string; label: string; detail?: string }>;
  reload_instructions?: string[];
  retry_steps?: string[];
  retry_phrase?: string;
  credential_center_path?: string;
  blocked_reason?: string;
};

export type OperationLifecycleRecord = {
  provider?: string;
  project?: string | null;
  environment?: string | null;
  service?: string | null;
  operation?: string;
  preflight_job_id?: string | null;
  execution_job_id?: string | null;
  approval_status?: string;
  execution_status?: string;
  verification_status?: string;
  canonical_state?: string;
  credential_blocked?: boolean;
  latest_summary?: string;
};

export type PostMutationVerificationRecord = {
  status?: string;
  last_checked_at?: string | number | null;
  service_health?: string;
  provider_command_submitted?: boolean;
  logs_after_execution?: boolean;
  evidence_summary?: string;
  before_status?: string;
  after_status?: string;
};

export type RepairLearningRecord = {
  operation?: string;
  target?: string;
  result?: string;
  helped?: boolean;
  health_after?: string;
  lesson?: string;
  recommended_next_action?: string;
  avoid_repeat_restart?: boolean;
  evidence?: string[];
  attempted_at?: string;
};

export function repairLearningFromJob(job: TrackedJobRecord): RepairLearningRecord | null {
  const raw = job.params?.repair_learning;
  if (!raw || typeof raw !== "object") return null;
  const record = raw as Record<string, unknown>;
  return {
    operation: String(record.operation ?? ""),
    target: String(record.target ?? ""),
    result: String(record.result ?? ""),
    helped: record.helped === true,
    health_after: String(record.health_after ?? ""),
    lesson: String(record.lesson ?? ""),
    recommended_next_action: record.helped
      ? "Continue monitoring recovery and confirm with fresh logs."
      : "Inspect deeper failure evidence before repeating the mutation.",
    avoid_repeat_restart: record.helped === false && String(record.operation ?? "") === "restart",
    evidence: Array.isArray(record.evidence) ? record.evidence.map(String) : [],
    attempted_at: String(record.attempted_at ?? ""),
  };
}

export function repairLearningSummary(job: TrackedJobRecord): string | null {
  const record = repairLearningFromJob(job);
  if (!record) return null;
  const parts = ["Repair learning"];
  if (record.operation) parts.push(`${record.operation.replace(/_/g, " ")} attempted`);
  parts.push(record.helped ? "helped" : "did not resolve");
  if (record.health_after) parts.push(`health: ${record.health_after}`);
  return parts.join(" · ");
}

export function postMutationVerificationFromJob(job: TrackedJobRecord): PostMutationVerificationRecord | null {
  const params = job.params ?? {};
  const execId = isMutationExecutionJob(job) ? job.id : mutationExecutionJobId(job);
  if (!execId && !params.executed) return null;
  const before = params.railway_before_snapshot as Record<string, unknown> | undefined;
  const after = params.railway_after_snapshot as Record<string, unknown> | undefined;
  const logSummary =
    typeof (params.provider_evidence_bundle as Record<string, unknown> | undefined)?.log_summary === "string"
      ? String((params.provider_evidence_bundle as Record<string, unknown>).log_summary)
      : "";
  const status = String(
    params.post_mutation_verification_status ??
      params.restart_verification_state ??
      params.verification_state ??
      "",
  );
  if (!status && params.executed !== true) return null;
  const lastChecked = params.verification_completed_at ?? params.updated_at;
  const providerResult = params.provider_result as { ok?: boolean } | undefined;
  return {
    status: status || "unconfirmed",
    last_checked_at:
      typeof lastChecked === "string" || typeof lastChecked === "number" ? lastChecked : null,
    service_health: String(params.restart_service_health ?? "unknown"),
    provider_command_submitted: Boolean(params.restart_command_submitted ?? providerResult?.ok),
    logs_after_execution: Boolean(logSummary),
    evidence_summary: logSummary || String(params.lifecycle_summary ?? ""),
    before_status: String(before?.latest_deployment_status ?? ""),
    after_status: String(after?.latest_deployment_status ?? ""),
  };
}

export function postMutationVerificationSummary(job: TrackedJobRecord): string | null {
  const record = postMutationVerificationFromJob(job);
  if (!record) return null;
  const parts = ["Verification"];
  if (record.status) parts.push(String(record.status).replace(/_/g, " "));
  if (record.service_health) parts.push(`health: ${record.service_health}`);
  return parts.join(" · ");
}

export function operationLifecycleFromJob(job: TrackedJobRecord): OperationLifecycleRecord | null {
  const raw = job.params?.operation_lifecycle;
  if (raw && typeof raw === "object") return raw as OperationLifecycleRecord;
  const execId = mutationExecutionJobId(job);
  if (!execId && mutationPreflightStatus(job) !== "ready_for_mutation_approval") {
    return null;
  }
  return {
    provider: String(mutationPreflightFromJob(job)?.provider ?? job.params?.provider ?? ""),
    service: String(mutationPreflightFromJob(job)?.target_name ?? job.params?.target_name ?? ""),
    operation: String(mutationPreflightFromJob(job)?.operation_type ?? job.params?.operation_type ?? ""),
    preflight_job_id: job.id,
    execution_job_id: execId,
    approval_status: job.params?.mutation_execution_approved ? "approved" : mutationPreflightStatus(job),
    execution_status: execId ? (job.params?.executed === true ? "completed" : "running") : "none",
    verification_status: String(job.params?.verification_state ?? "none"),
    canonical_state: String(job.params?.canonical_lifecycle_state ?? ""),
    latest_summary: String(job.params?.lifecycle_summary ?? ""),
  };
}

export function operationLifecycleSummary(job: TrackedJobRecord): string | null {
  const lifecycle = operationLifecycleFromJob(job);
  if (!lifecycle) return null;
  const parts = ["Latest lifecycle"];
  if (lifecycle.approval_status) parts.push(`preflight: ${String(lifecycle.approval_status).replace(/_/g, " ")}`);
  if (lifecycle.execution_status && lifecycle.execution_status !== "none") {
    parts.push(`execution: ${lifecycle.execution_status}`);
  }
  if (lifecycle.verification_status && lifecycle.verification_status !== "none") {
    parts.push(`verification: ${lifecycle.verification_status}`);
  }
  return parts.join(" · ");
}

export function isMutationPreflightJob(job: TrackedJobRecord): boolean {
  return job.job_type === CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE;
}

export function isMutationExecutionJob(job: TrackedJobRecord): boolean {
  return job.job_type === CANONICAL_MUTATION_EXECUTION_JOB_TYPE;
}

export function mutationPreflightFromJob(job: TrackedJobRecord): MutationPreflightRecord | null {
  const raw = job.params?.mutation_preflight;
  if (!raw || typeof raw !== "object") return null;
  return raw as MutationPreflightRecord;
}

export function mutationPreflightStatus(job: TrackedJobRecord): string {
  const pf = mutationPreflightFromJob(job);
  const fromParams = job.params?.preflight_status;
  if (typeof fromParams === "string" && fromParams) return fromParams;
  if (typeof pf?.preflight_status === "string" && pf.preflight_status) return pf.preflight_status;
  return "design_only_blocked";
}

export function isCurrentMutationPreflight(job: TrackedJobRecord): boolean {
  if (!isMutationPreflightJob(job)) return false;
  if (job.params?.is_current === false) return false;
  return mutationPreflightStatus(job) !== "superseded";
}

export function mutationStatusLabel(job: TrackedJobRecord): string {
  if (isMutationExecutionJob(job)) {
    const summary = job.params?.lifecycle_summary;
    if (typeof summary === "string" && summary.includes(" · ")) {
      const tail = summary.split(" · ").slice(1).join(" · ");
      if (tail) return tail;
    }
    if (job.params?.dry_run === true) return "dry-run";
    if (job.params?.executed !== true) return "execution failed";
    const vState = job.params?.verification_state;
    if (vState === "verified" || job.params?.verified === true) return "verified";
    if (vState === "verification_failed") return "verification failed";
    if (vState === "verification_running") return "verification running";
    if (job.params?.verification_job_id) return "verification pending";
    return "execution completed";
  }
  const status = mutationPreflightStatus(job);
  const labels: Record<string, string> = {
    ready_for_mutation_approval: "Awaiting approval",
    needs_workflow_resolution: "Discovery failed",
    design_only_blocked: "Design-only",
    needs_information: "Needs target",
    needs_credential: "Missing credential",
    needs_credential_repair: "Credential repair required",
    superseded: "Superseded",
    blocked: "Blocked",
  };
  return labels[status] ?? status.replace(/_/g, " ");
}

export function mutationTimelineSteps(job: TrackedJobRecord): string[] {
  if (isMutationPreflightJob(job)) {
    const steps = ["Preflight"];
    const status = mutationPreflightStatus(job);
    if (status === "ready_for_mutation_approval") steps.push("Awaiting approval");
    if (job.params?.mutation_execution_approved) steps.push("Approved");
    const execId = mutationExecutionJobId(job);
    if (execId) steps.push("Execution enqueued");
    steps.push("Audit");
    return steps;
  }
  if (isMutationExecutionJob(job)) {
    const steps = ["Preflight", "Awaiting approval", "Approved"];
    if (job.status === "running") steps.push("Execution running");
    else if (job.params?.executed === true) steps.push("Execution completed");
    else steps.push("Execution failed");
    const vState = String(job.params?.verification_state ?? "");
    if (job.params?.verification_job_id || vState) {
      if (vState === "verified" || job.params?.verified) steps.push("Verified");
      else if (vState === "verification_failed") steps.push("Verification failed");
      else steps.push("Verification running");
    }
    steps.push("Audit recorded");
    return steps;
  }
  return [];
}

export function mutationEvidenceTitle(job: TrackedJobRecord): string {
  const provider = String(mutationPreflightFromJob(job)?.provider ?? job.params?.provider ?? "unknown");
  const op = String(mutationPreflightFromJob(job)?.operation_type ?? job.params?.operation_type ?? "mutation");
  if (provider === "github" && op === "workflow_rerun") return "GitHub workflow rerun evidence";
  if (provider === "railway" && op === "restart") return "Railway restart evidence";
  if (provider === "railway" && op === "redeploy") return "Railway redeploy evidence";
  if (provider === "vercel" && op === "redeploy") return "Vercel deployment evidence";
  return `${provider} ${op.replace(/_/g, " ")} evidence`;
}

export function partitionMutationJobs(items: TrackedJobRecord[]): {
  mutationPreflights: TrackedJobRecord[];
  mutationExecutions: TrackedJobRecord[];
  other: TrackedJobRecord[];
} {
  const mutationPreflights: TrackedJobRecord[] = [];
  const mutationExecutions: TrackedJobRecord[] = [];
  const other: TrackedJobRecord[] = [];
  for (const job of items) {
    if (isMutationPreflightJob(job)) mutationPreflights.push(job);
    else if (isMutationExecutionJob(job)) mutationExecutions.push(job);
    else other.push(job);
  }
  return { mutationPreflights, mutationExecutions, other };
}

export function mutationRiskLabel(job: TrackedJobRecord): string | undefined {
  const pf = mutationPreflightFromJob(job);
  if (pf?.risk_label) return pf.risk_label;
  const tier = job.params?.risk_tier;
  return typeof tier === "string" ? tier.replace(/_/g, " ") : undefined;
}

export function blastRadiusFromJob(job: TrackedJobRecord): Record<string, unknown> | null {
  const pf = mutationPreflightFromJob(job);
  const br = pf?.blast_radius ?? job.params?.blast_radius;
  if (!br || typeof br !== "object") return null;
  return br as Record<string, unknown>;
}

export function mutationExecutionJobId(job: TrackedJobRecord): string | null {
  const pf = mutationPreflightFromJob(job);
  const id = pf?.mutation_execution_job_id ?? job.params?.mutation_execution_job_id;
  return typeof id === "string" && id ? id : null;
}

export function preflightPostApprovalLabel(job: TrackedJobRecord): string {
  if (!isMutationPreflightJob(job) || !pfApproved(job)) return mutationExecutionLabel(job);
  const execId = mutationExecutionJobId(job);
  if (!execId) return "Approved · execution pending";
  return "Approved · view execution below";
}

export function mutationExecutionStatusLabel(job: TrackedJobRecord): string {
  if (!isMutationExecutionJob(job)) return mutationExecutionLabel(job);
  const execState = String(job.params?.execution_state ?? "");
  const verState = String(job.params?.verification_state ?? "");
  const restartState = String(job.params?.restart_verification_state ?? "");
  const error =
    (job.params?.mutation_execution as Record<string, unknown> | undefined)?.error ??
    ((job.params?.mutation_execution as Record<string, unknown> | undefined)?.provider_result as Record<string, unknown> | undefined)?.detail;
  if (job.params?.executed === false || execState === "execution_failed") {
    const reason = typeof error === "string" && error.toLowerCase().includes("credential")
      ? "Railway mutation credentials are not configured."
      : typeof error === "string"
        ? error
        : "Execution failed";
    return `Execution failed · ${reason}`;
  }
  if (restartState === "restart_transition_detected" && (verState === "verified" || job.params?.verified === true)) {
    return "Restart transition verified";
  }
  if (restartState === "service_online_but_restart_unproven" || restartState === "restart_unverified") {
    return "Restart unverified · same deployment";
  }
  if (verState === "verified" || job.params?.verified === true) return "Restart verified";
  if (execState === "provider_mutation_requested" || execState === "stabilizing") {
    if (verState === "verification_pending" || verState === "verification_running" || job.params?.verification_job_id) {
      return "Restart requested · stabilizing";
    }
    return "Restart requested";
  }
  if (job.status === "queued") return "Execution queued";
  return mutationExecutionStatusLabel(job);
}

export type RailwayRestartEvidence = {
  providerRequest: string;
  restartCommandSubmitted: string;
  restartTransition: string;
  serviceHealth: string;
  finalVerification: string;
  transitionProof?: string;
};

export function railwayRestartEvidenceFromJob(job: TrackedJobRecord): RailwayRestartEvidence | null {
  if (!isMutationExecutionJob(job)) return null;
  if (String(job.params?.provider ?? "") !== "railway") return null;
  const providerRequest = String(job.params?.restart_provider_request ?? "unknown");
  const restartCommandSubmitted =
    job.params?.restart_command_submitted === true
      ? "submitted"
      : job.params?.restart_command_submitted === false
        ? "not submitted"
        : "unknown";
  const restartTransition = String(job.params?.restart_transition ?? "not_detected");
  const serviceHealth = String(job.params?.restart_service_health ?? "unknown");
  const finalVerification = String(job.params?.restart_final_verification ?? "unverified");
  const transitionProof =
    typeof job.params?.restart_transition_proof === "string" ? job.params.restart_transition_proof : undefined;
  if (
    providerRequest === "unknown" &&
    restartCommandSubmitted === "unknown" &&
    restartTransition === "not_detected" &&
    serviceHealth === "unknown" &&
    finalVerification === "unverified" &&
    !job.params?.restart_verification_state
  ) {
    return null;
  }
  return { providerRequest, restartCommandSubmitted, restartTransition, serviceHealth, finalVerification, transitionProof };
}

export function railwayRestartEvidenceLabel(evidence: RailwayRestartEvidence): string {
  const parts = [
    `Provider request: ${evidence.providerRequest}`,
    `Restart command: ${evidence.restartCommandSubmitted}`,
    `Restart transition: ${evidence.restartTransition.replace(/_/g, " ")}`,
    `Service health: ${evidence.serviceHealth}`,
    `Final verification: ${evidence.finalVerification}`,
  ];
  if (evidence.transitionProof && evidence.transitionProof !== "none") {
    parts.push(`Transition proof: ${evidence.transitionProof}`);
  }
  return parts.join(" · ");
}

export type ProviderEvidenceCards = {
  providerCommand: string;
  restartEvidence: string;
  deploymentEvidence: string;
  logsAfterApproval: string;
  runtimeHealth: string;
  diagnosis: string;
  fixPlan: string;
  finalStatus: string;
};

export function providerEvidenceCardsFromJob(job: TrackedJobRecord): ProviderEvidenceCards | null {
  if (!isMutationExecutionJob(job) || String(job.params?.provider ?? "") !== "railway") return null;
  const bundle = (job.params?.provider_evidence_bundle ?? (job.params?.mutation_execution as Record<string, unknown> | undefined)?.provider_evidence_bundle) as
    | Record<string, unknown>
    | undefined;
  if (!bundle || typeof bundle !== "object") return null;
  const evidence = (bundle.evidence ?? {}) as Record<string, unknown>;
  const verification = (bundle.verification ?? {}) as Record<string, unknown>;
  const before = (bundle.before ?? {}) as Record<string, unknown>;
  const after = (bundle.after ?? {}) as Record<string, unknown>;
  const diagnosis = (bundle.diagnosis ?? job.params?.provider_diagnosis) as Record<string, unknown> | undefined;
  const fixPlan = (bundle.fix_plan ?? job.params?.provider_fix_plan) as Record<string, unknown> | undefined;
  return {
    providerCommand: String(bundle.command ?? job.params?.command ?? "unknown"),
    restartEvidence: evidence.log_activity_after_approval
      ? `logs updated · ${String(after.last_log_at ?? "after approval")}`
      : "no log activity detected",
    deploymentEvidence: evidence.deployment_transition_detected
      ? `transition detected · ${String(after.latest_deployment_id ?? after.active_deployment_id ?? "unknown")}`
      : `unchanged · ${String(before.latest_deployment_id ?? before.active_deployment_id ?? "unknown")}`,
    logsAfterApproval: String(after.last_log_at ?? "unknown"),
    runtimeHealth: evidence.health_confirmed ? "online" : "unknown",
    diagnosis: typeof diagnosis?.summary === "string" ? diagnosis.summary : "none",
    fixPlan: typeof fixPlan?.summary === "string" ? fixPlan.summary : "none",
    finalStatus: String(verification.status ?? job.params?.restart_verification_state ?? "unverified"),
  };
}

export function providerEvidenceCardsLabel(cards: ProviderEvidenceCards): string {
  return [
    `Command: ${cards.providerCommand}`,
    `Restart evidence: ${cards.restartEvidence}`,
    `Deployment: ${cards.deploymentEvidence}`,
    `Logs after approval: ${cards.logsAfterApproval}`,
    `Health: ${cards.runtimeHealth}`,
    `Final status: ${cards.finalStatus}`,
  ].join(" · ");
}

export function targetMetadataFromJob(job: TrackedJobRecord): Record<string, unknown> | null {
  const pf = mutationPreflightFromJob(job);
  const raw = job.params?.target ?? pf?.target;
  if (!raw || typeof raw !== "object") return null;
  return raw as Record<string, unknown>;
}

export function targetResolvedFromJob(job: TrackedJobRecord): boolean {
  if (job.params?.target_resolved === true) return true;
  const pf = mutationPreflightFromJob(job);
  if (pf?.target_resolved === true) return true;
  const target = targetMetadataFromJob(job);
  if (target?.resolved === true) return true;
  const status = mutationPreflightStatus(job);
  if (status === "needs_information") return false;
  return Boolean(pf?.target_name ?? job.params?.target_name);
}

export function credentialGuidanceFromJob(job: TrackedJobRecord): CredentialGuidanceRecord | null {
  const params = job.params ?? {};
  const pf = mutationPreflightFromJob(job);
  const raw = params.credential_guidance ?? pf?.credential_guidance;
  if (!raw || typeof raw !== "object") return null;
  return raw as CredentialGuidanceRecord;
}

export function isCredentialBlockedPreflight(job: TrackedJobRecord): boolean {
  const status = mutationPreflightStatus(job);
  return status === "needs_credential" || status === "needs_credential_repair";
}

export function mutationCredentialBlockedLabel(job: TrackedJobRecord): string {
  const guidance = credentialGuidanceFromJob(job);
  const missing = guidance?.missing_credentials?.[0];
  if (missing) return `Missing credential · ${missing}`;
  if (mutationPreflightStatus(job) === "needs_credential_repair") return "Credential repair required";
  return "Missing provider credential";
}

export function canApproveMutationExecution(job: TrackedJobRecord): boolean {
  if (!isMutationPreflightJob(job)) return false;
  if (job.status !== "completed") return false;
  if (job.params?.is_current === false) return false;
  const status = mutationPreflightStatus(job);
  if (status !== "ready_for_mutation_approval") return false;
  if (!targetResolvedFromJob(job)) return false;
  const pf = mutationPreflightFromJob(job);
  if (pf?.mutation_execution_approved) return false;
  return true;
}

export function mutationExecutionLabel(job: TrackedJobRecord): string {
  if (!canApproveMutationExecution(job)) {
    const status = mutationPreflightStatus(job);
    if (status === "design_only_blocked") return "Mutation execution disabled";
    if (status === "needs_credential" || status === "needs_credential_repair") {
      return mutationCredentialBlockedLabel(job);
    }
    if (status === "needs_information" || !targetResolvedFromJob(job)) return "Resolve target before approval";
    if (pfApproved(job)) return preflightPostApprovalLabel(job);
    return "Mutation not approvable";
  }
  return "Approve governed mutation";
}

function pfApproved(job: TrackedJobRecord): boolean {
  const pf = mutationPreflightFromJob(job);
  return Boolean(pf?.mutation_execution_approved || job.params?.mutation_execution_approved);
}

export function mutationExecutionBlocked(job: TrackedJobRecord): boolean {
  if (isMutationExecutionJob(job)) {
    return job.params?.executed !== true;
  }
  const params = job.params ?? {};
  if (params.execution_blocked === true) return true;
  return mutationPreflightStatus(job) !== "ready_for_mutation_approval";
}

export function mutationLifecycleDisplay(job: TrackedJobRecord): string {
  if (isMutationPreflightJob(job)) {
    const status = mutationPreflightStatus(job);
    const risk = mutationRiskLabel(job);
    const parts = ["Mutation preflight"];
    if (status === "ready_for_mutation_approval") parts.push("awaiting approval");
    else parts.push("governed");
    if (risk) parts.push(risk);
    if (status) parts.push(status.replace(/_/g, " "));
    return parts.join(" · ");
  }
  if (isMutationExecutionJob(job)) {
    const summary = job.params?.lifecycle_summary;
    if (typeof summary === "string" && summary) return summary;
    const exec = job.params?.executed === true ? "execution completed" : job.params?.dry_run ? "dry-run" : "execution failed";
    const ver =
      job.params?.verification_state === "verified" || job.params?.verified
        ? "verified healthy"
        : job.params?.verification_state === "verification_failed"
          ? "verification failed"
          : job.params?.verification_job_id
            ? "verification pending"
            : null;
    return ver ? `Mutation · ${exec} · ${ver}` : `Mutation execution · ${exec}`;
  }
  return "Mutation artifact";
}

export async function approveMutationExecution(jobId: string): Promise<{
  preflight_job?: TrackedJobRecord;
  mutation_execution_job?: TrackedJobRecord;
}> {
  return mcFetch<{
    preflight_job?: TrackedJobRecord;
    mutation_execution_job?: TrackedJobRecord;
  }>(`/api/v1/jobs/${encodeURIComponent(jobId)}/approve-mutation-execution`, {
    method: "POST",
    body: "{}",
  });
}

export async function fetchRailwayTargets(): Promise<{ candidates: Array<Record<string, unknown>> }> {
  return mcFetch<{ candidates: Array<Record<string, unknown>> }>("/api/v1/providers/railway/targets");
}

export async function resolveJobTarget(
  jobId: string,
  serviceName: string,
): Promise<{ job?: TrackedJobRecord }> {
  return mcFetch<{ job?: TrackedJobRecord }>(`/api/v1/jobs/${encodeURIComponent(jobId)}/resolve-target`, {
    method: "POST",
    body: JSON.stringify({ service_name: serviceName }),
  });
}

export async function refreshJobTargets(jobId: string): Promise<{ candidates: Array<Record<string, unknown>> }> {
  return mcFetch<{ candidates: Array<Record<string, unknown>> }>(
    `/api/v1/jobs/${encodeURIComponent(jobId)}/refresh-targets`,
    { method: "POST", body: "{}" },
  );
}

export async function fetchCredentialRequirements(jobId: string): Promise<Record<string, unknown>> {
  return mcFetch<Record<string, unknown>>(`/api/v1/credentials/requirements/${encodeURIComponent(jobId)}`);
}

export async function refreshCredentialsAndPreflight(jobId?: string): Promise<Record<string, unknown>> {
  return mcFetch<Record<string, unknown>>("/api/v1/credentials/refresh", {
    method: "POST",
    body: JSON.stringify(jobId ? { job_id: jobId } : {}),
  });
}
