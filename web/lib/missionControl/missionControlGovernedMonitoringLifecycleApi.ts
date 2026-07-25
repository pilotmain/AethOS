/** FIX 220 — governed monitoring lifecycle (monitoring_authority ≠ operational_authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernedMonitoringLifecycleResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  observation_performed: boolean;
  monitoring_compose_evidence_only: boolean;
  monitoring_authority: boolean;
  incident_response_authority: boolean;
  autonomous_remediation_enabled: boolean;
  rollback_authority: boolean;
  provider_mutation_authority: boolean;
  workflow_execution_authority: boolean;
  deploy_authority: boolean;
  merge_authority: boolean;
  railway_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  governed_monitoring_lifecycle?: Record<string, unknown>;
  markdown?: string;
};

export type GovernedMonitoringLifecycleRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  governed_monitoring_lifecycle_memory_only: boolean;
  detail?: string;
};

export type GovernedMonitoringLifecycleEscalateResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  incident_escalation?: Record<string, unknown>;
  monitoring_authority: boolean;
  incident_response_authority: boolean;
  autonomous_remediation_enabled: boolean;
  executable: boolean;
  detail?: string;
};

export const fetchMissionControlGovernedMonitoringLifecycle = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernedMonitoringLifecycleResponse>(
    `/api/v1/mission-control/governed-monitoring-lifecycle?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernedMonitoringLifecycleRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
  metadata: Record<string, unknown> = {},
) =>
  mcFetch<GovernedMonitoringLifecycleRecordResponse>(
    `/api/v1/mission-control/governed-monitoring-lifecycle/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author, metadata }),
    },
  );

export const prepareMissionControlGovernedMonitoringEscalation = (sessionId = "default") =>
  mcFetch<GovernedMonitoringLifecycleEscalateResponse>(
    `/api/v1/mission-control/governed-monitoring-lifecycle/escalate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    },
  );
