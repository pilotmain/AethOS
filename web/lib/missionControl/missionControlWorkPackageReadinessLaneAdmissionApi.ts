/** FIX 169 — work package readiness + lane admission (admission cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type WorkPackageReadinessLaneAdmissionResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_approval_enabled: boolean;
  autonomous_lane_entry_enabled: boolean;
  code_write_enabled: boolean;
  pr_action_enabled: boolean;
  merge_deploy_enabled: boolean;
  railway_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  work_package_readiness_lane_admission?: Record<string, unknown>;
  markdown?: string;
};

export type WorkPackageReadinessLaneAdmissionRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  work_package_readiness_lane_admission_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlWorkPackageReadinessLaneAdmission = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<WorkPackageReadinessLaneAdmissionResponse>(
    `/api/v1/mission-control/work-package-readiness-lane-admission?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlWorkPackageReadinessLaneAdmissionRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<WorkPackageReadinessLaneAdmissionRecordResponse>(
    `/api/v1/mission-control/work-package-readiness-lane-admission/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
