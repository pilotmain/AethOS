/** FIX 200 — governed merge lifecycle (merge_authority ≠ autonomous_merge). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernedMergeLifecycleResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  merge_execution_performed: boolean;
  merge_lifecycle_compose_evidence_only: boolean;
  merge_authority: boolean;
  autonomous_merge_enabled: boolean;
  approval_bypass_enabled: boolean;
  hidden_merge_path_enabled: boolean;
  deploy_authority: boolean;
  railway_authority: boolean;
  provider_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  governed_merge_lifecycle?: Record<string, unknown>;
  markdown?: string;
};

export type GovernedMergeLifecycleRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  governed_merge_lifecycle_memory_only: boolean;
  detail?: string;
};

export type GovernedMergeLifecycleHandoffResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  merge_handoff?: Record<string, unknown>;
  merge_authority: boolean;
  autonomous_merge_enabled: boolean;
  merge_execution_performed: boolean;
  executable: boolean;
  detail?: string;
};

export const fetchMissionControlGovernedMergeLifecycle = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernedMergeLifecycleResponse>(
    `/api/v1/mission-control/governed-merge-lifecycle?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernedMergeLifecycleRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernedMergeLifecycleRecordResponse>(
    `/api/v1/mission-control/governed-merge-lifecycle/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );

export const prepareMissionControlGovernedMergeHandoff = (sessionId = "default") =>
  mcFetch<GovernedMergeLifecycleHandoffResponse>(
    `/api/v1/mission-control/governed-merge-lifecycle/handoff`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    },
  );
