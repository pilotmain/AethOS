/** FIX 230 — governed rollback lifecycle (rollback_authority ≠ autonomous_rollback). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernedRollbackLifecycleResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  rollback_compose_evidence_only: boolean;
  rollback_authority: boolean;
  autonomous_rollback_enabled: boolean;
  workflow_execution_performed: boolean;
  provider_mutation_authority: boolean;
  database_mutation_authority: boolean;
  hidden_recovery_path_enabled: boolean;
  monitoring_authority: boolean;
  deploy_authority: boolean;
  merge_authority: boolean;
  railway_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  governed_rollback_lifecycle?: Record<string, unknown>;
  markdown?: string;
};

export type GovernedRollbackLifecycleRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  governed_rollback_lifecycle_memory_only: boolean;
  detail?: string;
};

export type GovernedRollbackLifecycleHandoffResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  rollback_handoff?: Record<string, unknown>;
  rollback_authority: boolean;
  autonomous_rollback_enabled: boolean;
  workflow_execution_performed: boolean;
  executable: boolean;
  detail?: string;
};

export const fetchMissionControlGovernedRollbackLifecycle = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernedRollbackLifecycleResponse>(
    `/api/v1/mission-control/governed-rollback-lifecycle?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernedRollbackLifecycleRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
  metadata: Record<string, unknown> = {},
) =>
  mcFetch<GovernedRollbackLifecycleRecordResponse>(
    `/api/v1/mission-control/governed-rollback-lifecycle/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author, metadata }),
    },
  );

export const prepareMissionControlGovernedRollbackHandoff = (sessionId = "default") =>
  mcFetch<GovernedRollbackLifecycleHandoffResponse>(
    `/api/v1/mission-control/governed-rollback-lifecycle/handoff`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    },
  );
