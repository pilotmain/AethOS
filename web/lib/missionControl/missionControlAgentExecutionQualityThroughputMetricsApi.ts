/** FIX 190 — agent execution quality and throughput metrics (metrics ≠ authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type AgentExecutionQualityThroughputMetricsResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  metrics_compose_receipts_only: boolean;
  agent_metrics_grant_authority: boolean;
  agent_execution_authority: boolean;
  merge_authority: boolean;
  deploy_authority: boolean;
  railway_authority: boolean;
  provider_authority: boolean;
  gate_bypass_enabled: boolean;
  autonomous_approval_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  agent_execution_quality_throughput_metrics?: Record<string, unknown>;
  markdown?: string;
};

export type AgentExecutionQualityThroughputMetricsRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  agent_execution_quality_throughput_metrics_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlAgentExecutionQualityThroughputMetrics = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<AgentExecutionQualityThroughputMetricsResponse>(
    `/api/v1/mission-control/agent-execution-quality-throughput-metrics?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlAgentExecutionQualityThroughputMetricsRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<AgentExecutionQualityThroughputMetricsRecordResponse>(
    `/api/v1/mission-control/agent-execution-quality-throughput-metrics/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
