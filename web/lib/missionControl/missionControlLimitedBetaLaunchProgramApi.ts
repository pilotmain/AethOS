/** FIX 312 — Limited beta launch program (management ≠ provisioning authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type LimitedBetaLaunchProgramResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  beta_program_compose_artifacts_only: boolean;
  beta_authority: boolean;
  automatic_user_admission_enabled: boolean;
  automatic_customer_provisioning_enabled: boolean;
  automatic_plan_assignment_enabled: boolean;
  automatic_beta_expansion_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  limited_beta_launch_program?: Record<string, unknown>;
  markdown?: string;
};

export type LimitedBetaLaunchProgramRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  limited_beta_launch_program_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlLimitedBetaLaunchProgram = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<LimitedBetaLaunchProgramResponse>(
    `/api/v1/mission-control/limited-beta-launch-program?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlLimitedBetaLaunchProgramRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
  cohortId?: string,
  candidateId?: string,
) =>
  mcFetch<LimitedBetaLaunchProgramRecordResponse>(`/api/v1/mission-control/limited-beta-launch-program`, {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      kind,
      content,
      domain,
      cohort_id: cohortId,
      candidate_id: candidateId,
    }),
  });

export type BetaProgramFocus =
  | "beta_operations_dashboard"
  | "beta_cohort_registry"
  | "beta_feedback_registry"
  | "beta_success_metrics";

export const BETA_PROGRAM_FOCUS_BY_VIEW: Record<string, BetaProgramFocus> = {
  "beta-launch-program": "beta_operations_dashboard",
  "beta-cohorts": "beta_cohort_registry",
  "beta-feedback": "beta_feedback_registry",
  "beta-success-metrics": "beta_success_metrics",
  "beta-operations-dashboard": "beta_operations_dashboard",
};
