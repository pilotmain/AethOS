/** FIX 195 — Nexora pilot arc orchestrator (orchestration ≠ trust granting). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type NexoraPilotArcOrchestratorResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  pilot_execution_performed: boolean;
  trust_granting_authority: boolean;
  trust_inheritance_enabled: boolean;
  cross_repo_authority: boolean;
  pilot_arc_routes_through_fix_181: boolean;
  gate_bypass_enabled: boolean;
  merge_authority: boolean;
  deploy_authority: boolean;
  rollback_authority: boolean;
  provider_authority: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  nexora_pilot_arc_orchestrator?: Record<string, unknown>;
  markdown?: string;
};

export type NexoraPilotArcOrchestratorRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  nexora_pilot_arc_orchestrator_memory_only: boolean;
  detail?: string;
};

export type NexoraPilotArcOrchestratorRunResponse = {
  ok: boolean;
  pilot_number: number;
  session_id: string;
  audit_id?: string;
  stages_completed?: string[];
  blockers?: string[];
  trust_granting_authority: boolean;
  trust_inheritance_enabled: boolean;
  cross_repo_authority: boolean;
  pilot_arc_routes_through_fix_181: boolean;
  detail?: string;
};

export const fetchMissionControlNexoraPilotArcOrchestrator = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<NexoraPilotArcOrchestratorResponse>(
    `/api/v1/mission-control/nexora-pilot-arc-orchestrator?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlNexoraPilotArcOrchestratorRecord = (
  sessionId: string,
  kind: string,
  content: string,
  repoIssue = "",
  author = "operator",
) =>
  mcFetch<NexoraPilotArcOrchestratorRecordResponse>(
    `/api/v1/mission-control/nexora-pilot-arc-orchestrator/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, repo_issue: repoIssue, author }),
    },
  );

export const runMissionControlNexoraPilotArcOrchestrator = (
  pilotNumber: 1 | 2 | 3,
  sessionId = "default",
) =>
  mcFetch<NexoraPilotArcOrchestratorRunResponse>(
    `/api/v1/mission-control/nexora-pilot-arc-orchestrator/run`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pilot_number: pilotNumber, session_id: sessionId }),
    },
  );
