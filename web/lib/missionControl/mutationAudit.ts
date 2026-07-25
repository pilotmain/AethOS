/** Mutation audit chain — Phase 9.6.2+ centralized history with dedupe. */

import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";
import {
  isCurrentMutationPreflight,
  isMutationExecutionJob,
  isMutationPreflightJob,
  mutationEvidenceTitle,
  mutationExecutionJobId,
  mutationPreflightFromJob,
} from "@/lib/missionControl/mutationArtifacts";

export type MutationAuditStep = {
  key: string;
  label: string;
  jobId?: string;
  timestamp?: string;
  status?: string;
};

export type MutationAuditRecord = {
  chainId: string;
  chainKey: string;
  provider: string;
  operation: string;
  target?: string | null;
  preflightJobId?: string;
  executionJobId?: string;
  verificationJobId?: string;
  executionState?: string;
  verificationState?: string;
  lifecycleState?: string;
  canonicalLifecycleState?: string;
  failureType?: string;
  failureClassification?: string;
  isCurrent: boolean;
  steps: MutationAuditStep[];
  evidenceTitle?: string;
  lifecycleSummary?: string;
};

function stepTimestamp(job: TrackedJobRecord | undefined): string | undefined {
  if (!job) return undefined;
  const ts = job.completed_at ?? job.updated_at ?? job.created_at;
  return typeof ts === "string" ? ts : undefined;
}

function chainKey(provider: string, operation: string, target: string | null): string {
  return `${provider}:${operation}:${target ?? ""}`;
}

function recordScore(record: MutationAuditRecord): number {
  let score = 0;
  if (record.isCurrent) score += 100;
  if (record.executionJobId) score += 50;
  if (record.verificationJobId) score += 25;
  if (record.canonicalLifecycleState === "audit_recorded" || record.canonicalLifecycleState === "verified") score += 20;
  if (record.preflightJobId) score += 10;
  return score;
}

function buildSingleRecord(
  pf: TrackedJobRecord | undefined,
  execJob: TrackedJobRecord | undefined,
  verifyJob: TrackedJobRecord | undefined,
  isCurrent: boolean,
): MutationAuditRecord {
  const meta = mutationPreflightFromJob(pf ?? execJob ?? ({} as TrackedJobRecord));
  const provider = String(meta?.provider ?? pf?.params?.provider ?? execJob?.params?.provider ?? "unknown");
  const operation = String(meta?.operation_type ?? pf?.params?.operation_type ?? execJob?.params?.operation_type ?? "mutation");
  const targetRaw = meta?.target_name ?? pf?.params?.target_name ?? execJob?.params?.target_name ?? null;
  const target = typeof targetRaw === "string" ? targetRaw : null;
  const execId = execJob?.id ?? (pf ? mutationExecutionJobId(pf) ?? undefined : undefined);
  const verifyId =
    typeof execJob?.params?.verification_job_id === "string"
      ? execJob.params.verification_job_id
      : verifyJob?.id;

  const approved = Boolean(pf?.params?.mutation_execution_approved);
  const execRunning = execJob?.status === "running";
  const execCompleted = execJob?.params?.execution_state === "execution_completed" || execJob?.params?.executed === true;
  const verState = String(execJob?.params?.verification_state ?? "");
  const verified = verState === "verified" || execJob?.params?.verified === true;

  const steps: MutationAuditStep[] = [
    { key: "preflight", label: "Preflight", jobId: pf?.id, timestamp: stepTimestamp(pf), status: "completed" },
    {
      key: "approval",
      label: approved ? "Approved" : "Awaiting approval",
      timestamp: stepTimestamp(pf),
      status: approved ? "approved" : "awaiting_approval",
    },
  ];
  if (execRunning) {
    steps.push({ key: "execution", label: "Execution running", jobId: execId, timestamp: stepTimestamp(execJob), status: "execution_running" });
  } else if (execCompleted) {
    steps.push({ key: "execution", label: "Execution completed", jobId: execId, timestamp: stepTimestamp(execJob), status: "execution_completed" });
  } else if (execJob) {
    steps.push({ key: "execution", label: "Execution failed", jobId: execId, timestamp: stepTimestamp(execJob), status: "execution_failed" });
  }
  if (verifyId) {
    if (verified) {
      steps.push({ key: "verification", label: "Verified", jobId: verifyId, timestamp: stepTimestamp(verifyJob), status: "verified" });
    } else if (verState === "verification_running" || verState === "verification_pending") {
      steps.push({ key: "verification", label: "Verification running", jobId: verifyId, timestamp: stepTimestamp(verifyJob), status: verState });
    } else if (verState === "verification_failed") {
      steps.push({ key: "verification", label: "Verification failed", jobId: verifyId, timestamp: stepTimestamp(verifyJob), status: "verification_failed" });
    } else {
      steps.push({ key: "verification", label: "Verification", jobId: verifyId, timestamp: stepTimestamp(verifyJob), status: verState || "verification_pending" });
    }
  }
  steps.push({ key: "audit", label: "Audit recorded", timestamp: stepTimestamp(execJob ?? pf), status: "audit_recorded" });

  const key = chainKey(provider, operation, target);
  return {
    chainId: pf?.id ?? execId ?? key,
    chainKey: key,
    provider,
    operation,
    target,
    preflightJobId: pf?.id,
    executionJobId: execId,
    verificationJobId: verifyId,
    executionState: typeof execJob?.params?.execution_state === "string" ? execJob.params.execution_state : undefined,
    verificationState: typeof execJob?.params?.verification_state === "string" ? execJob.params.verification_state : undefined,
    lifecycleState: typeof execJob?.params?.lifecycle_state === "string" ? execJob.params.lifecycle_state : undefined,
    canonicalLifecycleState:
      typeof execJob?.params?.canonical_lifecycle_state === "string"
        ? execJob.params.canonical_lifecycle_state
        : undefined,
    failureType: typeof execJob?.params?.failure_type === "string" ? execJob.params.failure_type : undefined,
    failureClassification:
      typeof execJob?.params?.failure_classification === "string"
        ? execJob.params.failure_classification
        : undefined,
    lifecycleSummary:
      typeof execJob?.params?.lifecycle_summary === "string" ? execJob.params.lifecycle_summary : undefined,
    isCurrent,
    steps,
    evidenceTitle: execJob ? mutationEvidenceTitle(execJob) : pf ? mutationEvidenceTitle(pf) : undefined,
  };
}

