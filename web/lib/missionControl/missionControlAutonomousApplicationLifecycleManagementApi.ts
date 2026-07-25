/** FIX 280 — autonomous application lifecycle management (lifecycle ≠ execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type AutonomousApplicationLifecycleManagementResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  lifecycle_compose_artifacts_only: boolean;
  lifecycle_management_authority: boolean;
  automatic_lifecycle_execution_enabled: boolean;
  repository_mutation_authority: boolean;
  deployment_authority: boolean;
  rollback_authority: boolean;
  trust_mutation_authority: boolean;
  merge_authority: boolean;
  provider_mutation_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  autonomous_application_lifecycle_management?: Record<string, unknown>;
  markdown?: string;
};

export type AutonomousApplicationLifecycleManagementRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  autonomous_application_lifecycle_management_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlAutonomousApplicationLifecycleManagement = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<AutonomousApplicationLifecycleManagementResponse>(
    `/api/v1/mission-control/autonomous-application-lifecycle-management?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlAutonomousApplicationLifecycleManagementRecord = (
  sessionId: string,
  kind: string,
  content: string,
  options?: {
    lifecycleStage?: string;
    opportunityId?: string;
  },
) =>
  mcFetch<AutonomousApplicationLifecycleManagementRecordResponse>(
    `/api/v1/mission-control/autonomous-application-lifecycle-management/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        lifecycle_stage: options?.lifecycleStage,
        opportunity_id: options?.opportunityId,
      }),
    },
  );
