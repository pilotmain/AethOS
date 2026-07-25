/** Governed mutation approval UX helpers — Mission Control Durable Jobs. */

import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";
import {
  blastRadiusFromJob,
  mutationPreflightFromJob,
  mutationRiskLabel,
} from "@/lib/missionControl/mutationArtifacts";
import {
  orchestrationOperationFromJob,
  orchestrationProviderFromJob,
} from "@/lib/missionControl/operationPreflight";

export type PendingApprovalRecord = {
  job_id: string;
  approval_surface?: string;
  approval_action_label?: string;
  ui_action_available?: boolean;
  provider?: string | null;
  operation_type?: string | null;
  target_name?: string | null;
  risk_tier?: string | null;
  blast_radius?: Record<string, unknown> | null;
  rollback_plan?: Record<string, unknown> | null;
};

export function pendingApprovalReviewLines(job: PendingApprovalRecord | TrackedJobRecord): string[] {
  const id = "job_id" in job ? job.job_id : job.id;
  const provider =
    ("provider" in job && job.provider) ||
    orchestrationProviderFromJob(job as TrackedJobRecord) ||
    mutationPreflightFromJob(job as TrackedJobRecord)?.provider ||
    "unknown";
  const operation =
    ("operation_type" in job && job.operation_type) ||
    orchestrationOperationFromJob(job as TrackedJobRecord) ||
    mutationPreflightFromJob(job as TrackedJobRecord)?.operation_type ||
    "mutation";
  const risk =
    ("risk_tier" in job && job.risk_tier) ||
    mutationRiskLabel(job as TrackedJobRecord) ||
    "—";
  const blast =
    ("blast_radius" in job && job.blast_radius && typeof job.blast_radius === "object"
      ? (job.blast_radius as { summary?: string }).summary
      : undefined) ||
    blastRadiusFromJob(job as TrackedJobRecord)?.summary ||
    "Review blast radius in preflight";
  const rollback =
    ("rollback_plan" in job && job.rollback_plan && typeof job.rollback_plan === "object"
      ? (job.rollback_plan as { summary?: string }).summary
      : undefined) || "Review rollback plan in preflight";
  const target =
    ("target_name" in job && job.target_name) ||
    mutationPreflightFromJob(job as TrackedJobRecord)?.target_name ||
    "—";

  return [
    `Job: ${id}`,
    `Operation: ${String(operation).replace(/_/g, " ")}`,
    `Provider: ${provider}`,
    `Target service: ${target}`,
    `Risk tier: ${risk}`,
    `Blast radius: ${blast}`,
    `Rollback plan: ${rollback}`,
  ];
}

export function governedMutationSafetyCopy(job: PendingApprovalRecord | TrackedJobRecord): string {
  const provider =
    ("provider" in job && job.provider) ||
    mutationPreflightFromJob(job as TrackedJobRecord)?.provider ||
    "provider";
  const operation =
    ("operation_type" in job && job.operation_type) ||
    mutationPreflightFromJob(job as TrackedJobRecord)?.operation_type ||
    "mutation";
  return `No mutation has been performed yet. Approval will execute the governed ${String(provider)} ${String(operation).replace(/_/g, " ")}.`;
}