export function buildMutationAuditRecords(jobs: TrackedJobRecord[]): MutationAuditRecord[] {
  const byId = new Map(jobs.map((j) => [j.id, j]));
  const raw: MutationAuditRecord[] = [];
  const seenExec = new Set<string>();

  for (const job of jobs) {
    if (isMutationPreflightJob(job)) {
      const execId = mutationExecutionJobId(job);
      const execJob = execId ? byId.get(execId) : undefined;
      const verifyId =
        typeof execJob?.params?.verification_job_id === "string" ? execJob.params.verification_job_id : undefined;
      const verifyJob = verifyId ? byId.get(verifyId) : undefined;
      if (execId) seenExec.add(execId);
      raw.push(buildSingleRecord(job, execJob, verifyJob, isCurrentMutationPreflight(job)));
    }
  }

  for (const job of jobs) {
    if (!isMutationExecutionJob(job) || seenExec.has(job.id)) continue;
    const verifyId =
      typeof job.params?.verification_job_id === "string" ? job.params.verification_job_id : undefined;
    raw.push(buildSingleRecord(undefined, job, verifyId ? byId.get(verifyId) : undefined, false));
  }

  const bestByKey = new Map<string, MutationAuditRecord>();
  for (const record of raw) {
    const existing = bestByKey.get(record.chainKey);
    if (!existing || recordScore(record) > recordScore(existing)) {
      bestByKey.set(record.chainKey, record);
    }
  }

  return [...bestByKey.values()].sort((a, b) => (b.chainId > a.chainId ? 1 : -1));
}

export function partitionMutationAuditRecords(jobs: TrackedJobRecord[]): {
  current: MutationAuditRecord[];
  historical: MutationAuditRecord[];
} {
  const all = buildMutationAuditRecords(jobs);
  const current = all.filter((r) => r.isCurrent);
  const currentKeys = new Set(current.map((r) => r.chainKey));
  const historical = all.filter((r) => !r.isCurrent && !currentKeys.has(r.chainKey));
  return { current, historical };
}

export function mutationLifecycleSummary(job: TrackedJobRecord): string | null {
  const summary = job.params?.lifecycle_summary;
  if (typeof summary === "string" && summary.trim()) return summary;
  const artifact = job.params?.mutation_execution;
  if (artifact && typeof artifact === "object") {
    const inner = (artifact as Record<string, unknown>).lifecycle_summary;
    if (typeof inner === "string" && inner.trim()) return inner;
  }
  return null;
}

export function mutationExecutionStateLabel(job: TrackedJobRecord): string {
  const summary = mutationLifecycleSummary(job);
  if (summary) {
    const parts = summary.split(" · ");
    const idx = parts.findIndex((p) => p.includes("execution"));
    if (idx >= 0) return parts[idx].trim();
  }
  const state = job.params?.execution_state;
  if (typeof state === "string" && state) return state.replace(/_/g, " ");
  if (job.params?.executed === true) return "execution completed";
  if (job.params?.dry_run === true) return "dry-run";
  return "execution failed";
}

export function mutationVerificationStateLabel(job: TrackedJobRecord): string {
  const summary = mutationLifecycleSummary(job);
  if (summary) {
    if (summary.includes("verified healthy")) return "verified healthy";
    if (summary.includes("verification failed")) return "verification failed";
    if (summary.includes("verification timeout")) return "verification timeout";
    if (summary.includes("verification inconclusive")) return "verification inconclusive";
    if (summary.includes("verification running")) return "verification running";
    if (summary.includes("rollback suggested")) return "rollback suggested";
  }
  const state = job.params?.verification_state;
  if (typeof state === "string" && state) {
    const labels: Record<string, string> = {
      verification_pending: "verification pending",
      verification_running: "verification running",
      verified: "verified healthy",
      verification_failed: "verification failed",
      verification_timeout: "verification timeout",
      verification_inconclusive: "verification inconclusive",
    };
    return labels[state] ?? state.replace(/_/g, " ");
  }
  if (job.params?.verified === true) return "verified healthy";
  if (job.params?.rollback_suggested === true) return "rollback suggested";
  if (job.params?.rollback_required === true) return "rollback required";
  if (job.params?.verification_job_id) return "verification pending";
  return "verification not started";
}

export function mutationFailureClassificationLabel(job: TrackedJobRecord): string | null {
  const fc = job.params?.failure_classification ?? job.params?.failure_type;
  return typeof fc === "string" && fc ? fc.replace(/_/g, " ") : null;
}
