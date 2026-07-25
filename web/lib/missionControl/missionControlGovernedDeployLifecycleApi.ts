/** FIX 210 — governed deploy lifecycle (deploy_authority ≠ autonomous_deploy). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernedDeployLifecycleResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  workflow_execution_performed: boolean;
  deploy_lifecycle_compose_evidence_only: boolean;
  deploy_authority: boolean;
  autonomous_deploy_enabled: boolean;
  approval_bypass_enabled: boolean;
  hidden_workflow_execution_enabled: boolean;
  merge_authority: boolean;
  railway_authority: boolean;
  vercel_authority: boolean;
  aws_authority: boolean;
  kubernetes_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  governed_deploy_lifecycle?: Record<string, unknown>;
  markdown?: string;
};

export type GovernedDeployLifecycleRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  governed_deploy_lifecycle_memory_only: boolean;
  detail?: string;
};

export type GovernedDeployLifecycleHandoffResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  deploy_handoff?: Record<string, unknown>;
  deploy_authority: boolean;
  autonomous_deploy_enabled: boolean;
  workflow_execution_performed: boolean;
  executable: boolean;
  detail?: string;
};

export const fetchMissionControlGovernedDeployLifecycle = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernedDeployLifecycleResponse>(
    `/api/v1/mission-control/governed-deploy-lifecycle?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernedDeployLifecycleRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
  metadata: Record<string, unknown> = {},
) =>
  mcFetch<GovernedDeployLifecycleRecordResponse>(
    `/api/v1/mission-control/governed-deploy-lifecycle/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author, metadata }),
    },
  );

export const prepareMissionControlGovernedDeployHandoff = (sessionId = "default") =>
  mcFetch<GovernedDeployLifecycleHandoffResponse>(
    `/api/v1/mission-control/governed-deploy-lifecycle/handoff`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    },
  );
